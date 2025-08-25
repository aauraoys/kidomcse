from fastapi import FastAPI, Request, HTTPException
import base64 # Import base64 for file handling
import uuid
from dooray_client import (
    # Common API
    get_members,
    get_member,
    create_incoming_hook,
    get_incoming_hook,
    delete_incoming_hook,
    # Drive API
    get_drive_list,
    get_drive,
    get_drive_files,
    get_drive_file_metadata,
    download_file_base64,
    get_file_chunk,
    cleanup_temp_file,
    create_chunk_session,
    get_file_chunk_data,
    upload_drive_file,
    create_drive_folder,
    delete_drive_file,
    move_drive_file,
    copy_drive_file,
    get_drive_folder_contents,
    search_drive_files,
    # Messenger API
    send_message,
    # Project API
    get_projects,
    create_project,
    get_project,
    get_project_members,
    get_project_member,
    is_project_creatable,
    get_project_workflows,
    create_project_workflow,
    update_project_workflow,
    delete_project_workflow,
    get_project_posts,
    get_project_post,
    create_project_post,
    update_project_post,
    update_project_post_workflow,
    set_project_post_done,
    create_project_post_comment,
    get_project_post_comments,
    update_project_post_comment,
    delete_project_post_comment,
    # Wiki API
    get_wikis,
    get_wiki_pages,
    get_wiki_page,
    create_wiki_page,
    update_wiki_page,
    update_wiki_page_title,
    update_wiki_page_content,
    update_wiki_page_referrers,
    create_wiki_page_comment,
    get_wiki_page_comments,
    get_wiki_page_comment,
    update_wiki_page_comment,
    delete_wiki_page_comment,
    upload_wiki_page_file,
    get_wiki_page_file,
    delete_wiki_page_file,
    upload_wiki_file,
    # Calendar API
    get_calendars,
    get_calendar,
    create_calendar_event,
    get_calendar_events,
    get_calendar_event,
    update_calendar_event,
    delete_calendar_event,
    create_calendar,
    update_calendar,
    delete_calendar,
    get_calendar_permissions,
    add_calendar_permission,
    remove_calendar_permission,
    get_busy_time,
    # Reservation API
    get_resource_categories,
    get_resources,
    get_resource,
    get_resource_reservations,
    create_resource_reservation,
    get_resource_reservation,
    update_resource_reservation,
    delete_resource_reservation,
    # Enhanced Messenger API
    get_messenger_channels,
    create_messenger_channel,
    send_channel_message,
    get_channel_messages,
    # Enhanced Hook API
    get_incoming_hooks,
    update_incoming_hook,
    create_outgoing_hook,
    get_outgoing_hooks,
    delete_outgoing_hook,
    # Drive Changes and Shared Links API
    get_drive_changes,
    create_drive_shared_link,
    get_drive_shared_links,
    get_drive_shared_link,
    update_drive_shared_link,
    delete_drive_shared_link,
    # Project Post File Management
    upload_project_post_file,
    download_project_post_file,
    delete_project_post_file,
    set_project_post_parent,
    move_project_post,
    delete_project_post,
    get_project_milestones,
    create_project_milestone
)

# 세션 기반 토큰 저장을 위한 딕셔너리
SESSION_TOKENS = {}

from fastapi.middleware.cors import CORSMiddleware
from mcp_http import router as mcp_router
from contextlib import asynccontextmanager

# GPTs용 우선순위 API 경로 정의 (최대 30개)
PRIORITY_PATHS = [
    # 1순위 - 인증 (필수)
    "/mcp/auth/set_token",
    "/mcp/auth/status",
    
    # 2순위 - 드라이브 (파일 관리 핵심)
    "/mcp/drive/list",
    "/mcp/drive/files/list",
    "/mcp/drive/files/download_complete", # downloadFileComplete (새로운 원샷 다운로드)
    "/mcp/drive/files/download_base64",  # downloadFile (기존 청크 방식)
    "/mcp/drive/files/get_chunk",        # getFileChunk
    "/mcp/drive/files/cleanup_session",  # cleanupChunkSession
    "/mcp/drive/files/upload",
    "/mcp/drive/files/delete",
    "/mcp/drive/files/move",
    "/mcp/drive/files/copy",
    "/mcp/drive/folders/create",
    
    # 3순위 - 프로젝트 (업무 관리)
    "/mcp/project/list",
    "/mcp/project/create",
    "/mcp/project/get",
    "/mcp/project/posts/list",
    "/mcp/project/posts/get",
    "/mcp/project/posts/create",
    "/mcp/project/posts/update",
    "/mcp/project/posts/comments/create",
    "/mcp/project/posts/comments/list",
    "/mcp/project/members/list",
    
    # 4순위 - 위키
    "/mcp/wiki/list",
    "/mcp/wiki/pages/list",
    "/mcp/wiki/pages/get",
    "/mcp/wiki/pages/create",
    "/mcp/wiki/pages/update",
    "/mcp/wiki/pages/files/upload",
    
    # 5순위 - 메신저 (공간이 있으면)
    "/mcp/messenger/send"
]

# lifespan 함수 정의 (app 정의 전에 위치)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 lifespan 관리 - 시작 시 스키마 생성"""
    # Startup
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title="Dooray MCP API",
        version="2.0.0",
        description="Official Dooray API integration for ChatGPT - Top 30 priority APIs",
        routes=app.routes,
        servers=[{"url": "https://kic-dooray-mcp.onrender.com", "description": "Production server"}]
    )
    
    # GPTs 30개 제한을 위한 우선순위 필터링
    filtered_paths = {}
    for path in PRIORITY_PATHS[:30]:  # 최대 30개만
        if path in openapi_schema.get("paths", {}):
            filtered_paths[path] = openapi_schema["paths"][path]
    
    # 핵심 API들에 명시적인 requestBody 스키마 추가
    if "/mcp/auth/set_token" in filtered_paths:
        set_token_path = filtered_paths["/mcp/auth/set_token"]
        if "post" in set_token_path:
            set_token_path["post"]["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "token": {
                                    "type": "string",
                                    "description": "Dooray API token"
                                }
                            },
                            "required": ["token"]
                        },
                        "example": {
                            "token": "your_dooray_api_token_here"
                        }
                    }
                }
            }
    
    # 드라이브 파일 목록 API 스키마 추가
    if "/mcp/drive/files/list" in filtered_paths:
        drive_files_path = filtered_paths["/mcp/drive/files/list"]
        if "post" in drive_files_path:
            drive_files_path["post"]["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "drive_id": {
                                    "type": "string",
                                    "description": "Drive ID to list files from"
                                }
                            },
                            "required": ["drive_id"]
                        },
                        "example": {
                            "drive_id": "4025223258147514341"
                        }
                    }
                }
            }
    
    # 드라이브 파일 완전 다운로드 API 스키마 추가
    if "/mcp/drive/files/download_complete" in filtered_paths:
        complete_download_path = filtered_paths["/mcp/drive/files/download_complete"]
        if "post" in complete_download_path:
            complete_download_path["post"]["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "drive_id": {
                                    "type": "string",
                                    "description": "Drive ID where the file is located"
                                },
                                "file_id": {
                                    "type": "string", 
                                    "description": "File ID to download"
                                }
                            },
                            "required": ["drive_id", "file_id"]
                        },
                        "example": {
                            "drive_id": "4025223258147514341",
                            "file_id": "4139468188722698827"
                        }
                    }
                }
            }

    # 드라이브 파일 다운로드 API 스키마 추가
    if "/mcp/drive/files/download_base64" in filtered_paths:
        download_path = filtered_paths["/mcp/drive/files/download_base64"]
        if "post" in download_path:
            download_path["post"]["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "drive_id": {
                                    "type": "string",
                                    "description": "Drive ID where the file is located"
                                },
                                "file_id": {
                                    "type": "string", 
                                    "description": "File ID to download"
                                },
                                "media": {
                                    "type": "string",
                                    "description": "Media type for download",
                                    "default": "raw"
                                }
                            },
                            "required": ["drive_id", "file_id"]
                        },
                        "example": {
                            "drive_id": "4025223258147514341",
                            "file_id": "4139468188722698827",
                            "media": "raw"
                        }
                    }
                }
            }
    
    # 파일 청크 다운로드 API 스키마 추가
    if "/mcp/drive/files/get_chunk" in filtered_paths:
        chunk_path = filtered_paths["/mcp/drive/files/get_chunk"]
        if "post" in chunk_path:
            chunk_path["post"]["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "chunkSessionId": {
                                    "type": "string",
                                    "description": "Chunk session ID from downloadFile response"
                                },
                                "chunkIndex": {
                                    "type": "integer",
                                    "description": "Index of the chunk to download"
                                }
                            },
                            "required": ["chunkSessionId", "chunkIndex"]
                        },
                        "example": {
                            "chunkSessionId": "session_123",
                            "chunkIndex": 0
                        }
                    }
                }
            }
    
    # 프로젝트 포스트 생성 API 스키마 추가
    if "/mcp/project/posts/create" in filtered_paths:
        create_post_path = filtered_paths["/mcp/project/posts/create"]
        if "post" in create_post_path:
            create_post_path["post"]["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "project_id": {
                                    "type": "string",
                                    "description": "Project ID to create post in"
                                },
                                "subject": {
                                    "type": "string",
                                    "description": "Post subject/title"
                                },
                                "body": {
                                    "type": "string",
                                    "description": "Post content/body"
                                }
                            },
                            "required": ["project_id", "subject", "body"]
                        },
                        "example": {
                            "project_id": "123456789",
                            "subject": "새로운 업무",
                            "body": "업무 내용입니다"
                        }
                    }
                }
            }
    
    # 위키 페이지 생성 API 스키마 추가
    if "/mcp/wiki/pages/create" in filtered_paths:
        create_wiki_path = filtered_paths["/mcp/wiki/pages/create"]
        if "post" in create_wiki_path:
            create_wiki_path["post"]["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "wiki_id": {
                                    "type": "string",
                                    "description": "Wiki ID to create page in"
                                },
                                "subject": {
                                    "type": "string",
                                    "description": "Page title"
                                },
                                "body": {
                                    "type": "string",
                                    "description": "Page content"
                                }
                            },
                            "required": ["wiki_id", "subject", "body"]
                        },
                        "example": {
                            "wiki_id": "123456789",
                            "subject": "새로운 페이지",
                            "body": "페이지 내용입니다"
                        }
                    }
                }
            }
    
    openapi_schema["paths"] = filtered_paths
    
    # GPTs를 위한 operationId 최적화
    for path, path_item in openapi_schema.get("paths", {}).items():
        for method, operation in path_item.items():
            if isinstance(operation, dict) and "operationId" not in operation:
                operation_name = operation.get("summary", "").replace(" ", "")
                if not operation_name:
                    operation_name = f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '')}"
                operation["operationId"] = operation_name
    
    app.openapi_schema = openapi_schema
    yield
    # Shutdown (필요시 정리 작업)

app = FastAPI(
    title="Dooray MCP API",
    version="2.0.0",
    description="Official Dooray API integration for ChatGPT - Dynamically generated schema",
    servers=[
        {
            "url": "https://kic-dooray-mcp.onrender.com",
            "description": "Production server"
        }
    ],
    lifespan=lifespan
)

# CORS 설정 추가
origins = [
    "*" # 모든 출처 허용 (개발 단계에서 편리, 프로덕션에서는 특정 도메인으로 제한 권장)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # 모든 HTTP 메서드 허용
    allow_headers=["*"], # 모든 헤더 허용
)

app.include_router(mcp_router)

# Claude 및 기타 LLM 연동을 위한 표준 엔드포인트
@app.get("/")
async def read_root():
    return {"message": "Dooray MCP is running."}

@app.post("/register")
async def register():
    return {"status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "MCP server is healthy"}

@app.get("/mcp")
async def mcp_base():
    return {"message": "Dooray MCP base endpoint. Use /mcp/<service>/<action> for specific APIs."}


@app.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource():
    return {"status": "ok"}

@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server():
    return {"status": "ok"}

# --- 인증 API ---
@app.post(
    "/mcp/auth/set_token",
    summary="Set API token", 
    description="Set Dooray API token for authentication. Send JSON with token field.",
    operation_id="setAuthToken",
    responses={
        200: {
            "description": "Token set successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "토큰이 성공적으로 설정되었습니다."
                    }
                }
            }
        }
    }
)
async def set_token(request: Request):
    """
    현재 대화 세션에 대한 Dooray API 토큰을 설정합니다.
    다양한 클라이언트의 세션 ID 헤더를 지원합니다.
    """
    # 다양한 헤더에서 세션 ID 찾기
    conversation_id = (
        request.headers.get("claude-conversation-id") or 
        request.headers.get("X-Conversation-ID") or
        request.headers.get("X-Request-ID") or
        request.headers.get("X-Session-ID") or
        request.headers.get("User-Agent", "").split("/")[-1] if "/" in request.headers.get("User-Agent", "") else None
    )
    
    # 세션 ID가 없으면 고정 토큰으로 사용 (GPTs용 대안)
    if not conversation_id:
        conversation_id = "default_gpts_session"

    try:
        body = await request.json()
        token = body.get("token")
        if not token:
            return {
                "success": False,
                "error_type": "parameter_required",
                "message": "요청 본문에 'token'이 필요합니다.",
                "dooray_response": None
            }
    except Exception:
        return {
            "success": False,
            "error_type": "invalid_request",
            "message": "잘못된 JSON 형식의 요청 본문입니다.",
            "dooray_response": None
        }

    SESSION_TOKENS[conversation_id] = token
    return {
        "success": True,
        "message": "현재 세션에 대한 API 토큰이 성공적으로 설정되었습니다.",
        "session_id": conversation_id
    }


def _handle_api_call(result):
    """두레이 API 응답을 공식 형식으로 처리"""
    if "error" in result:
        return {
            "header": {
                "isSuccessful": False,
                "resultCode": result.get("status_code", -1),
                "resultMessage": result.get("error", "API 오류가 발생했습니다.")
            },
            "result": None
        }
    
    # 성공적인 응답의 경우
    return {
        "header": {
            "isSuccessful": True,
            "resultCode": 0,
            "resultMessage": ""
        },
        "result": result
    }

def _get_api_key(request: Request):
    """
    하이브리드 인증 방식:
    1. 세션 ID를 사용하여 세션별 토큰을 우선적으로 확인합니다.
    2. 세션 토큰이 없으면 헤더의 고정 API 키를 사용합니다.
    """
    # 1. 세션 기반 인증 시도 (다양한 헤더 지원)
    conversation_id = (
        request.headers.get("claude-conversation-id") or 
        request.headers.get("X-Conversation-ID") or
        request.headers.get("X-Request-ID") or
        request.headers.get("X-Session-ID") or
        request.headers.get("User-Agent", "").split("/")[-1] if "/" in request.headers.get("User-Agent", "") else None
    )
    
    if conversation_id:
        token = SESSION_TOKENS.get(conversation_id)
        if token:
            return token

    # 2. 고정 API 키 인증으로 대체
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            api_key = auth_header.split(" ")[1]

    return api_key  # None이면 토큰 없음

def _create_auth_required_response():
    """토큰이 필요할 때 사용자 친화적 응답 생성"""
    return {
        "success": False,
        "error_type": "authentication_required", 
        "message": "Dooray API 토큰이 필요합니다.",
        "instructions": "1. Dooray → 설정 → API 토큰에서 개인 토큰을 생성하세요.\n2. '/mcp/auth/set_token' 엔드포인트를 호출해서 토큰을 설정하세요.",
        "dooray_response": None
    }

def _create_error_response(error_message, result_code=-1):
    """공식 두레이 형식의 에러 응답 생성"""
    return {
        "header": {
            "isSuccessful": False,
            "resultCode": result_code,
            "resultMessage": error_message
        },
        "result": None
    }

def _handle_api_call_with_auth(request: Request, api_func, *args, **kwargs):
    """인증이 필요한 API 호출을 처리하는 헬퍼 함수"""
    api_key = _get_api_key(request)
    if not api_key:
        return _create_auth_required_response()
    
    try:
        result = api_func(api_key, *args, **kwargs)
        return _handle_api_call(result)
    except Exception as e:
        return _create_error_response(f"API 호출 중 오류가 발생했습니다: {str(e)}", -500)

# --- 인증 상태 확인 API ---
@app.get(
    "/mcp/auth/status",
    summary="Check authentication status",
    description="Check current authentication status and token validity",
    operation_id="getAuthStatus"
)
async def check_auth_status(request: Request):
    """현재 세션의 인증 상태를 확인합니다"""
    api_key = _get_api_key(request)
    conversation_id = (
        request.headers.get("claude-conversation-id") or 
        request.headers.get("X-Conversation-ID") or
        request.headers.get("X-Request-ID") or
        request.headers.get("X-Session-ID") or
        request.headers.get("User-Agent", "").split("/")[-1] if "/" in request.headers.get("User-Agent", "") else "default_gpts_session"
    )
    
    if not api_key:
        return {
            "authenticated": False,
            "token_valid": False,
            "session_id": conversation_id,
            "message": "API 토큰이 설정되지 않았습니다. '/mcp/auth/set_token'을 사용하여 토큰을 설정해주세요."
        }
    
    # 토큰이 설정되어 있으면 유효하다고 간주 (MCP 서버가 정상 작동 중)
    # 실제 API 호출은 각 기능에서 개별적으로 처리
    
    return {
        "authenticated": True,
        "token_valid": True,
        "session_id": conversation_id,
        "message": "인증이 정상적으로 설정되었습니다."
    }

# --- Common API ---
@app.post("/mcp/common/members/list")
async def api_get_members(request: Request):
    return _handle_api_call_with_auth(request, get_members)

@app.post("/mcp/common/members/get")
async def api_get_member(request: Request):
    body = await request.json()
    member_id = body.get("member_id")
    if not member_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "member_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    return _handle_api_call_with_auth(request, get_member, member_id)

@app.post("/mcp/common/incoming_hooks/create")
async def api_create_incoming_hook(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    name = body.get("name")
    url = body.get("url")
    description = body.get("description")
    if not name or not url:
        raise HTTPException(status_code=400, detail="name and url are required")
    result = create_incoming_hook(api_key, name, url, description)
    return _handle_api_call(result)

@app.post("/mcp/common/incoming_hooks/get")
async def api_get_incoming_hook(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    incoming_hook_id = body.get("incoming_hook_id")
    if not incoming_hook_id:
        raise HTTPException(status_code=400, detail="incoming_hook_id is required")
    result = get_incoming_hook(api_key, incoming_hook_id)
    return _handle_api_call(result)

@app.post("/mcp/common/incoming_hooks/delete")
async def api_delete_incoming_hook(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    incoming_hook_id = body.get("incoming_hook_id")
    if not incoming_hook_id:
        raise HTTPException(status_code=400, detail="incoming_hook_id is required")
    result = delete_incoming_hook(api_key, incoming_hook_id)
    return _handle_api_call(result)


# --- Drive API ---
@app.post("/mcp/drive/list")
async def api_get_drive_list(request: Request):
    body = await request.json()
    drive_type = body.get("type", "private")
    return _handle_api_call_with_auth(request, get_drive_list, drive_type)

@app.post("/mcp/drive/get")
async def api_get_drive(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    if not drive_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    return _handle_api_call_with_auth(request, get_drive, drive_id)

@app.post(
    "/mcp/drive/files/list",
    summary="List drive files",
    description="Get list of files in a specific drive",
    operation_id="listDriveFiles"
)
async def api_get_drive_files(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    if not drive_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    return _handle_api_call_with_auth(request, get_drive_files, drive_id)

@app.post("/mcp/drive/files/metadata")
async def api_get_drive_file_metadata(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    file_id = body.get("file_id")
    if not drive_id or not file_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id와 file_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    return _handle_api_call_with_auth(request, get_drive_file_metadata, drive_id, file_id)

@app.post("/mcp/drive/files/download")
async def api_download_drive_file(request: Request):
    """
    파일 다운로드 - 청킹 시스템 사용
    ResponseTooLargeError 방지를 위해 첫 번째 청크만 반환
    """
    api_key = _get_api_key(request)
    if not api_key:
        return _create_auth_required_response()
    
    body = await request.json()
    drive_id = body.get("drive_id")
    file_id = body.get("file_id")
    media = body.get("media", "raw")
    
    if not drive_id or not file_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id와 file_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    # 청킹 시스템 사용하여 첫 번째 청크 반환
    result = download_file_base64(api_key, drive_id, file_id, media)
    
    if "error" in result:
        return {
            "success": False,
            "error_type": "dooray_api_error",
            "message": result["error"],
            "dooray_response": None
        }
    
    return {
        "success": True,
        "message": "파일 다운로드 시작 (청킹 시스템)",
        "dooray_response": result,
        "chunking_info": {
            "description": "대용량 파일은 청크 단위로 다운로드됩니다.",
            "next_chunk_endpoint": "/mcp/drive/files/get_chunk",
            "parameters": {
                "chunkSessionId": result.get("chunkSessionId"),
                "chunkIndex": "다음 청크 인덱스 (1부터 시작)"
            },
            "total_chunks": result.get("totalChunks", 1),
            "current_chunk": 0
        }
    }

@app.post(
    "/mcp/drive/files/download_complete",
    summary="Complete file download (one-shot)",
    description="Download entire file at once and return base64 data or download URL for large files.",
    operation_id="downloadFileComplete"
)
async def api_download_file_complete(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    file_id = body.get("file_id")
    
    if not drive_id or not file_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id와 file_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    api_key = _get_api_key(request)
    if not api_key:
        return {
            "success": False,
            "error_type": "authentication_required",
            "message": "Dooray API 토큰이 필요합니다.",
            "dooray_response": None
        }
    
    try:
        # 메타데이터 확인
        metadata = get_drive_file_metadata(api_key, drive_id, file_id)
        if "error" in metadata:
            return {
                "success": False,
                "error_type": "dooray_api_error",
                "message": metadata["error"],
                "dooray_response": None
            }
        
        file_info = metadata.get("result", {})
        file_name = file_info.get("name", "unknown")
        file_size = file_info.get("size", 0)
        
        # 5MB 이하 파일: 서버측 병합 후 단일 파일 반환
        if file_size <= 5 * 1024 * 1024:  # 5MB
            session_id = str(uuid.uuid4())
            result = create_chunk_session(api_key, drive_id, file_id, session_id)
            
            if "error" in result:
                return {
                    "success": False,
                    "error_type": "dooray_api_error",
                    "message": result["error"],
                    "dooray_response": None
                }
            
            # 모든 청크를 서버에서 병합
            from dooray_client import chunk_sessions
            if session_id in chunk_sessions:
                chunks = chunk_sessions[session_id]["chunks"]
                
                # 모든 청크를 디코딩 후 병합
                merged_data = b""
                for chunk_b64 in chunks:
                    merged_data += base64.b64decode(chunk_b64)
                
                # 다시 base64로 인코딩
                final_data = base64.b64encode(merged_data).decode('utf-8')
                
                # 청크 세션 정리
                del chunk_sessions[session_id]
                
                return {
                    "success": True,
                    "message": f"파일 다운로드 완료: {file_name}",
                    "dooray_response": {
                        "fileName": file_name,
                        "fileSize": file_size,
                        "fileData": final_data,
                        "downloadType": "merged",
                        "originalChunks": len(chunks)
                    }
                }
        
        # 대용량 파일: 서버측 병합 후 임시 URL 제공
        return {
            "success": True,
            "message": f"대용량 파일 처리 중: {file_name}",
            "dooray_response": {
                "fileName": file_name,
                "fileSize": file_size,
                "downloadType": "processing",
                "note": "대용량 파일은 서버측 병합 후 URL 제공 예정"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error_type": "server_error",
            "message": f"파일 다운로드 중 오류: {str(e)}",
            "dooray_response": None
        }

@app.post(
    "/mcp/drive/files/download_base64",
    summary="Initialize file download session",
    description="Initialize a chunked download session for large files. Returns session info for chunk-based downloading.",
    operation_id="downloadFile"
)
async def api_download_file_base64(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    file_id = body.get("file_id")
    media = body.get("media", "raw")

    if not drive_id or not file_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id와 file_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    # 파일 메타데이터 확인 및 청크 세션 생성
    api_key = _get_api_key(request)
    if not api_key:
        return {
            "success": False,
            "error_type": "authentication_required",
            "message": "Dooray API 토큰이 필요합니다.",
            "dooray_response": None
        }
    
    try:
        # 세션 ID 생성
        session_id = str(uuid.uuid4())
        
        # 실제 청크 세션 생성 (파일 다운로드 포함)
        result = create_chunk_session(api_key, drive_id, file_id, session_id)
        
        if "error" in result:
            return {
                "success": False,
                "error_type": "dooray_api_error",
                "message": result["error"],
                "dooray_response": None
            }
        
        return {
            "success": True,
            "message": f"파일 다운로드 세션이 생성되었습니다: {result['result']['fileName']}",
            "dooray_response": result["result"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error_type": "server_error",
            "message": f"세션 생성 중 오류가 발생했습니다: {str(e)}",
            "dooray_response": None
        }

@app.post(
    "/mcp/drive/files/get_chunk",
    summary="Get file chunk",
    description="Get a specific chunk of a file using chunk session ID and index",
    operation_id="getFileChunk"
)
async def api_get_file_chunk(request: Request):
    body = await request.json()
    session_id = body.get("chunkSessionId")
    chunk_index = body.get("chunkIndex")

    if not session_id or chunk_index is None:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "chunkSessionId and chunkIndex 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    # 인증 확인
    api_key = _get_api_key(request)
    if not api_key:
        return {
            "success": False,
            "error_type": "authentication_required",
            "message": "Dooray API 토큰이 필요합니다.",
            "dooray_response": None
        }
    
    try:
        # 실제 청크 데이터 가져오기
        result = get_file_chunk_data(session_id, chunk_index)
        
        if "error" in result:
            return {
                "success": False,
                "error_type": "chunk_error",
                "message": result["error"],
                "dooray_response": None
            }
        
        return {
            "success": True,
            "message": f"청크 {chunk_index} 완료",
            "dooray_response": result["result"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error_type": "server_error",
            "message": f"청크 다운로드 중 오류가 발생했습니다: {str(e)}",
            "dooray_response": None
        }

@app.post(
    "/mcp/drive/files/cleanup_session",
    summary="Cleanup chunk session",
    description="Clean up chunking session and delete temporary files",
    operation_id="cleanupChunkSession"
)
async def api_cleanup_chunk_session(request: Request):
    """청킹 세션 정리 - 임시 파일 삭제"""
    body = await request.json()
    session_id = body.get("chunkSessionId")

    if not session_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "chunkSessionId 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    cleanup_temp_file(session_id)
    return {
        "success": True,
        "message": "청킹 세션이 정리되었습니다.",
        "dooray_response": {"session_id": session_id, "cleaned": True}
    }

@app.post("/mcp/drive/files/upload")
async def api_upload_drive_file(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    folder_id = body.get("folder_id")
    file_name = body.get("file_name")
    file_content_base64 = body.get("file_content_base64")
    
    if not drive_id or not folder_id or not file_name or not file_content_base64:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id, folder_id, file_name, file_content_base64 파라미터가 모두 필요합니다.",
            "dooray_response": None
        }
    
    try:
        file_content = base64.b64decode(file_content_base64)
    except Exception:
        return {
            "success": False,
            "error_type": "invalid_parameter",
            "message": "file_content_base64가 올바른 Base64 형식이 아닙니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, upload_drive_file, drive_id, folder_id, file_name, file_content)

@app.post("/mcp/drive/folders/create")
async def api_create_drive_folder(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    parent_folder_id = body.get("parent_folder_id")
    folder_name = body.get("folder_name")
    
    if not drive_id or not parent_folder_id or not folder_name:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id, parent_folder_id, folder_name 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, create_drive_folder, drive_id, parent_folder_id, folder_name)

@app.post("/mcp/drive/files/delete")
async def api_delete_drive_file(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    file_id = body.get("file_id")
    
    if not drive_id or not file_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id와 file_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, delete_drive_file, drive_id, file_id)

@app.post("/mcp/drive/files/move")
async def api_move_drive_file(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    file_id = body.get("file_id")
    target_folder_id = body.get("target_folder_id")
    
    if not drive_id or not file_id or not target_folder_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id, file_id, target_folder_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, move_drive_file, drive_id, file_id, target_folder_id)

@app.post("/mcp/drive/files/copy")
async def api_copy_drive_file(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    file_id = body.get("file_id")
    target_drive_id = body.get("target_drive_id", drive_id)  # 기본값은 동일 드라이브
    target_folder_id = body.get("target_folder_id")
    
    if not drive_id or not file_id or not target_folder_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id, file_id, target_folder_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, copy_drive_file, drive_id, file_id, target_drive_id, target_folder_id)

@app.post("/mcp/drive/folders/contents")
async def api_get_drive_folder_contents(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    folder_id = body.get("folder_id")
    
    if not drive_id or not folder_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id와 folder_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, get_drive_folder_contents, drive_id, folder_id)

@app.post("/mcp/drive/search")
async def api_search_drive_files(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    query = body.get("query")
    
    if not drive_id or not query:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id와 query 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, search_drive_files, drive_id, query)

@app.post("/mcp/drive/changes")
async def api_get_drive_changes(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    page_token = body.get("page_token")
    include_removed = body.get("include_removed", False)
    
    if not drive_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, get_drive_changes, drive_id, page_token, include_removed)

# --- Drive Shared Links API ---
@app.post("/mcp/drive/shared_links/create")
async def api_create_drive_shared_link(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    file_id = body.get("file_id")
    scope = body.get("scope", "memberAndGuestAndExternal")
    expired_at = body.get("expired_at")
    
    if not drive_id or not file_id or not expired_at:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id, file_id, expired_at 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, create_drive_shared_link, drive_id, file_id, scope, expired_at)

@app.post("/mcp/drive/shared_links/list")
async def api_get_drive_shared_links(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    file_id = body.get("file_id")
    valid = body.get("valid", True)
    
    if not drive_id or not file_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id와 file_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, get_drive_shared_links, drive_id, file_id, valid)

@app.post("/mcp/drive/shared_links/get")
async def api_get_drive_shared_link(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    file_id = body.get("file_id")
    link_id = body.get("link_id")
    
    if not drive_id or not file_id or not link_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id, file_id, link_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, get_drive_shared_link, drive_id, file_id, link_id)

@app.post("/mcp/drive/shared_links/update")
async def api_update_drive_shared_link(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    file_id = body.get("file_id")
    link_id = body.get("link_id")
    scope = body.get("scope")
    expired_at = body.get("expired_at")
    
    if not drive_id or not file_id or not link_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id, file_id, link_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    if not scope and not expired_at:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "수정할 필드(scope 또는 expired_at) 중 하나는 제공해야 합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, update_drive_shared_link, drive_id, file_id, link_id, scope, expired_at)

@app.post("/mcp/drive/shared_links/delete")
async def api_delete_drive_shared_link(request: Request):
    body = await request.json()
    drive_id = body.get("drive_id")
    file_id = body.get("file_id")
    link_id = body.get("link_id")
    
    if not drive_id or not file_id or not link_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "drive_id, file_id, link_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, delete_drive_shared_link, drive_id, file_id, link_id)

# --- Messenger API ---
@app.post("/mcp/messenger/send")
async def api_send_message(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    recipient_id = body.get("recipient_id")
    message = body.get("message")

    if not recipient_id or not message:
        raise HTTPException(status_code=400, detail="recipient_id and message are required")

    result = send_message(api_key, recipient_id, message)
    return _handle_api_call(result)

# --- Project API ---
@app.post("/mcp/project/list")
async def api_get_projects(request: Request):
    return _handle_api_call_with_auth(request, get_projects)

@app.post("/mcp/project/create")
async def api_create_project(request: Request):
    body = await request.json()
    name = body.get("name")
    code = body.get("code")
    description = body.get("description")

    if not name or not code:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "프로젝트 이름(name)과 코드(code) 파라미터가 필요합니다.",
            "dooray_response": None
        }

    return _handle_api_call_with_auth(request, create_project, name, code, description)

@app.post("/mcp/project/get")
async def api_get_project(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")
    result = get_project(api_key, project_id)
    return _handle_api_call(result)

@app.post("/mcp/project/members/list")
async def api_get_project_members(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")
    result = get_project_members(api_key, project_id)
    return _handle_api_call(result)

@app.post("/mcp/project/members/get")
async def api_get_project_member(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    member_id = body.get("member_id")
    if not project_id or not member_id:
        raise HTTPException(status_code=400, detail="project_id and member_id are required")
    result = get_project_member(api_key, project_id, member_id)
    return _handle_api_call(result)

@app.post("/mcp/project/is_creatable")
async def api_is_project_creatable(request: Request):
    api_key = _get_api_key(request)
    result = is_project_creatable(api_key)
    return _handle_api_call(result)

@app.post("/mcp/project/workflows/list")
async def api_get_project_workflows(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")
    result = get_project_workflows(api_key, project_id)
    return _handle_api_call(result)

@app.post("/mcp/project/workflows/create")
async def api_create_project_workflow(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    name = body.get("name")
    description = body.get("description")
    if not project_id or not name:
        raise HTTPException(status_code=400, detail="project_id and name are required")
    result = create_project_workflow(api_key, project_id, name, description)
    return _handle_api_call(result)

@app.post("/mcp/project/workflows/update")
async def api_update_project_workflow(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    workflow_id = body.get("workflow_id")
    name = body.get("name")
    description = body.get("description")
    if not project_id or not workflow_id or (not name and not description):
        raise HTTPException(status_code=400, detail="project_id, workflow_id and either name or description are required")
    result = update_project_workflow(api_key, project_id, workflow_id, name, description)
    return _handle_api_call(result)

@app.post("/mcp/project/workflows/delete")
async def api_delete_project_workflow(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    workflow_id = body.get("workflow_id")
    if not project_id or not workflow_id:
        raise HTTPException(status_code=400, detail="project_id and workflow_id are required")
    result = delete_project_workflow(api_key, project_id, workflow_id)
    return _handle_api_call(result)

@app.post("/mcp/project/posts/list")
async def api_get_project_posts(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")
    result = get_project_posts(api_key, project_id)
    return _handle_api_call(result)

@app.post("/mcp/project/posts/get")
async def api_get_project_post(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    if not project_id or not post_id:
        raise HTTPException(status_code=400, detail="project_id and post_id are required")
    result = get_project_post(api_key, project_id, post_id)
    return _handle_api_call(result)

@app.post("/mcp/project/posts/create")
async def api_create_project_post(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    subject = body.get("subject")
    post_body = body.get("body", "")
    post_type = body.get("post_type", "task")

    if not project_id or not subject:
        raise HTTPException(status_code=400, detail="project_id and subject are required")

    result = create_project_post(api_key, project_id, subject, post_body, post_type)
    return _handle_api_call(result)

@app.post("/mcp/project/posts/update")
async def api_update_project_post(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    subject = body.get("subject")
    post_body = body.get("body")

    if not project_id or not post_id or (not subject and not post_body):
        raise HTTPException(status_code=400, detail="project_id, post_id and either subject or body are required")

    result = update_project_post(api_key, project_id, post_id, subject, post_body)
    return _handle_api_call(result)

@app.post("/mcp/project/posts/update_workflow")
async def api_update_project_post_workflow(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    workflow_id = body.get("workflow_id")

    if not project_id or not post_id or not workflow_id:
        raise HTTPException(status_code=400, detail="project_id, post_id and workflow_id are required")

    result = update_project_post_workflow(api_key, project_id, post_id, workflow_id)
    return _handle_api_call(result)

@app.post("/mcp/project/posts/set_done")
async def api_set_project_post_done(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")

    if not project_id or not post_id:
        raise HTTPException(status_code=400, detail="project_id and post_id are required")

    result = set_project_post_done(api_key, project_id, post_id)
    return _handle_api_call(result)

@app.post("/mcp/project/comments/create")
async def api_create_project_post_comment(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    content = body.get("content")

    if not project_id or not post_id or not content:
        raise HTTPException(status_code=400, detail="project_id, post_id and content are required")

    result = create_project_post_comment(api_key, project_id, post_id, content)
    return _handle_api_call(result)

@app.post("/mcp/project/comments/list")
async def api_get_project_post_comments(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")

    if not project_id or not post_id:
        raise HTTPException(status_code=400, detail="project_id and post_id are required")

    result = get_project_post_comments(api_key, project_id, post_id)
    return _handle_api_call(result)

@app.post("/mcp/project/comments/update")
async def api_update_project_post_comment(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    comment_id = body.get("comment_id")
    content = body.get("content")

    if not project_id or not post_id or not comment_id or not content:
        raise HTTPException(status_code=400, detail="project_id, post_id, comment_id and content are required")

    result = update_project_post_comment(api_key, project_id, post_id, comment_id, content)
    return _handle_api_call(result)

@app.post("/mcp/project/comments/delete")
async def api_delete_project_post_comment(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    comment_id = body.get("comment_id")

    if not project_id or not post_id or not comment_id:
        raise HTTPException(status_code=400, detail="project_id, post_id and comment_id are required")

    result = delete_project_post_comment(api_key, project_id, post_id, comment_id)
    return _handle_api_call(result)

# --- Project Post File Management ---
@app.post("/mcp/project/posts/files/upload")
async def api_upload_project_post_file(request: Request):
    body = await request.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    file_name = body.get("file_name")
    file_content_base64 = body.get("file_content_base64")
    
    if not project_id or not post_id or not file_name or not file_content_base64:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "project_id, post_id, file_name, file_content_base64 파라미터가 모두 필요합니다.",
            "dooray_response": None
        }
    
    try:
        file_content = base64.b64decode(file_content_base64)
    except Exception:
        return {
            "success": False,
            "error_type": "invalid_parameter",
            "message": "file_content_base64가 올바른 Base64 형식이 아닙니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, upload_project_post_file, project_id, post_id, file_name, file_content)

@app.post("/mcp/project/posts/files/download")
async def api_download_project_post_file(request: Request):
    body = await request.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    file_id = body.get("file_id")
    
    if not project_id or not post_id or not file_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "project_id, post_id, file_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, download_project_post_file, project_id, post_id, file_id)

@app.post("/mcp/project/posts/files/delete")
async def api_delete_project_post_file(request: Request):
    body = await request.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    file_id = body.get("file_id")
    
    if not project_id or not post_id or not file_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "project_id, post_id, file_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, delete_project_post_file, project_id, post_id, file_id)

@app.post("/mcp/project/posts/set_parent")
async def api_set_project_post_parent(request: Request):
    body = await request.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    parent_post_id = body.get("parent_post_id")
    
    if not project_id or not post_id or not parent_post_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "project_id, post_id, parent_post_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, set_project_post_parent, project_id, post_id, parent_post_id)

@app.post("/mcp/project/posts/move")
async def api_move_project_post(request: Request):
    body = await request.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    target_project_id = body.get("target_project_id")
    
    if not project_id or not post_id or not target_project_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "project_id, post_id, target_project_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, move_project_post, project_id, post_id, target_project_id)

@app.post("/mcp/project/posts/delete")
async def api_delete_project_post(request: Request):
    body = await request.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    
    if not project_id or not post_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "project_id와 post_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, delete_project_post, project_id, post_id)

@app.post("/mcp/project/milestones/list")
async def api_get_project_milestones(request: Request):
    body = await request.json()
    project_id = body.get("project_id")
    
    if not project_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "project_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, get_project_milestones, project_id)

@app.post("/mcp/project/milestones/create")
async def api_create_project_milestone(request: Request):
    body = await request.json()
    project_id = body.get("project_id")
    name = body.get("name")
    description = body.get("description")
    due_date = body.get("due_date")
    
    if not project_id or not name:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "project_id와 name 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, create_project_milestone, project_id, name, description, due_date)

# --- Wiki API ---
@app.post("/mcp/wiki/list")
async def api_get_wikis(request: Request):
    api_key = _get_api_key(request)
    result = get_wikis(api_key)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/list")
async def api_get_wiki_pages(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    if not wiki_id:
        raise HTTPException(status_code=400, detail="wiki_id is required")
    result = get_wiki_pages(api_key, wiki_id)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/get")
async def api_get_wiki_page(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    page_id = body.get("page_id")
    if not wiki_id or not page_id:
        raise HTTPException(status_code=400, detail="wiki_id and page_id are required")
    result = get_wiki_page(api_key, wiki_id, page_id)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/create")
async def api_create_wiki_page(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    title = body.get("title")
    content = body.get("content")
    parent_page_id = body.get("parent_page_id")

    if not wiki_id or not title or not content:
        raise HTTPException(status_code=400, detail="wiki_id, title and content are required")

    result = create_wiki_page(api_key, wiki_id, title, content, parent_page_id)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/update")
async def api_update_wiki_page(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    page_id = body.get("page_id")
    title = body.get("title")
    content = body.get("content")

    if not wiki_id or not page_id or (not title and not content):
        raise HTTPException(status_code=400, detail="wiki_id, page_id and either title or content are required")

    result = update_wiki_page(api_key, wiki_id, page_id, title, content)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/update_title")
async def api_update_wiki_page_title(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    page_id = body.get("page_id")
    title = body.get("title")
    if not wiki_id or not page_id or not title:
        raise HTTPException(status_code=400, detail="wiki_id, page_id and title are required")
    result = update_wiki_page_title(api_key, wiki_id, page_id, title)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/update_content")
async def api_update_wiki_page_content(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    page_id = body.get("page_id")
    content = body.get("content")
    if not wiki_id or not page_id or not content:
        raise HTTPException(status_code=400, detail="wiki_id, page_id and content are required")
    result = update_wiki_page_content(api_key, wiki_id, page_id, content)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/update_referrers")
async def api_update_wiki_page_referrers(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    page_id = body.get("page_id")
    referrers = body.get("referrers")
    if not wiki_id or not page_id or not referrers:
        raise HTTPException(status_code=400, detail="wiki_id, page_id and referrers are required")
    result = update_wiki_page_referrers(api_key, wiki_id, page_id, referrers)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/comments/create")
async def api_create_wiki_page_comment(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    page_id = body.get("page_id")
    content = body.get("content")
    if not wiki_id or not page_id or not content:
        raise HTTPException(status_code=400, detail="wiki_id, page_id and content are required")
    result = create_wiki_page_comment(api_key, wiki_id, page_id, content)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/comments/list")
async def api_get_wiki_page_comments(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    page_id = body.get("page_id")
    if not wiki_id or not page_id:
        raise HTTPException(status_code=400, detail="wiki_id and page_id are required")
    result = get_wiki_page_comments(api_key, wiki_id, page_id)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/comments/get")
async def api_get_wiki_page_comment(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    page_id = body.get("page_id")
    comment_id = body.get("comment_id")
    if not wiki_id or not page_id or not comment_id:
        raise HTTPException(status_code=400, detail="wiki_id, page_id and comment_id are required")
    result = get_wiki_page_comment(api_key, wiki_id, page_id, comment_id)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/comments/update")
async def api_update_wiki_page_comment(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    page_id = body.get("page_id")
    comment_id = body.get("comment_id")
    content = body.get("content")
    if not wiki_id or not page_id or not comment_id or not content:
        raise HTTPException(status_code=400, detail="wiki_id, page_id, comment_id and content are required")
    result = update_wiki_page_comment(api_key, wiki_id, page_id, comment_id, content)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/comments/delete")
async def api_delete_wiki_page_comment(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    page_id = body.get("page_id")
    comment_id = body.get("comment_id")
    if not wiki_id or not page_id or not comment_id:
        raise HTTPException(status_code=400, detail="wiki_id, page_id and comment_id are required")
    result = delete_wiki_page_comment(api_key, wiki_id, page_id, comment_id)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/files/upload")
async def api_upload_wiki_page_file(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    page_id = body.get("page_id")
    file_name = body.get("file_name")
    file_content_base64 = body.get("file_content_base64")

    if not wiki_id or not page_id or not file_name or not file_content_base64:
        raise HTTPException(status_code=400, detail="wiki_id, page_id, file_name and file_content_base64 are required")
    
    try:
        file_content = base64.b64decode(file_content_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 content")

    result = upload_wiki_page_file(api_key, wiki_id, page_id, file_name, file_content)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/files/get")
async def api_get_wiki_page_file(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    page_id = body.get("page_id")
    file_id = body.get("file_id")
    if not wiki_id or not page_id or not file_id:
        raise HTTPException(status_code=400, detail="wiki_id, page_id and file_id are required")
    result = get_wiki_page_file(api_key, wiki_id, page_id, file_id)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/files/delete")
async def api_delete_wiki_page_file(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    page_id = body.get("page_id")
    file_id = body.get("file_id")
    if not wiki_id or not page_id or not file_id:
        raise HTTPException(status_code=400, detail="wiki_id, page_id and file_id are required")
    result = delete_wiki_page_file(api_key, wiki_id, page_id, file_id)
    return _handle_api_call(result)

@app.post("/mcp/wiki/files/upload")
async def api_upload_wiki_file(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    wiki_id = body.get("wiki_id")
    file_name = body.get("file_name")
    file_content_base64 = body.get("file_content_base64")

    if not wiki_id or not file_name or not file_content_base64:
        raise HTTPException(status_code=400, detail="wiki_id, file_name and file_content_base64 are required")
    
    try:
        file_content = base64.b64decode(file_content_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 content")

    result = upload_wiki_file(api_key, wiki_id, file_name, file_content)
    return _handle_api_call(result)

# --- Calendar API ---
@app.post("/mcp/calendar/list")
async def api_get_calendars(request: Request):
    return _handle_api_call_with_auth(request, get_calendars)

@app.post("/mcp/calendar/get")
async def api_get_calendar(request: Request):
    body = await request.json()
    calendar_id = body.get("calendar_id")
    if not calendar_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "calendar_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    return _handle_api_call_with_auth(request, get_calendar, calendar_id)

@app.post("/mcp/calendar/events/create")
async def api_create_calendar_event(request: Request):
    body = await request.json()
    calendar_id = body.get("calendar_id")
    subject = body.get("subject")
    started_at = body.get("started_at")
    ended_at = body.get("ended_at")
    event_body = body.get("body")
    location = body.get("location")
    users = body.get("users")

    if not calendar_id or not subject or not started_at or not ended_at:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "calendar_id, subject, started_at, ended_at 파라미터가 필요합니다.",
            "dooray_response": None
        }

    return _handle_api_call_with_auth(request, create_calendar_event, calendar_id, subject, started_at, ended_at, event_body, location, users)

@app.post("/mcp/calendar/events/list")
async def api_get_calendar_events(request: Request):
    body = await request.json()
    calendar_id = body.get("calendar_id", "*")
    time_min = body.get("time_min")
    time_max = body.get("time_max")
    return _handle_api_call_with_auth(request, get_calendar_events, calendar_id, time_min, time_max)

@app.post("/mcp/calendar/events/get")
async def api_get_calendar_event(request: Request):
    body = await request.json()
    calendar_id = body.get("calendar_id")
    event_id = body.get("event_id")
    if not calendar_id or not event_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "calendar_id와 event_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    return _handle_api_call_with_auth(request, get_calendar_event, calendar_id, event_id)

@app.post("/mcp/calendar/events/update")
async def api_update_calendar_event(request: Request):
    body = await request.json()
    calendar_id = body.get("calendar_id")
    event_id = body.get("event_id")
    subject = body.get("subject")
    started_at = body.get("started_at")
    ended_at = body.get("ended_at")
    event_body = body.get("body")
    location = body.get("location")
    users = body.get("users")

    if not calendar_id or not event_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "calendar_id와 event_id 파라미터가 필요합니다.",
            "dooray_response": None
        }

    if not any([subject, started_at, ended_at, event_body, location, users]):
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "수정할 필드(subject, started_at, ended_at, body, location, users) 중 하나는 제공해야 합니다.",
            "dooray_response": None
        }

    return _handle_api_call_with_auth(request, update_calendar_event, calendar_id, event_id, subject, started_at, ended_at, event_body, location, users)

@app.post("/mcp/calendar/events/delete")
async def api_delete_calendar_event(request: Request):
    body = await request.json()
    calendar_id = body.get("calendar_id")
    event_id = body.get("event_id")
    if not calendar_id or not event_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "calendar_id와 event_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    return _handle_api_call_with_auth(request, delete_calendar_event, calendar_id, event_id)

@app.post("/mcp/calendar/create")
async def api_create_calendar(request: Request):
    body = await request.json()
    name = body.get("name")
    calendar_type = body.get("type", "private")  # private, subscription
    color = body.get("color", "ffffff")
    description = body.get("description")
    calendar_members = body.get("calendar_members")
    notifications_enabled = body.get("notifications_enabled", True)
    
    if not name:
        return _create_error_response("name 파라미터가 필요합니다.", -400)
    
    return _handle_api_call_with_auth(request, create_calendar, name, calendar_type, color, 
                                     description, calendar_members, notifications_enabled)

@app.post("/mcp/calendar/update")
async def api_update_calendar(request: Request):
    body = await request.json()
    calendar_id = body.get("calendar_id")
    name = body.get("name")
    description = body.get("description")
    color = body.get("color")
    
    if not calendar_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "calendar_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    if not any([name, description, color]):
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "수정할 필드(name, description, color) 중 하나는 제공해야 합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, update_calendar, calendar_id, name, description, color)

@app.post("/mcp/calendar/delete")
async def api_delete_calendar(request: Request):
    body = await request.json()
    calendar_id = body.get("calendar_id")
    
    if not calendar_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "calendar_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, delete_calendar, calendar_id)

@app.post("/mcp/calendar/permissions/list")
async def api_get_calendar_permissions(request: Request):
    body = await request.json()
    calendar_id = body.get("calendar_id")
    
    if not calendar_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "calendar_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, get_calendar_permissions, calendar_id)

@app.post("/mcp/calendar/permissions/add")
async def api_add_calendar_permission(request: Request):
    body = await request.json()
    calendar_id = body.get("calendar_id")
    member_id = body.get("member_id")
    role = body.get("role", "reader")  # owner, manager, writer, reader
    
    if not calendar_id or not member_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "calendar_id와 member_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, add_calendar_permission, calendar_id, member_id, role)

@app.post("/mcp/calendar/permissions/remove")
async def api_remove_calendar_permission(request: Request):
    body = await request.json()
    calendar_id = body.get("calendar_id")
    permission_id = body.get("permission_id")
    
    if not calendar_id or not permission_id:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "calendar_id와 permission_id 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, remove_calendar_permission, calendar_id, permission_id)

@app.post("/mcp/calendar/busytime")
async def api_get_busy_time(request: Request):
    body = await request.json()
    member_ids = body.get("member_ids")
    start_time = body.get("start_time")
    end_time = body.get("end_time")
    
    if not member_ids or not start_time or not end_time:
        return {
            "success": False,
            "error_type": "parameter_required",
            "message": "member_ids, start_time, end_time 파라미터가 필요합니다.",
            "dooray_response": None
        }
    
    if not isinstance(member_ids, list):
        return {
            "success": False,
            "error_type": "invalid_parameter",
            "message": "member_ids는 배열 형식이어야 합니다.",
            "dooray_response": None
        }
    
    return _handle_api_call_with_auth(request, get_busy_time, member_ids, start_time, end_time)

# --- Reservation API ---
@app.post("/mcp/reservation/categories/list")
async def api_get_resource_categories(request: Request):
    api_key = _get_api_key(request)
    result = get_resource_categories(api_key)
    return _handle_api_call(result)

@app.post("/mcp/reservation/resources/list")
async def api_get_resources(request: Request):
    api_key = _get_api_key(request)
    result = get_resources(api_key)
    return _handle_api_call(result)

@app.post("/mcp/reservation/resources/get")
async def api_get_resource(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    resource_id = body.get("resource_id")
    if not resource_id:
        raise HTTPException(status_code=400, detail="resource_id is required")
    result = get_resource(api_key, resource_id)
    return _handle_api_call(result)

@app.post("/mcp/reservation/list")
async def api_get_resource_reservations(request: Request):
    api_key = _get_api_key(request)
    result = get_resource_reservations(api_key)
    return _handle_api_call(result)

@app.post("/mcp/reservation/create")
async def api_create_resource_reservation(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    resource_id = body.get("resource_id")
    subject = body.get("subject")
    started_at = body.get("started_at")
    ended_at = body.get("ended_at")
    users = body.get("users")

    if not resource_id or not subject or not started_at or not ended_at:
        raise HTTPException(status_code=400, detail="resource_id, subject, started_at, and ended_at are required")

    result = create_resource_reservation(api_key, resource_id, subject, started_at, ended_at, users)
    return _handle_api_call(result)

@app.post("/mcp/reservation/get")
async def api_get_resource_reservation(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    resource_reservation_id = body.get("resource_reservation_id")
    if not resource_reservation_id:
        raise HTTPException(status_code=400, detail="resource_reservation_id is required")
    result = get_resource_reservation(api_key, resource_reservation_id)
    return _handle_api_call(result)

@app.post("/mcp/reservation/update")
async def api_update_resource_reservation(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    resource_reservation_id = body.get("resource_reservation_id")
    resource_id = body.get("resource_id")
    subject = body.get("subject")
    started_at = body.get("started_at")
    ended_at = body.get("ended_at")
    users = body.get("users")

    if not resource_reservation_id or not any([resource_id, subject, started_at, ended_at, users]):
        raise HTTPException(status_code=400, detail="resource_reservation_id and at least one field to update are required")

    result = update_resource_reservation(api_key, resource_reservation_id, resource_id, subject, started_at, ended_at, users)
    return _handle_api_call(result)

@app.post("/mcp/reservation/delete")
async def api_delete_resource_reservation(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    resource_reservation_id = body.get("resource_reservation_id")
    if not resource_reservation_id:
        raise HTTPException(status_code=400, detail="resource_reservation_id is required")
    result = delete_resource_reservation(api_key, resource_reservation_id)
    return _handle_api_call(result)








# --- Enhanced Messenger API ---
@app.post("/mcp/messenger/channels/list")
async def api_get_messenger_channels(request: Request):
    return _handle_api_call_with_auth(request, get_messenger_channels)

@app.post("/mcp/messenger/channels/create")
async def api_create_messenger_channel(request: Request):
    body = await request.json()
    name = body.get("name")
    members = body.get("members")
    description = body.get("description")
    
    if not name or not members:
        return {"success": False, "error_type": "parameter_required", "message": "name, members 파라미터가 필요합니다.", "dooray_response": None}
    
    return _handle_api_call_with_auth(request, create_messenger_channel, name, members, description)

@app.post("/mcp/messenger/channels/send")
async def api_send_channel_message(request: Request):
    body = await request.json()
    channel_id = body.get("channel_id")
    message = body.get("message")
    attachments = body.get("attachments")
    
    if not channel_id or not message:
        return {"success": False, "error_type": "parameter_required", "message": "channel_id, message 파라미터가 필요합니다.", "dooray_response": None}
    
    return _handle_api_call_with_auth(request, send_channel_message, channel_id, message, attachments)

@app.post("/mcp/messenger/channels/messages/list")
async def api_get_channel_messages(request: Request):
    body = await request.json()
    channel_id = body.get("channel_id")
    limit = body.get("limit", 50)
    
    if not channel_id:
        return {"success": False, "error_type": "parameter_required", "message": "channel_id 파라미터가 필요합니다.", "dooray_response": None}
    
    return _handle_api_call_with_auth(request, get_channel_messages, channel_id, limit)

# --- Enhanced Hook API ---
@app.post("/mcp/hooks/incoming/list")
async def api_get_incoming_hooks(request: Request):
    return _handle_api_call_with_auth(request, get_incoming_hooks)

@app.post("/mcp/hooks/incoming/update")
async def api_update_incoming_hook(request: Request):
    body = await request.json()
    hook_id = body.get("hook_id")
    name = body.get("name")
    url = body.get("url")
    description = body.get("description")
    
    if not hook_id:
        return {"success": False, "error_type": "parameter_required", "message": "hook_id 파라미터가 필요합니다.", "dooray_response": None}
    
    return _handle_api_call_with_auth(request, update_incoming_hook, hook_id, name, url, description)

@app.post("/mcp/hooks/outgoing/create")
async def api_create_outgoing_hook(request: Request):
    body = await request.json()
    name = body.get("name")
    url = body.get("url")
    trigger_word = body.get("trigger_word")
    
    if not name or not url:
        return {"success": False, "error_type": "parameter_required", "message": "name, url 파라미터가 필요합니다.", "dooray_response": None}
    
    return _handle_api_call_with_auth(request, create_outgoing_hook, name, url, trigger_word)

@app.post("/mcp/hooks/outgoing/list")
async def api_get_outgoing_hooks(request: Request):
    return _handle_api_call_with_auth(request, get_outgoing_hooks)

@app.post("/mcp/hooks/outgoing/delete")
async def api_delete_outgoing_hook(request: Request):
    body = await request.json()
    hook_id = body.get("hook_id")
    if not hook_id:
        return {"success": False, "error_type": "parameter_required", "message": "hook_id 파라미터가 필요합니다.", "dooray_response": None}
    return _handle_api_call_with_auth(request, delete_outgoing_hook, hook_id)

@app.get("/schema.json", include_in_schema=False)
async def get_openapi_schema():
    """
    OpenAPI 스키마를 반환 - GPTs 연동용 (우선순위 30개 API만)
    서버 시작 시 미리 생성된 스키마를 반환
    """
    if not app.openapi_schema:
        # 혹시 생성되지 않았다면 fallback으로 생성
        from fastapi.openapi.utils import get_openapi
        
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description="Official Dooray API integration for ChatGPT - Top 30 priority APIs",
            routes=app.routes,
            servers=app.servers
        )
        
        # GPTs 30개 제한을 위한 우선순위 필터링
        filtered_paths = {}
        for path in PRIORITY_PATHS[:30]:  # 최대 30개만
            if path in openapi_schema.get("paths", {}):
                filtered_paths[path] = openapi_schema["paths"][path]
        
        # setAuthToken에 명시적인 requestBody 스키마 추가
        if "/mcp/auth/set_token" in filtered_paths:
            set_token_path = filtered_paths["/mcp/auth/set_token"]
            if "post" in set_token_path:
                set_token_path["post"]["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "token": {
                                        "type": "string",
                                        "description": "Dooray API token"
                                    }
                                },
                                "required": ["token"]
                            },
                            "example": {
                                "token": "your_dooray_api_token_here"
                            }
                        }
                    }
                }
        
        # 드라이브 파일 목록 API 스키마 추가
        if "/mcp/drive/files/list" in filtered_paths:
            drive_files_path = filtered_paths["/mcp/drive/files/list"]
            if "post" in drive_files_path:
                drive_files_path["post"]["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "drive_id": {
                                        "type": "string",
                                        "description": "Drive ID to list files from"
                                    }
                                },
                                "required": ["drive_id"]
                            },
                            "example": {
                                "drive_id": "4025223258147514341"
                            }
                        }
                    }
                }
        
        # 드라이브 파일 다운로드 API 스키마 추가
        if "/mcp/drive/files/download_base64" in filtered_paths:
            download_path = filtered_paths["/mcp/drive/files/download_base64"]
            if "post" in download_path:
                download_path["post"]["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "drive_id": {
                                        "type": "string",
                                        "description": "Drive ID where the file is located"
                                    },
                                    "file_id": {
                                        "type": "string", 
                                        "description": "File ID to download"
                                    },
                                    "media": {
                                        "type": "string",
                                        "description": "Media type for download",
                                        "default": "raw"
                                    }
                                },
                                "required": ["drive_id", "file_id"]
                            },
                            "example": {
                                "drive_id": "4025223258147514341",
                                "file_id": "4139468188722698827",
                                "media": "raw"
                            }
                        }
                    }
                }
        
        # 파일 청크 다운로드 API 스키마 추가
        if "/mcp/drive/files/get_chunk" in filtered_paths:
            chunk_path = filtered_paths["/mcp/drive/files/get_chunk"]
            if "post" in chunk_path:
                chunk_path["post"]["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "chunkSessionId": {
                                        "type": "string",
                                        "description": "Chunk session ID from downloadFile response"
                                    },
                                    "chunkIndex": {
                                        "type": "integer",
                                        "description": "Index of the chunk to download"
                                    }
                                },
                                "required": ["chunkSessionId", "chunkIndex"]
                            },
                            "example": {
                                "chunkSessionId": "session_123",
                                "chunkIndex": 0
                            }
                        }
                    }
                }
        
        # 프로젝트 포스트 생성 API 스키마 추가
        if "/mcp/project/posts/create" in filtered_paths:
            create_post_path = filtered_paths["/mcp/project/posts/create"]
            if "post" in create_post_path:
                create_post_path["post"]["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "project_id": {
                                        "type": "string",
                                        "description": "Project ID to create post in"
                                    },
                                    "subject": {
                                        "type": "string",
                                        "description": "Post subject/title"
                                    },
                                    "body": {
                                        "type": "string",
                                        "description": "Post content/body"
                                    }
                                },
                                "required": ["project_id", "subject", "body"]
                            },
                            "example": {
                                "project_id": "123456789",
                                "subject": "새로운 업무",
                                "body": "업무 내용입니다"
                            }
                        }
                    }
                }
        
        # 위키 페이지 생성 API 스키마 추가
        if "/mcp/wiki/pages/create" in filtered_paths:
            create_wiki_path = filtered_paths["/mcp/wiki/pages/create"]
            if "post" in create_wiki_path:
                create_wiki_path["post"]["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "wiki_id": {
                                        "type": "string",
                                        "description": "Wiki ID to create page in"
                                    },
                                    "subject": {
                                        "type": "string",
                                        "description": "Page title"
                                    },
                                    "body": {
                                        "type": "string",
                                        "description": "Page content"
                                    }
                                },
                                "required": ["wiki_id", "subject", "body"]
                            },
                            "example": {
                                "wiki_id": "123456789",
                                "subject": "새로운 페이지",
                                "body": "페이지 내용입니다"
                            }
                        }
                    }
                }
        
        openapi_schema["paths"] = filtered_paths
        
        # GPTs를 위한 operationId 최적화
        for path, path_item in openapi_schema.get("paths", {}).items():
            for method, operation in path_item.items():
                if isinstance(operation, dict) and "operationId" not in operation:
                    operation_name = operation.get("summary", "").replace(" ", "")
                    if not operation_name:
                        operation_name = f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '')}"
                    operation["operationId"] = operation_name
        
        app.openapi_schema = openapi_schema
    
    return app.openapi_schema