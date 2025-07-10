from fastapi import FastAPI, Request, HTTPException, Response
import base64 # Import base64 for file handling
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
    download_drive_file,
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
    # Reservation API
    get_resource_categories,
    get_resources,
    get_resource,
    get_resource_reservations,
    create_resource_reservation,
    get_resource_reservation,
    update_resource_reservation,
    delete_resource_reservation,
    # Organization Chart API
    get_organization_chart,
    get_department_details,
    get_user_details,
    # Account Synchronization API
    sync_users,
    sync_departments,
    delete_sync_user,
    delete_sync_department
)

app = FastAPI()

def _handle_api_call(result):
    if "error" in result:
        raise HTTPException(status_code=result.get("status_code", 500), detail=result["error"])
    return {"dooray_response": result}

def _get_api_key(request: Request):
    # ChatGPT는 API Key를 'X-API-Key' 헤더로 보낼 가능성이 높습니다。
    # 또는 'Authorization' 헤더에 'Bearer <API_KEY>' 형태로 보낼 수도 있습니다.
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        # 'Authorization: Bearer <API_KEY>' 형태도 고려
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            api_key = auth_header.split(" ")[1]
    
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key is missing or invalid")
    return api_key

# --- Common API ---
@app.post("/mcp/common/members/list")
async def api_get_members(request: Request):
    api_key = _get_api_key(request)
    result = get_members(api_key)
    return _handle_api_call(result)

@app.post("/mcp/common/members/get")
async def api_get_member(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    member_id = body.get("member_id")
    if not member_id:
        raise HTTPException(status_code=400, detail="member_id is required")
    result = get_member(api_key, member_id)
    return _handle_api_call(result)

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
    api_key = _get_api_key(request)
    body = await request.json()
    drive_type = body.get("type", "private")
    result = get_drive_list(api_key, drive_type)
    return _handle_api_call(result)

@app.post("/mcp/drive/get")
async def api_get_drive(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    drive_id = body.get("drive_id")
    if not drive_id:
        raise HTTPException(status_code=400, detail="drive_id is required")
    result = get_drive(api_key, drive_id)
    return _handle_api_call(result)

@app.post("/mcp/drive/files/list")
async def api_get_drive_files(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    drive_id = body.get("drive_id")
    if not drive_id:
        raise HTTPException(status_code=400, detail="drive_id is required")
    result = get_drive_files(api_key, drive_id)
    return _handle_api_call(result)

@app.post("/mcp/drive/files/metadata")
async def api_get_drive_file_metadata(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    drive_id = body.get("drive_id")
    file_id = body.get("file_id")
    if not drive_id or not file_id:
        raise HTTPException(status_code=400, detail="drive_id and file_id are required")
    result = get_drive_file_metadata(api_key, drive_id, file_id)
    return _handle_api_call(result)

@app.post("/mcp/drive/files/download")
async def api_download_drive_file(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    drive_id = body.get("drive_id")
    file_id = body.get("file_id")
    if not drive_id or not file_id:
        raise HTTPException(status_code=400, detail="drive_id and file_id are required")
    
    file_content = download_drive_file(api_key, drive_id, file_id)
    
    if isinstance(file_content, dict) and "error" in file_content:
        raise HTTPException(status_code=file_content.get("status_code", 500), detail=file_content["error"])
    
    # Assuming the file content is binary, return it as a stream or appropriate media type
    # You might want to add content-type detection based on file metadata if available
    return Response(content=file_content, media_type="application/octet-stream")

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
    api_key = _get_api_key(request)
    result = get_projects(api_key)
    return _handle_api_call(result)

@app.post("/mcp/project/create")
async def api_create_project(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    name = body.get("name")
    code = body.get("code")
    description = body.get("description")

    if not name or not code:
        raise HTTPException(status_code=400, detail="name and code are required")

    result = create_project(api_key, name, code, description)
    return _handle_api_call(result)

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

    result = delete_project_post_comment(api_key, project_id, comment_id)
    return _handle_api_call(result)

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
    api_key = _get_api_key(request)
    result = get_calendars(api_key)
    return _handle_api_call(result)

@app.post("/mcp/calendar/get")
async def api_get_calendar(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    calendar_id = body.get("calendar_id")
    if not calendar_id:
        raise HTTPException(status_code=400, detail="calendar_id is required")
    result = get_calendar(api_key, calendar_id)
    return _handle_api_call(result)

@app.post("/mcp/calendar/events/create")
async def api_create_calendar_event(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    calendar_id = body.get("calendar_id")
    subject = body.get("subject")
    started_at = body.get("started_at")
    ended_at = body.get("ended_at")
    event_body = body.get("body")
    location = body.get("location")
    users = body.get("users")

    if not calendar_id or not subject or not started_at or not ended_at:
        raise HTTPException(status_code=400, detail="calendar_id, subject, started_at, and ended_at are required")

    result = create_calendar_event(api_key, calendar_id, subject, started_at, ended_at, event_body, location, users)
    return _handle_api_call(result)

@app.post("/mcp/calendar/events/list")
async def api_get_calendar_events(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    calendar_id = body.get("calendar_id", "*")
    time_min = body.get("time_min")
    time_max = body.get("time_max")
    result = get_calendar_events(api_key, calendar_id, time_min, time_max)
    return _handle_api_call(result)

@app.post("/mcp/calendar/events/get")
async def api_get_calendar_event(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    calendar_id = body.get("calendar_id")
    event_id = body.get("event_id")
    if not calendar_id or not event_id:
        raise HTTPException(status_code=400, detail="calendar_id and event_id are required")
    result = get_calendar_event(api_key, calendar_id, event_id)
    return _handle_api_call(result)

@app.post("/mcp/calendar/events/update")
async def api_update_calendar_event(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    calendar_id = body.get("calendar_id")
    event_id = body.get("event_id")
    subject = body.get("subject")
    started_at = body.get("started_at")
    ended_at = body.get("ended_at")
    event_body = body.get("body")
    location = body.get("location")
    users = body.get("users")

    if not calendar_id or not event_id or not any([subject, started_at, ended_at, event_body, location, users]):
        raise HTTPException(status_code=400, detail="calendar_id, event_id and at least one field to update are required")

    result = update_calendar_event(api_key, calendar_id, event_id, subject, started_at, ended_at, event_body, location, users)
    return _handle_api_call(result)

@app.post("/mcp/calendar/events/delete")
async def api_delete_calendar_event(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    calendar_id = body.get("calendar_id")
    event_id = body.get("event_id")
    if not calendar_id or not event_id:
        raise HTTPException(status_code=400, detail="calendar_id and event_id are required")
    result = delete_calendar_event(api_key, calendar_id, event_id)
    return _handle_api_call(result)

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

# --- Organization Chart API ---
@app.post("/mcp/organization_chart/list")
async def api_get_organization_chart(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    include_inactive = body.get("include_inactive", False)
    result = get_organization_chart(api_key, include_inactive)
    return _handle_api_call(result)

@app.post("/mcp/organization_chart/departments/get")
async def api_get_department_details(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    department_id = body.get("department_id")
    if not department_id:
        raise HTTPException(status_code=400, detail="department_id is required")
    result = get_department_details(api_key, department_id)
    return _handle_api_call(result)

@app.post("/mcp/organization_chart/users/get")
async def api_get_user_details(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    result = get_user_details(api_key, user_id)
    return _handle_api_call(result)

# --- Account Synchronization API ---
@app.post("/mcp/account_sync/users/sync")
async def api_sync_users(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    users = body.get("users")
    if not users or not isinstance(users, list):
        raise HTTPException(status_code=400, detail="users (list) is required")
    result = sync_users(api_key, users)
    return _handle_api_call(result)

@app.post("/mcp/account_sync/departments/sync")
async def api_sync_departments(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    departments = body.get("departments")
    if not departments or not isinstance(departments, list):
        raise HTTPException(status_code=400, detail="departments (list) is required")
    result = sync_departments(api_key, departments)
    return _handle_api_call(result)

@app.post("/mcp/account_sync/users/delete")
async def api_delete_sync_user(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    result = delete_sync_user(api_key, user_id)
    return _handle_api_call(result)

@app.post("/mcp/account_sync/departments/delete")
async def api_delete_sync_department(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    department_id = body.get("department_id")
    if not department_id:
        raise HTTPException(status_code=400, detail="department_id is required")
    result = delete_sync_department(api_key, department_id)
    return _handle_api_call(result)
