import os
import requests
from dotenv import load_dotenv
from config import DOORAY_BASE_URL

load_dotenv()

def _call_dooray_api(access_token: str, method, endpoint, json_data=None, params=None, files=None):
    headers = {
        "Authorization": f"dooray-api {access_token}"
    }
    if files is None: # Only set Content-Type for non-file uploads
        headers["Content-Type"] = "application/json"

    url = f"{DOORAY_BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json_data, params=params, files=files)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=json_data, params=params, files=files)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, params=params)
        else:
            return {"error": "Unsupported HTTP method"}

        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        # For file downloads, return raw content
        if params and params.get("media") == "raw":
            return response.content

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
    return _call_dooray_api(access_token, "GET", "/common/v1/members")

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
def get_drive_list(access_token: str, type: str = "private"):
    return _call_dooray_api(access_token, "GET", "/drive/v1/drives", params={"type": type})

def get_drive(access_token: str, drive_id: str):
    return _call_dooray_api(access_token, "GET", f"/drive/v1/drives/{drive_id}")

def get_drive_files(access_token: str, drive_id: str):
    return _call_dooray_api(access_token, "GET", f"/drive/v1/drives/{drive_id}/files")

def get_drive_file_metadata(access_token: str, drive_id: str, file_id: str):
    return _call_dooray_api(access_token, "GET", f"/drive/v1/drives/{drive_id}/files/{file_id}", params={"media": "meta"})

def download_drive_file(access_token: str, drive_id: str, file_id: str):
    return _call_dooray_api(access_token, "GET", f"/drive/v1/drives/{drive_id}/files/{file_id}", params={"media": "raw"})

# --- Messenger API (1:1 message) ---
def send_message(access_token: str, recipient_id: str, message: str):
    endpoint = "/messenger/v1/channels/direct-send"
    json_data = {
        "organizationMemberId": recipient_id,
        "text": message
    }
    return _call_dooray_api(access_token, "POST", endpoint, json_data)

# --- Project API ---
def get_projects(access_token: str):
    return _call_dooray_api(access_token, "GET", "/project/v1/projects")

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

def update_project_post_comment(access_token: str, project_id: str, post_id: str, comment_id: str, content: str):
    json_data = {"content": {"mimeType": "text/x-markdown", "content": content}}
    return _call_dooray_api(access_token, "PUT", f"/project/v1/projects/{project_id}/posts/{post_id}/comments/{comment_id}", json_data)

def delete_project_post_comment(access_token: str, project_id: str, post_id: str, comment_id: str):
    return _call_dooray_api(access_token, "DELETE", f"/project/v1/projects/{project_id}/posts/{post_id}/comments/{comment_id}")

# --- Wiki API ---
def get_wikis(access_token: str):
    return _call_dooray_api(access_token, "GET", "/wiki/v1/wikis")

def get_wiki_pages(access_token: str, wiki_id: str):
    return _call_dooray_api(access_token, "GET", f"/wiki/v1/wikis/{wiki_id}/pages")

def get_wiki_page(access_token: str, wiki_id: str, page_id: str):
    return _call_dooray_api(access_token, "GET", f"/wiki/v1/wikis/{wiki_id}/pages/{page_id}")

def create_wiki_page(access_token: str, wiki_id: str, title: str, content: str, parent_page_id: str = None):
    json_data = {
        "title": title,
        "content": {"mimeType": "text/x-markdown", "content": content}
    }
    if parent_page_id: json_data["parentPageId"] = parent_page_id
    return _call_dooray_api(access_token, "POST", f"/wiki/v1/wikis/{wiki_id}/pages", json_data)

def update_wiki_page(access_token: str, wiki_id: str, page_id: str, title: str = None, content: str = None):
    json_data = {}
    if title: json_data["title"] = title
    if content: json_data["content"] = {"mimeType": "text/x-markdown", "content": content}
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

# --- Organization Chart API ---
def get_organization_chart(access_token: str, include_inactive: bool = False):
    params = {"include_inactive": include_inactive}
    return _call_dooray_api(access_token, "GET", "/organization-chart", params=params)

def get_department_details(access_token: str, department_id: str):
    return _call_dooray_api(access_token, "GET", f"/organization-chart/departments/{department_id}")

def get_user_details(access_token: str, user_id: str):
    return _call_dooray_api(access_token, "GET", f"/organization-chart/users/{user_id}")

# --- Account Synchronization API ---
def sync_users(access_token: str, users: list):
    json_data = users
    return _call_dooray_api(access_token, "POST", "/account-sync/users", json_data)

def sync_departments(access_token: str, departments: list):
    json_data = departments
    return _call_dooray_api(access_token, "POST", "/account-sync/departments", json_data)

def delete_sync_user(access_token: str, user_id: str):
    return _call_dooray_api(access_token, "DELETE", f"/account-sync/users/{user_id}")

def delete_sync_department(access_token: str, department_id: str):
    return _call_dooray_api(access_token, "DELETE", f"/account-sync/departments/{department_id}")
