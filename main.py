from fastapi import FastAPI, Request, HTTPException
from dooray_client import (
    # Common API
    get_members,
    get_member,
    # Drive API
    get_drive_list,
    get_drive,
    # Messenger API
    send_message,
    # Project API
    get_projects,
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
    get_wiki_projects,
    get_wiki_pages,
    get_wiki_page,
    create_wiki_page,
    update_wiki_page,
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
    delete_resource_reservation
)

app = FastAPI()

def _handle_api_call(result):
    if "error" in result:
        raise HTTPException(status_code=result.get("status_code", 500), detail=result["error"])
    return {"dooray_response": result}

def _get_api_key(request: Request):
    # ChatGPT는 API Key를 'X-API-Key' 헤더로 보낼 가능성이 높습니다.
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
@app.post("/mcp/wiki/projects/list")
async def api_get_wiki_projects(request: Request):
    api_key = _get_api_key(request)
    result = get_wiki_projects(api_key)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/list")
async def api_get_wiki_pages(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")
    result = get_wiki_pages(api_key, project_id)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/get")
async def api_get_wiki_page(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    page_id = body.get("page_id")
    if not project_id or not page_id:
        raise HTTPException(status_code=400, detail="project_id and page_id are required")
    result = get_wiki_page(api_key, project_id, page_id)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/create")
async def api_create_wiki_page(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    title = body.get("title")
    content = body.get("content")
    parent_page_id = body.get("parent_page_id")

    if not project_id or not title or not content:
        raise HTTPException(status_code=400, detail="project_id, title and content are required")

    result = create_wiki_page(api_key, project_id, title, content, parent_page_id)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/update")
async def api_update_wiki_page(request: Request):
    api_key = _get_api_key(request)
    body = await request.json()
    project_id = body.get("project_id")
    page_id = body.get("page_id")
    title = body.get("title")
    content = body.get("content")

    if not project_id or not page_id or (not title and not content):
        raise HTTPException(status_code=400, detail="project_id, page_id and either title or content are required")

    result = update_wiki_page(api_key, project_id, page_id, title, content)
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
