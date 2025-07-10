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

# --- Common API ---
@app.post("/mcp/common/members/list")
async def api_get_members():
    result = get_members()
    return _handle_api_call(result)

@app.post("/mcp/common/members/get")
async def api_get_member(req: Request):
    body = await req.json()
    member_id = body.get("member_id")
    if not member_id:
        raise HTTPException(status_code=400, detail="member_id is required")
    result = get_member(member_id)
    return _handle_api_call(result)

# --- Drive API ---
@app.post("/mcp/drive/list")
async def api_get_drive_list(req: Request):
    body = await req.json()
    drive_type = body.get("type", "private")
    result = get_drive_list(drive_type)
    return _handle_api_call(result)

@app.post("/mcp/drive/get")
async def api_get_drive(req: Request):
    body = await req.json()
    drive_id = body.get("drive_id")
    if not drive_id:
        raise HTTPException(status_code=400, detail="drive_id is required")
    result = get_drive(drive_id)
    return _handle_api_call(result)

# --- Messenger API ---
@app.post("/mcp/messenger/send")
async def api_send_message(req: Request):
    body = await req.json()
    recipient_id = body.get("recipient_id")
    message = body.get("message")

    if not recipient_id or not message:
        raise HTTPException(status_code=400, detail="recipient_id and message are required")

    result = send_message(recipient_id, message)
    return _handle_api_call(result)

# --- Project API ---
@app.post("/mcp/project/list")
async def api_get_projects():
    result = get_projects()
    return _handle_api_call(result)

@app.post("/mcp/project/posts/list")
async def api_get_project_posts(req: Request):
    body = await req.json()
    project_id = body.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")
    result = get_project_posts(project_id)
    return _handle_api_call(result)

@app.post("/mcp/project/posts/get")
async def api_get_project_post(req: Request):
    body = await req.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    if not project_id or not post_id:
        raise HTTPException(status_code=400, detail="project_id and post_id are required")
    result = get_project_post(project_id, post_id)
    return _handle_api_call(result)

@app.post("/mcp/project/posts/create")
async def api_create_project_post(req: Request):
    body = await req.json()
    project_id = body.get("project_id")
    subject = body.get("subject")
    post_body = body.get("body", "")
    post_type = body.get("post_type", "task")

    if not project_id or not subject:
        raise HTTPException(status_code=400, detail="project_id and subject are required")

    result = create_project_post(project_id, subject, post_body, post_type)
    return _handle_api_call(result)

@app.post("/mcp/project/posts/update")
async def api_update_project_post(req: Request):
    body = await req.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    subject = body.get("subject")
    post_body = body.get("body")

    if not project_id or not post_id or (not subject and not post_body):
        raise HTTPException(status_code=400, detail="project_id, post_id and either subject or body are required")

    result = update_project_post(project_id, post_id, subject, post_body)
    return _handle_api_call(result)

@app.post("/mcp/project/posts/update_workflow")
async def api_update_project_post_workflow(req: Request):
    body = await req.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    workflow_id = body.get("workflow_id")

    if not project_id or not post_id or not workflow_id:
        raise HTTPException(status_code=400, detail="project_id, post_id and workflow_id are required")

    result = update_project_post_workflow(project_id, post_id, workflow_id)
    return _handle_api_call(result)

@app.post("/mcp/project/posts/set_done")
async def api_set_project_post_done(req: Request):
    body = await req.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")

    if not project_id or not post_id:
        raise HTTPException(status_code=400, detail="project_id and post_id are required")

    result = set_project_post_done(project_id, post_id)
    return _handle_api_call(result)

@app.post("/mcp/project/comments/create")
async def api_create_project_post_comment(req: Request):
    body = await req.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    content = body.get("content")

    if not project_id or not post_id or not content:
        raise HTTPException(status_code=400, detail="project_id, post_id and content are required")

    result = create_project_post_comment(project_id, post_id, content)
    return _handle_api_call(result)

@app.post("/mcp/project/comments/list")
async def api_get_project_post_comments(req: Request):
    body = await req.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")

    if not project_id or not post_id:
        raise HTTPException(status_code=400, detail="project_id and post_id are required")

    result = get_project_post_comments(project_id, post_id)
    return _handle_api_call(result)

@app.post("/mcp/project/comments/update")
async def api_update_project_post_comment(req: Request):
    body = await req.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    comment_id = body.get("comment_id")
    content = body.get("content")

    if not project_id or not post_id or not comment_id or not content:
        raise HTTPException(status_code=400, detail="project_id, post_id, comment_id and content are required")

    result = update_project_post_comment(project_id, post_id, comment_id, content)
    return _handle_api_call(result)

@app.post("/mcp/project/comments/delete")
async def api_delete_project_post_comment(req: Request):
    body = await req.json()
    project_id = body.get("project_id")
    post_id = body.get("post_id")
    comment_id = body.get("comment_id")

    if not project_id or not post_id or not comment_id:
        raise HTTPException(status_code=400, detail="project_id, post_id and comment_id are required")

    result = delete_project_post_comment(project_id, post_id, comment_id)
    return _handle_api_call(result)

# --- Wiki API ---
@app.post("/mcp/wiki/projects/list")
async def api_get_wiki_projects():
    result = get_wiki_projects()
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/list")
async def api_get_wiki_pages(req: Request):
    body = await req.json()
    project_id = body.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")
    result = get_wiki_pages(project_id)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/get")
async def api_get_wiki_page(req: Request):
    body = await req.json()
    project_id = body.get("project_id")
    page_id = body.get("page_id")
    if not project_id or not page_id:
        raise HTTPException(status_code=400, detail="project_id and page_id are required")
    result = get_wiki_page(project_id, page_id)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/create")
async def api_create_wiki_page(req: Request):
    body = await req.json()
    project_id = body.get("project_id")
    title = body.get("title")
    content = body.get("content")
    parent_page_id = body.get("parent_page_id")

    if not project_id or not title or not content:
        raise HTTPException(status_code=400, detail="project_id, title and content are required")

    result = create_wiki_page(project_id, title, content, parent_page_id)
    return _handle_api_call(result)

@app.post("/mcp/wiki/pages/update")
async def api_update_wiki_page(req: Request):
    body = await req.json()
    project_id = body.get("project_id")
    page_id = body.get("page_id")
    title = body.get("title")
    content = body.get("content")

    if not project_id or not page_id or (not title and not content):
        raise HTTPException(status_code=400, detail="project_id, page_id and either title or content are required")

    result = update_wiki_page(project_id, page_id, title, content)
    return _handle_api_call(result)

# --- Calendar API ---
@app.post("/mcp/calendar/list")
async def api_get_calendars():
    result = get_calendars()
    return _handle_api_call(result)

@app.post("/mcp/calendar/get")
async def api_get_calendar(req: Request):
    body = await req.json()
    calendar_id = body.get("calendar_id")
    if not calendar_id:
        raise HTTPException(status_code=400, detail="calendar_id is required")
    result = get_calendar(calendar_id)
    return _handle_api_call(result)

@app.post("/mcp/calendar/events/create")
async def api_create_calendar_event(req: Request):
    body = await req.json()
    calendar_id = body.get("calendar_id")
    subject = body.get("subject")
    started_at = body.get("started_at")
    ended_at = body.get("ended_at")
    event_body = body.get("body")
    location = body.get("location")
    users = body.get("users")

    if not calendar_id or not subject or not started_at or not ended_at:
        raise HTTPException(status_code=400, detail="calendar_id, subject, started_at, and ended_at are required")

    result = create_calendar_event(calendar_id, subject, started_at, ended_at, event_body, location, users)
    return _handle_api_call(result)

@app.post("/mcp/calendar/events/list")
async def api_get_calendar_events(req: Request):
    body = await req.json()
    calendar_id = body.get("calendar_id", "*")
    time_min = body.get("time_min")
    time_max = body.get("time_max")
    result = get_calendar_events(calendar_id, time_min, time_max)
    return _handle_api_call(result)

@app.post("/mcp/calendar/events/get")
async def api_get_calendar_event(req: Request):
    body = await req.json()
    calendar_id = body.get("calendar_id")
    event_id = body.get("event_id")
    if not calendar_id or not event_id:
        raise HTTPException(status_code=400, detail="calendar_id and event_id are required")
    result = get_calendar_event(calendar_id, event_id)
    return _handle_api_call(result)

@app.post("/mcp/calendar/events/update")
async def api_update_calendar_event(req: Request):
    body = await req.json()
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

    result = update_calendar_event(calendar_id, event_id, subject, started_at, ended_at, event_body, location, users)
    return _handle_api_call(result)

@app.post("/mcp/calendar/events/delete")
async def api_delete_calendar_event(req: Request):
    body = await req.json()
    calendar_id = body.get("calendar_id")
    event_id = body.get("event_id")
    if not calendar_id or not event_id:
        raise HTTPException(status_code=400, detail="calendar_id and event_id are required")
    result = delete_calendar_event(calendar_id, event_id)
    return _handle_api_call(result)

# --- Reservation API ---
@app.post("/mcp/reservation/categories/list")
async def api_get_resource_categories():
    result = get_resource_categories()
    return _handle_api_call(result)

@app.post("/mcp/reservation/resources/list")
async def api_get_resources():
    result = get_resources()
    return _handle_api_call(result)

@app.post("/mcp/reservation/resources/get")
async def api_get_resource(req: Request):
    body = await req.json()
    resource_id = body.get("resource_id")
    if not resource_id:
        raise HTTPException(status_code=400, detail="resource_id is required")
    result = get_resource(resource_id)
    return _handle_api_call(result)

@app.post("/mcp/reservation/list")
async def api_get_resource_reservations():
    result = get_resource_reservations()
    return _handle_api_call(result)

@app.post("/mcp/reservation/create")
async def api_create_resource_reservation(req: Request):
    body = await req.json()
    resource_id = body.get("resource_id")
    subject = body.get("subject")
    started_at = body.get("started_at")
    ended_at = body.get("ended_at")
    users = body.get("users")

    if not resource_id or not subject or not started_at or not ended_at:
        raise HTTPException(status_code=400, detail="resource_id, subject, started_at, and ended_at are required")

    result = create_resource_reservation(resource_id, subject, started_at, ended_at, users)
    return _handle_api_call(result)

@app.post("/mcp/reservation/get")
async def api_get_resource_reservation(req: Request):
    body = await req.json()
    resource_reservation_id = body.get("resource_reservation_id")
    if not resource_reservation_id:
        raise HTTPException(status_code=400, detail="resource_reservation_id is required")
    result = get_resource_reservation(resource_reservation_id)
    return _handle_api_call(result)

@app.post("/mcp/reservation/update")
async def api_update_resource_reservation(req: Request):
    body = await req.json()
    resource_reservation_id = body.get("resource_reservation_id")
    resource_id = body.get("resource_id")
    subject = body.get("subject")
    started_at = body.get("started_at")
    ended_at = body.get("ended_at")
    users = body.get("users")

    if not resource_reservation_id or not any([resource_id, subject, started_at, ended_at, users]):
        raise HTTPException(status_code=400, detail="resource_reservation_id and at least one field to update are required")

    result = update_resource_reservation(resource_reservation_id, resource_id, subject, started_at, ended_at, users)
    return _handle_api_call(result)

@app.post("/mcp/reservation/delete")
async def api_delete_resource_reservation(req: Request):
    body = await req.json()
    resource_reservation_id = body.get("resource_reservation_id")
    if not resource_reservation_id:
        raise HTTPException(status_code=400, detail="resource_reservation_id is required")
    result = delete_resource_reservation(resource_reservation_id)
    return _handle_api_call(result)