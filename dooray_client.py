import requests
import base64
import uuid
import math
import tempfile
import os
from config import DOORAY_BASE_URL

CHUNK_CACHE = {}
CHUNK_SIZE = 1024 * 512  # 512KB per chunk

def _call_dooray_api(access_token: str, method, endpoint, json_data=None, params=None, files=None):
    headers = {
        "Authorization": f"dooray-api {access_token}"
    }
    if files is None:
        headers["Content-Type"] = "application/json"

    url = f"{DOORAY_BASE_URL}{endpoint}"

    try:
        # First request, do not follow redirects automatically
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, allow_redirects=False)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json_data, params=params, files=files, allow_redirects=False)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=json_data, params=params, files=files, allow_redirects=False)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, params=params, allow_redirects=False)
        else:
            return {"error": "Unsupported HTTP method"}

        # Handle 307 Temporary Redirect for file APIs
        if response.status_code == 307:
            redirect_url = response.headers.get("Location")
            if not redirect_url:
                return {"error": "API returned 307 but no Location header"}

            # Make the second request to the redirect URL
            if method == "GET":
                response = requests.get(redirect_url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(redirect_url, headers=headers, json=json_data, params=params, files=files)
            elif method == "PUT":
                response = requests.put(redirect_url, headers=headers, json=json_data, params=params, files=files)
            elif method == "DELETE":
                response = requests.delete(redirect_url, headers=headers, params=params)

        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        # For file downloads, return raw content
        if params and params.get("media") == "raw":
            return response.content

        # For other successful responses, return JSON
        return response.json()

    except requests.exceptions.HTTPError as e:
        return {
            "error": "API request failed",
            "status_code": e.response.status_code,
            "response": e.response.text
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Network or request error: {e}"}

# --- Common API ---
def get_members(access_token: str):
    # Dooray API requires query parameters for members endpoint
    params = {"page": 0, "size": 50}
    return _call_dooray_api(access_token, "GET", "/common/v1/members", params=params)

def get_member(access_token: str, member_id: str):
    return _call_dooray_api(access_token, "GET", f"/common/v1/members/{member_id}")

def create_incoming_hook(access_token: str, name: str, url: str, description: str = None):
    json_data = {
        "name": name,
        "url": url
    }
    if description: json_data["description"] = description
    return _call_dooray_api(access_token, "POST", "/common/v1/incoming-hooks", json_data)

def get_incoming_hook(access_token: str, incoming_hook_id: str):
    return _call_dooray_api(access_token, "GET", f"/common/v1/incoming-hooks/{incoming_hook_id}")

def delete_incoming_hook(access_token: str, incoming_hook_id: str):
    return _call_dooray_api(access_token, "DELETE", f"/common/v1/incoming-hooks/{incoming_hook_id}")


# --- Drive API ---
def get_drive_list(access_token: str, drive_type: str = "private", project_id: str = None, 
                  scope: str = "private", state: str = "active"):
    """드라이브 목록 조회 (공식 두레이 API 형식)"""
    params = {"type": drive_type}
    
    if project_id:
        params["projectId"] = project_id
        
    if drive_type == "project":
        params["scope"] = scope  # private, public
        
    if state != "active":  # default는 active
        params["state"] = state  # active, archived
        
    return _call_dooray_api(access_token, "GET", "/drive/v1/drives", params=params)

def get_drive(access_token: str, drive_id: str):
    return _call_dooray_api(access_token, "GET", f"/drive/v1/drives/{drive_id}")

def get_drive_files(access_token: str, drive_id: str):
    return _call_dooray_api(access_token, "GET", f"/drive/v1/drives/{drive_id}/files")

def get_drive_file_metadata(access_token: str, drive_id: str, file_id: str):
    return _call_dooray_api(access_token, "GET", f"/drive/v1/drives/{drive_id}/files/{file_id}", params={"media": "meta"})

def download_drive_file(access_token: str, drive_id: str, file_id: str):
    """
    Dooray 파일 다운로드 - 307 리다이렉트를 통해 file-api.dooray.com으로 처리
    """
    headers = {
        "Authorization": f"dooray-api {access_token}"
    }
    
    # 1단계: api.dooray.com으로 요청하여 307 리다이렉트 받기
    url = f"{DOORAY_BASE_URL}/drive/v1/drives/{drive_id}/files/{file_id}"
    params = {"media": "raw"}
    
    try:
        # 리다이렉트 없이 요청
        response = requests.get(url, headers=headers, params=params, allow_redirects=False)
        
        if response.status_code == 307:
            # 2단계: Location 헤더의 file-api.dooray.com URL로 재요청
            redirect_url = response.headers.get("Location")
            if not redirect_url:
                return {"error": "API returned 307 but no Location header"}
            
            # file-api.dooray.com으로 실제 파일 다운로드
            file_response = requests.get(redirect_url, headers=headers, stream=True)
            file_response.raise_for_status()
            return file_response.content
            
        elif response.status_code == 200:
            # 직접 응답받은 경우
            return response.content
        else:
            response.raise_for_status()
            
    except requests.exceptions.HTTPError as e:
        return {
            "error": "File download failed",
            "status_code": e.response.status_code,
            "response": e.response.text
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Network or request error: {e}"}

# 청크 세션 저장소 (실제 운영에서는 Redis 등 사용)
chunk_sessions = {}

def create_chunk_session(access_token: str, drive_id: str, file_id: str, session_id: str):
    """청크 다운로드 세션을 생성하고 파일을 스트리밍으로 다운로드"""
    try:
        # 파일 메타데이터 가져오기
        metadata = get_drive_file_metadata(access_token, drive_id, file_id)
        if "error" in metadata:
            return metadata
            
        file_info = metadata.get("result", {})
        file_name = file_info.get("name", "unknown")
        file_size = file_info.get("size", 0)
        
        # 파일 크기에 따른 동적 청크 크기 결정
        def get_optimal_chunk_size(size_bytes):
            if size_bytes <= 5 * 1024 * 1024:  # 5MB 이하
                return 1024 * 1024  # 1MB 청크 (대부분 단일 청크)
            elif size_bytes <= 50 * 1024 * 1024:  # 50MB 이하  
                return 256 * 1024  # 256KB 청크
            else:  # 50MB 초과
                return 64 * 1024   # 64KB 청크
        
        chunk_size = get_optimal_chunk_size(file_size)
        
        # Dooray API로 파일 스트리밍 다운로드
        headers = {"Authorization": f"dooray-api {access_token}"}
        url = f"{DOORAY_BASE_URL}/drive/v1/drives/{drive_id}/files/{file_id}"
        params = {"media": "raw"}
        
        # 첫 번째 요청으로 307 리다이렉트 받기
        response = requests.get(url, headers=headers, params=params, allow_redirects=False)
        
        if response.status_code == 307:
            redirect_url = response.headers.get("Location")
            if not redirect_url:
                return {"error": "API returned 307 but no Location header"}
            
            # 리다이렉트된 URL로 스트리밍 다운로드 (인증 헤더 포함)
            stream_response = requests.get(redirect_url, headers=headers, stream=True)
            stream_response.raise_for_status()
            
            # 파일 데이터를 청크로 나누어 저장 (동적 크기 적용)
            chunks = []
            current_chunk = b""
            
            for data in stream_response.iter_content(chunk_size=8192):
                current_chunk += data
                if len(current_chunk) >= chunk_size:
                    chunks.append(base64.b64encode(current_chunk).decode('utf-8'))
                    current_chunk = b""
            
            # 마지막 청크 처리
            if current_chunk:
                chunks.append(base64.b64encode(current_chunk).decode('utf-8'))
            
            # 세션에 저장
            chunk_sessions[session_id] = {
                "file_name": file_name,
                "file_size": file_size,
                "chunks": chunks,
                "total_chunks": len(chunks),
                "drive_id": drive_id,
                "file_id": file_id
            }
            
            return {
                "result": {
                    "chunkSessionId": session_id,
                    "fileName": file_name,
                    "fileSize": file_size,
                    "totalChunks": len(chunks),
                    "chunkSize": chunk_size
                }
            }
        else:
            return {"error": f"Unexpected response status: {response.status_code}"}
            
    except Exception as e:
        return {"error": f"Failed to create chunk session: {str(e)}"}

def get_file_chunk_data(session_id: str, chunk_index: int):
    """세션 ID와 청크 인덱스로 파일 청크 데이터 반환 (ResponseTooLargeError 방지)"""
    if session_id not in chunk_sessions:
        return {"error": f"Invalid or expired chunk session: {session_id}"}
    
    session = chunk_sessions[session_id]
    chunks = session["chunks"]
    
    if chunk_index < 0 or chunk_index >= len(chunks):
        return {"error": f"Invalid chunk index: {chunk_index}. Valid range: 0-{len(chunks)-1}"}
    
    # 기존 청크가 너무 큰 경우 더 작은 단위로 재분할
    original_chunk = chunks[chunk_index]
    
    # Base64 디코딩 후 크기 확인
    try:
        decoded_data = base64.b64decode(original_chunk)
        
        # 2KB 이하인 경우 그대로 반환 (Onrender 무료 서버 제한)
        max_size = 2 * 1024  # 2KB
        if len(decoded_data) <= max_size:
            return {
                "result": {
                    "chunkData": original_chunk,
                    "chunkIndex": chunk_index,
                    "totalChunks": len(chunks),
                    "fileName": session["file_name"],
                    "isLastChunk": chunk_index == len(chunks) - 1,
                    "chunkSize": len(decoded_data)
                }
            }
        
        # 큰 청크인 경우 더 작은 크기로 분할 (Onrender 극한 제약 대응)
        # 2KB도 실패할 경우를 대비해 1KB로 추가 축소
        fallback_size = 1 * 1024  # 1KB
        actual_size = min(max_size, fallback_size) if len(decoded_data) > max_size else max_size
        
        smaller_data = decoded_data[:actual_size]
        smaller_chunk = base64.b64encode(smaller_data).decode('utf-8')
        
        return {
            "result": {
                "chunkData": smaller_chunk,
                "chunkIndex": chunk_index,
                "totalChunks": len(chunks),
                "fileName": session["file_name"],
                "isLastChunk": chunk_index == len(chunks) - 1,
                "chunkSize": len(smaller_data),
                "originalSize": len(decoded_data),
                "note": f"Chunk reduced from {len(decoded_data)} to {len(smaller_data)} bytes for GPTs compatibility"
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to process chunk: {str(e)}"}

def download_file_base64(access_token: str, drive_id: str, file_id: str, media: str = "raw"):
    """Downloads a file using temporary file storage and returns the first chunk."""
    # 1. Get metadata
    metadata = get_drive_file_metadata(access_token, drive_id, file_id)
    if "error" in metadata:
        return metadata

    fileName = metadata.get("result", {}).get("name")
    if not fileName:
        return {"error": "Filename could not be found in the metadata response.", "raw_metadata": metadata}

    if media == "meta":
        return metadata

    # 2. Stream download to temporary file
    session_id = str(uuid.uuid4())
    temp_file_path = None
    
    try:
        # Get streaming response
        headers = {"Authorization": f"dooray-api {access_token}"}
        url = f"{DOORAY_BASE_URL}/drive/v1/drives/{drive_id}/files/{file_id}"
        params = {"media": "raw"}
        
        # First request for 307 redirect
        response = requests.get(url, headers=headers, params=params, allow_redirects=False)
        
        if response.status_code == 307:
            redirect_url = response.headers.get("Location")
            if not redirect_url:
                return {"error": "API returned 307 but no Location header"}
            
            # Stream download from file-api.dooray.com
            file_response = requests.get(redirect_url, headers=headers, stream=True)
            file_response.raise_for_status()
            
        elif response.status_code == 200:
            file_response = response
        else:
            response.raise_for_status()

        # Create temporary file for streaming download
        temp_fd, temp_file_path = tempfile.mkstemp(suffix='.tmp', prefix='dooray_download_')
        
        # Download file to temporary location
        with os.fdopen(temp_fd, 'wb') as temp_file:
            for chunk in file_response.iter_content(chunk_size=64*1024):  # 64KB chunks
                if chunk:
                    temp_file.write(chunk)
        
        # Store temp file path in cache instead of file content
        CHUNK_CACHE[session_id] = {
            'temp_file_path': temp_file_path,
            'file_name': fileName
        }
        
        # Read first chunk for immediate return
        with open(temp_file_path, 'rb') as f:
            first_raw_chunk = f.read(CHUNK_SIZE * 3 // 4)  # Read less raw data to account for base64 expansion
            first_chunk_data = base64.b64encode(first_raw_chunk).decode('utf-8')
        
        # Calculate total chunks based on file size
        file_size = os.path.getsize(temp_file_path)
        raw_chunk_size = CHUNK_SIZE * 3 // 4  # Account for base64 expansion
        total_chunks = math.ceil(file_size / raw_chunk_size)
        
        return {
            "fileName": fileName,
            "totalChunks": total_chunks,
            "chunkSessionId": session_id,
            "chunkData": first_chunk_data
        }
        
    except requests.exceptions.HTTPError as e:
        # Clean up temp file on error
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        return {
            "error": "File download failed",
            "status_code": e.response.status_code,
            "response": e.response.text
        }
    except Exception as e:
        # Clean up temp file on error
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        return {"error": f"Download error: {e}"}

def get_file_chunk(session_id: str, chunk_index: int):
    """Retrieves a specific chunk of a cached file from temporary storage."""
    if session_id not in CHUNK_CACHE:
        return {"error": "Invalid or expired chunkSessionId"}

    cache_entry = CHUNK_CACHE[session_id]
    
    # Handle old string-based cache entries for backward compatibility
    if isinstance(cache_entry, str):
        full_data = cache_entry
        total_chunks = math.ceil(len(full_data) / CHUNK_SIZE)

        if chunk_index < 0 or chunk_index >= total_chunks:
            return {"error": f"Invalid chunk_index. Must be between 0 and {total_chunks - 1}."}

        start = chunk_index * CHUNK_SIZE
        end = start + CHUNK_SIZE
        chunk_data = full_data[start:end]
        return {
            "chunkSessionId": session_id,
            "chunkIndex": chunk_index,
            "chunkData": chunk_data
        }
    
    # Handle new temp file-based cache entries
    temp_file_path = cache_entry.get('temp_file_path')
    if not temp_file_path or not os.path.exists(temp_file_path):
        return {"error": "Temporary file not found or expired"}
    
    try:
        # Calculate chunk boundaries
        file_size = os.path.getsize(temp_file_path)
        raw_chunk_size = CHUNK_SIZE * 3 // 4  # Account for base64 expansion
        total_chunks = math.ceil(file_size / raw_chunk_size)
        
        if chunk_index < 0 or chunk_index >= total_chunks:
            return {"error": f"Invalid chunk_index. Must be between 0 and {total_chunks - 1}."}
        
        # Read specific chunk from file
        start_pos = chunk_index * raw_chunk_size
        
        with open(temp_file_path, 'rb') as f:
            f.seek(start_pos)
            raw_chunk = f.read(raw_chunk_size)
            
        # Convert to base64
        chunk_data = base64.b64encode(raw_chunk).decode('utf-8')
        
        return {
            "chunkSessionId": session_id,
            "chunkIndex": chunk_index,
            "chunkData": chunk_data
        }
        
    except Exception as e:
        return {"error": f"Error reading chunk: {e}"}

def cleanup_temp_file(session_id: str):
    """Clean up temporary file associated with session"""
    if session_id in CHUNK_CACHE:
        cache_entry = CHUNK_CACHE[session_id]
        if isinstance(cache_entry, dict) and 'temp_file_path' in cache_entry:
            temp_file_path = cache_entry['temp_file_path']
            if os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass  # Ignore cleanup errors
        del CHUNK_CACHE[session_id]

def upload_drive_file(access_token: str, drive_id: str, folder_id: str, file_name: str, file_content: bytes):
    """드라이브에 파일 업로드 (307 리다이렉트 처리 포함)"""
    headers = {
        "Authorization": f"dooray-api {access_token}"
    }
    
    # 1단계: api.dooray.com으로 요청하여 307 리다이렉트 받기
    url = f"{DOORAY_BASE_URL}/drive/v1/drives/{drive_id}/files"
    params = {"parentId": folder_id} if folder_id else None
    files = {"file": (file_name, file_content)}
    
    try:
        # 리다이렉트 없이 요청
        response = requests.post(url, headers=headers, params=params, files=files, allow_redirects=False)
        
        if response.status_code == 307:
            # 2단계: Location 헤더의 file-api.dooray.com URL로 재요청
            redirect_url = response.headers.get("Location")
            if not redirect_url:
                return {"error": "API returned 307 but no Location header"}
            
            # file-api.dooray.com으로 실제 파일 업로드 (인증 헤더 포함)
            file_response = requests.post(redirect_url, headers=headers, params=params, files=files)
            file_response.raise_for_status()
            return file_response.json()
            
        elif response.status_code == 200:
            # 직접 응답받은 경우
            return response.json()
        else:
            response.raise_for_status()
            
    except requests.exceptions.HTTPError as e:
        return {
            "error": "File upload failed",
            "status_code": e.response.status_code,
            "response": e.response.text
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Network or request error: {e}"}

def create_drive_folder(access_token: str, drive_id: str, parent_folder_id: str, folder_name: str):
    """드라이브에 폴더 생성 (정확한 API 명세 반영)"""
    json_data = {
        "name": folder_name
    }
    return _call_dooray_api(access_token, "POST", f"/drive/v1/drives/{drive_id}/files/{parent_folder_id}/create-folder", json_data)

def delete_drive_file(access_token: str, drive_id: str, file_id: str):
    """드라이브 파일 삭제"""
    return _call_dooray_api(access_token, "DELETE", f"/drive/v1/drives/{drive_id}/files/{file_id}")

def move_drive_file(access_token: str, drive_id: str, file_id: str, target_folder_id: str):
    """드라이브 파일 이동 (정확한 API 명세 반영)"""
    json_data = {
        "destinationFileId": target_folder_id
    }
    return _call_dooray_api(access_token, "POST", f"/drive/v1/drives/{drive_id}/files/{file_id}/move", json_data)

def copy_drive_file(access_token: str, drive_id: str, file_id: str, target_drive_id: str, target_folder_id: str):
    """드라이브 파일 복사 (정확한 API 명세 반영)"""
    json_data = {
        "destinationDriveId": target_drive_id,
        "destinationFileId": target_folder_id
    }
    return _call_dooray_api(access_token, "POST", f"/drive/v1/drives/{drive_id}/files/{file_id}/copy", json_data)

def get_drive_folder_contents(access_token: str, drive_id: str, folder_id: str):
    """특정 폴더의 내용 조회"""
    return _call_dooray_api(access_token, "GET", f"/drive/v1/drives/{drive_id}/folders/{folder_id}/contents")

def search_drive_files(access_token: str, drive_id: str, query: str):
    """드라이브에서 파일 검색"""
    params = {"q": query}
    return _call_dooray_api(access_token, "GET", f"/drive/v1/drives/{drive_id}/search", params=params)

def get_drive_changes(access_token: str, drive_id: str, page_token: str = None, include_removed: bool = False):
    """드라이브 변경사항 조회"""
    params = {}
    if page_token:
        params["pageToken"] = page_token
    if include_removed:
        params["includeRemoved"] = include_removed
    return _call_dooray_api(access_token, "GET", f"/drive/v1/drives/{drive_id}/changes", params=params)

# --- Drive Shared Links API ---
def create_drive_shared_link(access_token: str, drive_id: str, file_id: str, scope: str, expired_at: str):
    """드라이브 파일 공유링크 생성"""
    json_data = {
        "scope": scope,  # member, memberAndGuest, memberAndGuestAndExternal
        "expiredAt": expired_at
    }
    return _call_dooray_api(access_token, "POST", f"/drive/v1/drives/{drive_id}/files/{file_id}/shared-links", json_data)

def get_drive_shared_links(access_token: str, drive_id: str, file_id: str, valid: bool = True):
    """드라이브 파일의 공유링크 목록 조회"""
    params = {"valid": valid}
    return _call_dooray_api(access_token, "GET", f"/drive/v1/drives/{drive_id}/files/{file_id}/shared-links", params=params)

def get_drive_shared_link(access_token: str, drive_id: str, file_id: str, link_id: str):
    """특정 공유링크 조회"""
    return _call_dooray_api(access_token, "GET", f"/drive/v1/drives/{drive_id}/files/{file_id}/shared-links/{link_id}")

def update_drive_shared_link(access_token: str, drive_id: str, file_id: str, link_id: str, scope: str = None, expired_at: str = None):
    """공유링크 수정"""
    json_data = {}
    if scope:
        json_data["scope"] = scope
    if expired_at:
        json_data["expiredAt"] = expired_at
    return _call_dooray_api(access_token, "PUT", f"/drive/v1/drives/{drive_id}/files/{file_id}/shared-links/{link_id}", json_data)

def delete_drive_shared_link(access_token: str, drive_id: str, file_id: str, link_id: str):
    """공유링크 삭제"""
    return _call_dooray_api(access_token, "DELETE", f"/drive/v1/drives/{drive_id}/files/{file_id}/shared-links/{link_id}")

# --- Messenger API (1:1 message) ---
def send_message(access_token: str, recipient_id: str, message: str):
    endpoint = "/messenger/v1/channels/direct-send"
    json_data = {
        "organizationMemberId": recipient_id,
        "text": message
    }
    return _call_dooray_api(access_token, "POST", endpoint, json_data)

# --- Project API ---
def get_projects(access_token: str, limit: int = 50, cursor: str = None):
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    return _call_dooray_api(access_token, "GET", "/project/v1/projects", params=params)

def create_project(access_token: str, name: str, code: str, description: str = None):
    json_data = {
        "name": name,
        "code": code
    }
    if description: json_data["description"] = description
    return _call_dooray_api(access_token, "POST", "/project/v1/projects", json_data)

def get_project(access_token: str, project_id: str):
    return _call_dooray_api(access_token, "GET", f"/project/v1/projects/{project_id}")

def is_project_creatable(access_token: str):
    return _call_dooray_api(access_token, "POST", "/project/v1/projects/is-creatable")

def get_project_members(access_token: str, project_id: str):
    return _call_dooray_api(access_token, "GET", f"/project/v1/projects/{project_id}/members")

def get_project_member(access_token: str, project_id: str, member_id: str):
    return _call_dooray_api(access_token, "GET", f"/project/v1/projects/{project_id}/members/{member_id}")

def get_project_workflows(access_token: str, project_id: str):
    return _call_dooray_api(access_token, "GET", f"/project/v1/projects/{project_id}/workflows")

def create_project_workflow(access_token: str, project_id: str, name: str, description: str = None):
    json_data = {
        "name": name
    }
    if description: json_data["description"] = description
    return _call_dooray_api(access_token, "POST", f"/project/v1/projects/{project_id}/workflows", json_data)

def update_project_workflow(access_token: str, project_id: str, workflow_id: str, name: str = None, description: str = None):
    json_data = {}
    if name: json_data["name"] = name
    if description: json_data["description"] = description
    return _call_dooray_api(access_token, "PUT", f"/project/v1/projects/{project_id}/workflows/{workflow_id}", json_data)

def delete_project_workflow(access_token: str, project_id: str, workflow_id: str):
    return _call_dooray_api(access_token, "POST", f"/project/v1/projects/{project_id}/workflows/{workflow_id}/delete")

def get_project_posts(access_token: str, project_id: str):
    return _call_dooray_api(access_token, "GET", f"/project/v1/projects/{project_id}/posts")

def get_project_post(access_token: str, project_id: str, post_id: str):
    return _call_dooray_api(access_token, "GET", f"/project/v1/projects/{project_id}/posts/{post_id}")

def create_project_post(access_token: str, project_id: str, subject: str, body: str, post_type: str = "task"):
    json_data = {
        "subject": subject,
        "body": {"mimeType": "text/x-markdown", "content": body},
        "postType": post_type
    }
    return _call_dooray_api(access_token, "POST", f"/project/v1/projects/{project_id}/posts", json_data)

def update_project_post(access_token: str, project_id: str, post_id: str, subject: str = None, body: str = None):
    json_data = {}
    if subject: json_data["subject"] = subject
    if body: json_data["body"] = {"mimeType": "text/x-markdown", "content": body}
    return _call_dooray_api(access_token, "PUT", f"/project/v1/projects/{project_id}/posts/{post_id}", json_data)

def update_project_post_workflow(access_token: str, project_id: str, post_id: str, workflow_id: str):
    json_data = {"workflowId": workflow_id}
    return _call_dooray_api(access_token, "PUT", f"/project/v1/projects/{project_id}/posts/{post_id}/workflow", json_data)

def set_project_post_done(access_token: str, project_id: str, post_id: str):
    return _call_dooray_api(access_token, "PUT", f"/project/v1/projects/{project_id}/posts/{post_id}/done")

def create_project_post_comment(access_token: str, project_id: str, post_id: str, content: str):
    json_data = {"content": {"mimeType": "text/x-markdown", "content": content}}
    return _call_dooray_api(access_token, "POST", f"/project/v1/projects/{project_id}/posts/{post_id}/comments", json_data)

def get_project_post_comments(access_token: str, project_id: str, post_id: str):
    return _call_dooray_api(access_token, "GET", f"/project/v1/projects/{project_id}/posts/{post_id}/comments")

def get_project_tags(access_token: str, project_id: str):
    return _call_dooray_api(access_token, "GET", f"/project/v1/projects/{project_id}/tags")

def get_project_milestones(access_token: str, project_id: str):
    """프로젝트 마일스톤 목록 조회"""
    return _call_dooray_api(access_token, "GET", f"/project/v1/projects/{project_id}/milestones")

def create_project_milestone(access_token: str, project_id: str, name: str, description: str = None, due_date: str = None):
    """프로젝트 마일스톤 생성"""
    json_data = {"name": name}
    if description:
        json_data["description"] = description
    if due_date:
        json_data["dueDate"] = due_date
    return _call_dooray_api(access_token, "POST", f"/project/v1/projects/{project_id}/milestones", json_data)


def update_project_post_comment(access_token: str, project_id: str, post_id: str, comment_id: str, content: str):
    json_data = {"content": {"mimeType": "text/x-markdown", "content": content}}
    return _call_dooray_api(access_token, "PUT", f"/project/v1/projects/{project_id}/posts/{post_id}/comments/{comment_id}", json_data)

def delete_project_post_comment(access_token: str, project_id: str, post_id: str, comment_id: str):
    return _call_dooray_api(access_token, "DELETE", f"/project/v1/projects/{project_id}/posts/{post_id}/comments/{comment_id}")

# --- Project Post File Management ---
def upload_project_post_file(access_token: str, project_id: str, post_id: str, file_name: str, file_content: bytes):
    """프로젝트 업무에 파일 첨부"""
    files = {"file": (file_name, file_content)}
    return _call_dooray_api(access_token, "POST", f"/project/v1/projects/{project_id}/posts/{post_id}/files", files=files)

def download_project_post_file(access_token: str, project_id: str, post_id: str, file_id: str):
    """프로젝트 업무 파일 다운로드"""
    return _call_dooray_api(access_token, "GET", f"/project/v1/projects/{project_id}/posts/{post_id}/files/{file_id}")

def delete_project_post_file(access_token: str, project_id: str, post_id: str, file_id: str):
    """프로젝트 업무 파일 삭제"""
    return _call_dooray_api(access_token, "DELETE", f"/project/v1/projects/{project_id}/posts/{post_id}/files/{file_id}")

def set_project_post_parent(access_token: str, project_id: str, post_id: str, parent_post_id: str):
    """업무의 상위 업무 설정"""
    json_data = {"parentPostId": parent_post_id}
    return _call_dooray_api(access_token, "POST", f"/project/v1/projects/{project_id}/posts/{post_id}/set-parent", json_data)

def move_project_post(access_token: str, project_id: str, post_id: str, target_project_id: str):
    """업무를 다른 프로젝트로 이동"""
    json_data = {"projectId": target_project_id}
    return _call_dooray_api(access_token, "POST", f"/project/v1/projects/{project_id}/posts/{post_id}/move", json_data)

def delete_project_post(access_token: str, project_id: str, post_id: str):
    """프로젝트 업무 삭제"""
    return _call_dooray_api(access_token, "DELETE", f"/project/v1/projects/{project_id}/posts/{post_id}")

# --- Wiki API ---
def get_wikis(access_token: str):
    return _call_dooray_api(access_token, "GET", "/wiki/v1/wikis")

def get_wiki_pages(access_token: str, wiki_id: str):
    return _call_dooray_api(access_token, "GET", f"/wiki/v1/wikis/{wiki_id}/pages")

def get_wiki_page(access_token: str, wiki_id: str, page_id: str):
    return _call_dooray_api(access_token, "GET", f"/wiki/v1/wikis/{wiki_id}/pages/{page_id}")

def create_wiki_page(access_token: str, wiki_id: str, subject: str, content: str, 
                     parent_page_id: str = None, attach_file_ids: list = None, referrers: list = None):
    """위키 페이지 생성 (공식 두레이 API 형식)"""
    json_data = {
        "subject": subject,  # title이 아니라 subject
        "body": {"mimeType": "text/x-markdown", "content": content}  # content가 아니라 body
    }
    if parent_page_id:
        json_data["parentPageId"] = parent_page_id
    if attach_file_ids:
        json_data["attachFileIds"] = attach_file_ids
    if referrers:
        json_data["referrers"] = referrers
    return _call_dooray_api(access_token, "POST", f"/wiki/v1/wikis/{wiki_id}/pages", json_data)

def update_wiki_page(access_token: str, wiki_id: str, page_id: str, subject: str = None, content: str = None):
    """위키 페이지 수정 (공식 두레이 API 형식)"""
    json_data = {}
    if subject: json_data["subject"] = subject  # title이 아니라 subject
    if content: json_data["body"] = {"mimeType": "text/x-markdown", "content": content}  # content가 아니라 body
    return _call_dooray_api(access_token, "PUT", f"/wiki/v1/wikis/{wiki_id}/pages/{page_id}", json_data)

def update_wiki_page_title(access_token: str, wiki_id: str, page_id: str, title: str):
    json_data = {"title": title}
    return _call_dooray_api(access_token, "PUT", f"/wiki/v1/wikis/{wiki_id}/pages/{page_id}/title", json_data)

def update_wiki_page_content(access_token: str, wiki_id: str, page_id: str, content: str):
    json_data = {"content": {"mimeType": "text/x-markdown", "content": content}}
    return _call_dooray_api(access_token, "PUT", f"/wiki/v1/wikis/{wiki_id}/pages/{page_id}/content", json_data)

def update_wiki_page_referrers(access_token: str, wiki_id: str, page_id: str, referrers: list):
    json_data = {"referrers": referrers}
    return _call_dooray_api(access_token, "PUT", f"/wiki/v1/wikis/{wiki_id}/pages/{page_id}/referrers", json_data)

def create_wiki_page_comment(access_token: str, wiki_id: str, page_id: str, content: str):
    json_data = {"content": {"mimeType": "text/x-markdown", "content": content}}
    return _call_dooray_api(access_token, "POST", f"/wiki/v1/wikis/{wiki_id}/pages/{page_id}/comments", json_data)

def get_wiki_page_comments(access_token: str, wiki_id: str, page_id: str):
    return _call_dooray_api(access_token, "GET", f"/wiki/v1/wikis/{wiki_id}/pages/{page_id}/comments")

def get_wiki_page_comment(access_token: str, wiki_id: str, page_id: str, comment_id: str):
    return _call_dooray_api(access_token, "GET", f"/wiki/v1/wikis/{wiki_id}/pages/{page_id}/comments/{comment_id}")

def update_wiki_page_comment(access_token: str, wiki_id: str, page_id: str, comment_id: str, content: str):
    json_data = {"content": {"mimeType": "text/x-markdown", "content": content}}
    return _call_dooray_api(access_token, "PUT", f"/wiki/v1/wikis/{wiki_id}/pages/{page_id}/comments/{comment_id}", json_data)

def delete_wiki_page_comment(access_token: str, wiki_id: str, page_id: str, comment_id: str):
    return _call_dooray_api(access_token, "DELETE", f"/wiki/v1/wikis/{wiki_id}/pages/{page_id}/comments/{comment_id}")

def upload_wiki_page_file(access_token: str, wiki_id: str, page_id: str, file_name: str, file_content: bytes):
    files = {"file": (file_name, file_content, "application/octet-stream")}
    return _call_dooray_api(access_token, "POST", f"/wiki/v1/wikis/{wiki_id}/pages/{page_id}/files", files=files)

def get_wiki_page_file(access_token: str, wiki_id: str, page_id: str, file_id: str):
    return _call_dooray_api(access_token, "GET", f"/wiki/v1/wikis/{wiki_id}/pages/{page_id}/files/{file_id}")

def delete_wiki_page_file(access_token: str, wiki_id: str, page_id: str, file_id: str):
    return _call_dooray_api(access_token, "DELETE", f"/wiki/v1/wikis/{wiki_id}/pages/{page_id}/files/{file_id}")

def upload_wiki_file(access_token: str, wiki_id: str, file_name: str, file_content: bytes):
    files = {"file": (file_name, file_content, "application/octet-stream")}
    return _call_dooray_api(access_token, "POST", f"/wiki/v1/wikis/{wiki_id}/files", files=files)

# --- Calendar API ---
def get_calendars(access_token: str):
    return _call_dooray_api(access_token, "GET", "/calendar/v1/calendars")

def get_calendar(access_token: str, calendar_id: str):
    return _call_dooray_api(access_token, "GET", f"/calendar/v1/calendars/{calendar_id}")

def create_calendar_event(access_token: str, calendar_id: str, subject: str, started_at: str, ended_at: str, body: str = None, location: str = None, users: list = None):
    json_data = {
        "subject": subject,
        "startedAt": started_at,
        "endedAt": ended_at,
        "wholeDayFlag": False,
        "users": users if users else []
    }
    if body: json_data["body"] = {"mimeType": "text/x-markdown", "content": body}
    if location: json_data["location"] = location
    return _call_dooray_api(access_token, "POST", f"/calendar/v1/calendars/{calendar_id}/events", json_data)

def get_calendar_events(access_token: str, calendar_id: str = "*", time_min: str = None, time_max: str = None):
    params = {}
    if time_min: params["timeMin"] = time_min
    if time_max: params["timeMax"] = time_max
    return _call_dooray_api(access_token, "GET", f"/calendar/v1/calendars/{calendar_id}/events", params=params)

def get_calendar_event(access_token: str, calendar_id: str, event_id: str):
    return _call_dooray_api(access_token, "GET", f"/calendar/v1/calendars/{calendar_id}/events/{event_id}")

def update_calendar_event(access_token: str, calendar_id: str, event_id: str, subject: str = None, started_at: str = None, ended_at: str = None, body: str = None, location: str = None, users: list = None):
    json_data = {}
    if subject: json_data["subject"] = subject
    if started_at: json_data["startedAt"] = started_at
    if ended_at: json_data["endedAt"] = ended_at
    if body: json_data["body"] = {"mimeType": "text/x-markdown", "content": body}
    if location: json_data["location"] = location
    if users: json_data["users"] = users
    return _call_dooray_api(access_token, "PUT", f"/calendar/v1/calendars/{calendar_id}/events/{event_id}", json_data)

def delete_calendar_event(access_token: str, calendar_id: str, event_id: str):
    return _call_dooray_api(access_token, "POST", f"/calendar/v1/calendars/{calendar_id}/events/{event_id}/delete")

def create_calendar(access_token: str, name: str, calendar_type: str = "private", color: str = "ffffff", 
                   description: str = None, calendar_members: list = None, notifications_enabled: bool = True):
    """새로운 캘린더 생성 (공식 두레이 API 형식)"""
    json_data = {
        "name": name,
        "type": calendar_type,  # private, subscription
        "me": {
            "color": color,
            "notification": {
                "enabled": notifications_enabled,
                "alarms": [{
                    "action": "mail",
                    "trigger": "TRIGGER:-PT10M",
                    "wholeDayTrigger": "TRIGGER:-PT10M"
                }]
            }
        }
    }
    
    # 개인 캘린더에 공유 멤버가 있는 경우
    if calendar_type == "private" and calendar_members:
        json_data["calendarMemberList"] = calendar_members
        
    # 구독 캘린더인 경우 (향후 확장용)  
    if calendar_type == "subscription" and description:
        json_data["calendarUrl"] = description  # description을 URL로 사용
    
    return _call_dooray_api(access_token, "POST", "/calendar/v1/calendars", json_data)

def update_calendar(access_token: str, calendar_id: str, name: str = None, description: str = None, color: str = None):
    """캘린더 정보 수정"""
    json_data = {}
    if name:
        json_data["name"] = name
    if description:
        json_data["description"] = description
    if color:
        json_data["color"] = color
    return _call_dooray_api(access_token, "PUT", f"/calendar/v1/calendars/{calendar_id}", json_data)

def delete_calendar(access_token: str, calendar_id: str):
    """캘린더 삭제"""
    return _call_dooray_api(access_token, "DELETE", f"/calendar/v1/calendars/{calendar_id}")

def get_calendar_permissions(access_token: str, calendar_id: str):
    """캘린더 권한 조회"""
    return _call_dooray_api(access_token, "GET", f"/calendar/v1/calendars/{calendar_id}/permissions")

def add_calendar_permission(access_token: str, calendar_id: str, member_id: str, role: str):
    """캘린더 권한 추가 (role: owner, manager, writer, reader)"""
    json_data = {
        "member": {"id": member_id},
        "role": role
    }
    return _call_dooray_api(access_token, "POST", f"/calendar/v1/calendars/{calendar_id}/permissions", json_data)

def remove_calendar_permission(access_token: str, calendar_id: str, permission_id: str):
    """캘린더 권한 제거"""
    return _call_dooray_api(access_token, "DELETE", f"/calendar/v1/calendars/{calendar_id}/permissions/{permission_id}")

def get_busy_time(access_token: str, member_ids: list, start_time: str, end_time: str):
    """멤버들의 일정 중복 시간 조회"""
    json_data = {
        "members": [{"id": mid} for mid in member_ids],
        "timeMin": start_time,
        "timeMax": end_time
    }
    return _call_dooray_api(access_token, "POST", "/calendar/v1/busytime", json_data)

# --- Reservation API ---
def get_resource_categories(access_token: str):
    return _call_dooray_api(access_token, "GET", "/reservation/v1/resource-categories")

def get_resources(access_token: str):
    return _call_dooray_api(access_token, "GET", "/reservation/v1/resources")

def get_resource(access_token: str, resource_id: str):
    return _call_dooray_api(access_token, "GET", f"/reservation/v1/resources/{resource_id}")

def get_resource_reservations(access_token: str):
    return _call_dooray_api(access_token, "GET", "/reservation/v1/resource-reservations")

def create_resource_reservation(access_token: str, resource_id: str, subject: str, started_at: str, ended_at: str, users: list = None):
    json_data = {
        "resourceId": resource_id,
        "subject": subject,
        "startedAt": started_at,
        "endedAt": ended_at,
        "users": users if users else []
    }
    return _call_dooray_api(access_token, "POST", "/reservation/v1/resource-reservations", json_data)

def get_resource_reservation(access_token: str, resource_reservation_id: str):
    return _call_dooray_api(access_token, "GET", f"/reservation/v1/resource-reservations/{resource_reservation_id}")

def update_resource_reservation(access_token: str, resource_reservation_id: str, resource_id: str = None, subject: str = None, started_at: str = None, ended_at: str = None, users: list = None):
    json_data = {}
    if resource_id: json_data["resourceId"] = resource_id
    if subject: json_data["subject"] = subject
    if started_at: json_data["startedAt"] = started_at
    if ended_at: json_data["endedAt"] = ended_at
    if users: json_data["users"] = users
    return _call_dooray_api(access_token, "PUT", f"/reservation/v1/resource-reservations/{resource_reservation_id}", json_data)

def delete_resource_reservation(access_token: str, resource_reservation_id: str):
    return _call_dooray_api(access_token, "DELETE", f"/reservation/v1/resource-reservations/{resource_reservation_id}")








# --- Enhanced Messenger API ---
def get_messenger_channels(access_token: str):
    """메신저 채널 목록 조회"""
    return _call_dooray_api(access_token, "GET", "/messenger/v1/channels")

def create_messenger_channel(access_token: str, name: str, members: list, description: str = None):
    """메신저 채널 생성"""
    json_data = {
        "name": name,
        "members": members
    }
    if description:
        json_data["description"] = description
    return _call_dooray_api(access_token, "POST", "/messenger/v1/channels", json_data)

def send_channel_message(access_token: str, channel_id: str, message: str, attachments: list = None):
    """채널에 메시지 전송"""
    json_data = {"text": message}
    if attachments:
        json_data["attachments"] = attachments
    return _call_dooray_api(access_token, "POST", f"/messenger/v1/channels/{channel_id}/messages", json_data)

def get_channel_messages(access_token: str, channel_id: str, limit: int = 50):
    """채널 메시지 목록 조회"""
    params = {"limit": limit}
    return _call_dooray_api(access_token, "GET", f"/messenger/v1/channels/{channel_id}/messages", params=params)

# --- Enhanced Hook API ---
def get_incoming_hooks(access_token: str):
    """인커밍 훅 목록 조회"""
    return _call_dooray_api(access_token, "GET", "/common/v1/incoming-hooks")

def update_incoming_hook(access_token: str, hook_id: str, name: str = None, url: str = None, description: str = None):
    """인커밍 훅 수정"""
    json_data = {}
    if name:
        json_data["name"] = name
    if url:
        json_data["url"] = url
    if description:
        json_data["description"] = description
    return _call_dooray_api(access_token, "PUT", f"/common/v1/incoming-hooks/{hook_id}", json_data)

def create_outgoing_hook(access_token: str, name: str, url: str, trigger_word: str = None):
    """아웃고잉 훅 생성"""
    json_data = {
        "name": name,
        "url": url
    }
    if trigger_word:
        json_data["triggerWord"] = trigger_word
    return _call_dooray_api(access_token, "POST", "/common/v1/outgoing-hooks", json_data)

def get_outgoing_hooks(access_token: str):
    """아웃고잉 훅 목록 조회"""
    return _call_dooray_api(access_token, "GET", "/common/v1/outgoing-hooks")

def delete_outgoing_hook(access_token: str, hook_id: str):
    """아웃고잉 훅 삭제"""
    return _call_dooray_api(access_token, "DELETE", f"/common/v1/outgoing-hooks/{hook_id}")
