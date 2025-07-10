import os
import requests
from dotenv import load_dotenv
from config import DOORAY_BASE_URL

load_dotenv()

ACCESS_TOKEN = os.getenv("DOORAY_ACCESS_TOKEN")

def _call_dooray_api(method, endpoint, json_data=None, params=None):
    if not ACCESS_TOKEN:
        return {"error": "DOORAY_ACCESS_TOKEN is not set in .env file"}

    headers = {
        "Authorization": f"dooray-api {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    url = f"{DOORAY_BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json_data, params=params)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=json_data, params=params)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, params=params)
        else:
            return {"error": "Unsupported HTTP method"}

        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
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
def get_members():
    return _call_dooray_api("GET", "/common/v1/members")

def get_member(member_id: str):
    return _call_dooray_api("GET", f"/common/v1/members/{member_id}")

# --- Drive API ---
def get_drive_list(type: str = "private"):
    return _call_dooray_api("GET", "/drive/v1/drives", params={"type": type})

def get_drive(drive_id: str):
    return _call_dooray_api("GET", f"/drive/v1/drives/{drive_id}")

# --- Messenger API (1:1 message) ---
def send_message(recipient_id: str, message: str):
    endpoint = "/messenger/v1/channels/direct-send"
    json_data = {
        "organizationMemberId": recipient_id,
        "text": message
    }
    return _call_dooray_api("POST", endpoint, json_data)

# --- Project API ---
def get_projects():
    return _call_dooray_api("GET", "/project/v1/projects")

def get_project_posts(project_id: str):
    return _call_dooray_api("GET", f"/project/v1/projects/{project_id}/posts")

def get_project_post(project_id: str, post_id: str):
    return _call_dooray_api("GET", f"/project/v1/projects/{project_id}/posts/{post_id}")

def create_project_post(project_id: str, subject: str, body: str, post_type: str = "task"):
    json_data = {
        "subject": subject,
        "body": {"mimeType": "text/x-markdown", "content": body},
        "postType": post_type
    }
    return _call_dooray_api("POST", f"/project/v1/projects/{project_id}/posts", json_data)

def update_project_post(project_id: str, post_id: str, subject: str = None, body: str = None):
    json_data = {}
    if subject: json_data["subject"] = subject
    if body: json_data["body"] = {"mimeType": "text/x-markdown", "content": body}
    return _call_dooray_api("PUT", f"/project/v1/projects/{project_id}/posts/{post_id}", json_data)

def update_project_post_workflow(project_id: str, post_id: str, workflow_id: str):
    json_data = {"workflowId": workflow_id}
    return _call_dooray_api("PUT", f"/project/v1/projects/{project_id}/posts/{post_id}/workflow", json_data)

def set_project_post_done(project_id: str, post_id: str):
    return _call_dooray_api("PUT", f"/project/v1/projects/{project_id}/posts/{post_id}/done")

def create_project_post_comment(project_id: str, post_id: str, content: str):
    json_data = {"content": {"mimeType": "text/x-markdown", "content": content}}
    return _call_dooray_api("POST", f"/project/v1/projects/{project_id}/posts/{post_id}/comments", json_data)

def get_project_post_comments(project_id: str, post_id: str):
    return _call_dooray_api("GET", f"/project/v1/projects/{project_id}/posts/{post_id}/comments")

def update_project_post_comment(project_id: str, post_id: str, comment_id: str, content: str):
    json_data = {"content": {"mimeType": "text/x-markdown", "content": content}}
    return _call_dooray_api("PUT", f"/project/v1/projects/{project_id}/posts/{post_id}/comments/{comment_id}", json_data)

def delete_project_post_comment(project_id: str, post_id: str, comment_id: str):
    return _call_dooray_api("DELETE", f"/project/v1/projects/{project_id}/posts/{post_id}/comments/{comment_id}")

# --- Wiki API ---
def get_wiki_projects():
    return _call_dooray_api("GET", "/wiki/v1/projects")

def get_wiki_pages(project_id: str):
    return _call_dooray_api("GET", f"/wiki/v1/projects/{project_id}/pages")

def get_wiki_page(project_id: str, page_id: str):
    return _call_dooray_api("GET", f"/wiki/v1/projects/{project_id}/pages/{page_id}")

def create_wiki_page(project_id: str, title: str, content: str, parent_page_id: str = None):
    json_data = {
        "title": title,
        "content": {"mimeType": "text/x-markdown", "content": content}
    }
    if parent_page_id: json_data["parentPageId"] = parent_page_id
    return _call_dooray_api("POST", f"/wiki/v1/projects/{project_id}/pages", json_data)

def update_wiki_page(project_id: str, page_id: str, title: str = None, content: str = None):
    json_data = {}
    if title: json_data["title"] = title
    if content: json_data["content"] = {"mimeType": "text/x-markdown", "content": content}
    return _call_dooray_api("PUT", f"/wiki/v1/projects/{project_id}/pages/{page_id}", json_data)

# --- Calendar API ---
def get_calendars():
    return _call_dooray_api("GET", "/calendar/v1/calendars")

def get_calendar(calendar_id: str):
    return _call_dooray_api("GET", f"/calendar/v1/calendars/{calendar_id}")

def create_calendar_event(calendar_id: str, subject: str, started_at: str, ended_at: str, body: str = None, location: str = None, users: list = None):
    json_data = {
        "subject": subject,
        "startedAt": started_at,
        "endedAt": ended_at,
        "wholeDayFlag": False,
        "users": users if users else []
    }
    if body: json_data["body"] = {"mimeType": "text/x-markdown", "content": body}
    if location: json_data["location"] = location
    return _call_dooray_api("POST", f"/calendar/v1/calendars/{calendar_id}/events", json_data)

def get_calendar_events(calendar_id: str = "*", time_min: str = None, time_max: str = None):
    params = {}
    if time_min: params["timeMin"] = time_min
    if time_max: params["timeMax"] = time_max
    return _call_dooray_api("GET", f"/calendar/v1/calendars/{calendar_id}/events", params=params)

def get_calendar_event(calendar_id: str, event_id: str):
    return _call_dooray_api("GET", f"/calendar/v1/calendars/{calendar_id}/events/{event_id}")

def update_calendar_event(calendar_id: str, event_id: str, subject: str = None, started_at: str = None, ended_at: str = None, body: str = None, location: str = None, users: list = None):
    json_data = {}
    if subject: json_data["subject"] = subject
    if started_at: json_data["startedAt"] = started_at
    if ended_at: json_data["endedAt"] = ended_at
    if body: json_data["body"] = {"mimeType": "text/x-markdown", "content": body}
    if location: json_data["location"] = location
    if users: json_data["users"] = users
    return _call_dooray_api("PUT", f"/calendar/v1/calendars/{calendar_id}/events/{event_id}", json_data)

def delete_calendar_event(calendar_id: str, event_id: str):
    return _call_dooray_api("POST", f"/calendar/v1/calendars/{calendar_id}/events/{event_id}/delete")

# --- Reservation API ---
def get_resource_categories():
    return _call_dooray_api("GET", "/reservation/v1/resource-categories")

def get_resources():
    return _call_dooray_api("GET", "/reservation/v1/resources")

def get_resource(resource_id: str):
    return _call_dooray_api("GET", f"/reservation/v1/resources/{resource_id}")

def get_resource_reservations():
    return _call_dooray_api("GET", "/reservation/v1/resource-reservations")

def create_resource_reservation(resource_id: str, subject: str, started_at: str, ended_at: str, users: list = None):
    json_data = {
        "resourceId": resource_id,
        "subject": subject,
        "startedAt": started_at,
        "endedAt": ended_at,
        "users": users if users else []
    }
    return _call_dooray_api("POST", "/reservation/v1/resource-reservations", json_data)

def get_resource_reservation(resource_reservation_id: str):
    return _call_dooray_api("GET", f"/reservation/v1/resource-reservations/{resource_reservation_id}")

def update_resource_reservation(resource_reservation_id: str, resource_id: str = None, subject: str = None, started_at: str = None, ended_at: str = None, users: list = None):
    json_data = {}
    if resource_id: json_data["resourceId"] = resource_id
    if subject: json_data["subject"] = subject
    if started_at: json_data["startedAt"] = started_at
    if ended_at: json_data["endedAt"] = ended_at
    if users: json_data["users"] = users
    return _call_dooray_api("PUT", f"/reservation/v1/resource-reservations/{resource_reservation_id}", json_data)

def delete_resource_reservation(resource_reservation_id: str):
    return _call_dooray_api("DELETE", f"/reservation/v1/resource-reservations/{resource_reservation_id}")