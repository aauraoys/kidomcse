import asyncio
import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from datetime import datetime, timezone
import json
from dotenv import load_dotenv
from main import SESSION_TOKENS

load_dotenv(dotenv_path=".env")

from dooray_client import get_projects as dooray_get_projects, create_project_post as dooray_create_task, get_project_members as dooray_get_members, get_project_tags as dooray_get_tags, get_drive_list as dooray_get_drive_list, get_drive_files as dooray_get_drive_files

# MCP Router
router = APIRouter()

# --- MCP Standard Methods ---

async def handle_initialize(request_id):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2025-03-26",
            "serverInfo": {
                "name": "kic-dooray-mcp",
                "version": "0.1.0"
            },
            "capabilities": {
                "tools": {},
                "prompts": {},
                "resources": {},
                "sampling": {}
            }
        }
    }

async def handle_ping(request_id):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "ok": True,
            "ts": datetime.now(timezone.utc).isoformat()
        }
    }

async def handle_tools_list(request_id):
    tools = [
        {
            "name": "dooray_createTask",
            "description": "Create a Dooray task",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "projectId": {"type": "string", "description": "The ID of the project."},
                    "title": {"type": "string", "description": "The title of the task."},
                    "description": {"type": "string", "description": "The description of the task."},
                    "assignees": {"type": "array", "items": {"type": "string"}},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "dueDate": {"type": "string", "format": "date", "description": "The due date of the task."}
                },
                "required": ["projectId", "title"]
            }
        },
        {
            "name": "dooray_getProjects",
            "description": "Get a list of Dooray projects",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "cursor": {"type": "string"},
                    "limit": {"type": "integer", "default": 50}
                }
            }
        },
        {
            "name": "dooray_getMembers",
            "description": "Get a list of members in a project",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "projectId": {"type": "string"}
                },
                "required": ["projectId"]
            }
        },
        {
            "name": "dooray_getTags",
            "description": "Get a list of tags in a project",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "projectId": {"type": "string"}
                },
                "required": ["projectId"]
            }
        },
        {
            "name": "dooray_getDriveList",
            "description": "Get a list of Dooray drives",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Drive type (private or team)", "default": "private"}
                }
            }
        },
        {
            "name": "dooray_getDriveFiles",
            "description": "Get files from a Dooray drive",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "driveId": {"type": "string", "description": "The ID of the drive"}
                },
                "required": ["driveId"]
            }
        }
    ]
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"tools": tools}
    }

async def handle_tools_call(request_id, params, request: Request):
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    # Get API token
    conversation_id = request.headers.get("claude-conversation-id") or request.headers.get("X-Conversation-ID")
    if conversation_id:
        token = SESSION_TOKENS.get(conversation_id)
        if not token:
            return {
                "jsonrpc": "2.0", "id": request_id,
                "error": {"code": 401, "message": "Unauthorized", "data": "API token is not set for this session. Please use '/mcp/auth/set_token' to set the token first."}
            }
        
    else:
        token = os.getenv("DOORAY_API_TOKEN")
        if not token:
            return {
                "jsonrpc": "2.0", "id": request_id,
                "error": {"code": 401, "message": "Unauthorized", "data": "API token is missing. Either set DOORAY_API_TOKEN environment variable or use session-based authentication."}
            }

    try:
        if tool_name == "dooray_getProjects":
            result = dooray_get_projects(
                access_token=token,
                limit=arguments.get("limit", 50),
                cursor=arguments.get("cursor")
            )
            if "error" in result:
                raise Exception(result.get("response", result.get("error")))
            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": str(result)}]}}
        
        elif tool_name == "dooray_createTask":
            result = dooray_create_task(
                access_token=token,
                project_id=arguments.get("projectId"),
                subject=arguments.get("title"),
                body=arguments.get("description", "")
            )
            if "error" in result:
                raise Exception(result.get("response", result.get("error")))
            
            task_id = result.get("id")
            # This is a placeholder for the URL, as the API doesn't return it directly.
            url = f"https://{os.getenv('DOORAY_DOMAIN')}/projects/{arguments.get('projectId')}/{task_id}"

            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": f"Task created successfully. ID: {task_id}, URL: {url}"}]}}

        elif tool_name == "dooray_getMembers":
            result = dooray_get_members(
                access_token=token,
                project_id=arguments.get("projectId")
            )
            if "error" in result:
                raise Exception(result.get("response", result.get("error")))
            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": str(result)}]}}

        elif tool_name == "dooray_getTags":
            result = dooray_get_tags(access_token=token, project_id=arguments.get("projectId"))
            if "error" in result:
                 raise Exception(result.get("response", result.get("error")))
            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": str(result)}]}}

        elif tool_name == "dooray_getDriveList":
            result = dooray_get_drive_list(
                access_token=token,
                type=arguments.get("type", "private")
            )
            if "error" in result:
                raise Exception(result.get("response", result.get("error")))
            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": str(result)}]}}

        elif tool_name == "dooray_getDriveFiles":
            result = dooray_get_drive_files(
                access_token=token,
                drive_id=arguments.get("driveId")
            )
            if "error" in result:
                raise Exception(result.get("response", result.get("error")))
            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": str(result)}]}}

        else:
            return {
                "jsonrpc": "2.0", "id": request_id,
                "error": {"code": -32601, "message": "Method not found", "data": f"Tool '{tool_name}' not found."}
            }

    except Exception as e:
        print(f"Error in handle_tools_call: {e}")
        return {
            "jsonrpc": "2.0", "id": request_id,
            "error": {"code": -32000, "message": "Server error", "data": str(e)}
        }


@router.post("/mcp")
async def mcp_endpoint(request: Request):
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        if method == "initialize":
            response = await handle_initialize(request_id)
        elif method == "ping":
            response = await handle_ping(request_id)
        elif method == "tools/list":
            response = await handle_tools_list(request_id)
        elif method == "tools/call":
            response = await handle_tools_call(request_id, params, request)
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": "Method not found"
                }
            }
        return JSONResponse(content=response)
    except json.JSONDecodeError:
        return JSONResponse(content={
            "jsonrpc": "2.0", "id": None,
            "error": {"code": -32700, "message": "Parse error"}
        }, status_code=400)
    except Exception as e:
        return JSONResponse(content={
            "jsonrpc": "2.0", "id": None,
            "error": {"code": -32603, "message": "Internal error", "data": str(e)}
        }, status_code=500)


@router.get("/mcp/stream")
async def mcp_stream(request: Request):
    async def event_generator():
        while True:
            # Send a keepalive message every 30 seconds
            yield {
                "event": "message",
                "data": json.dumps({"type": "keepalive", "ts": datetime.now(timezone.utc).isoformat()})
            }
            await asyncio.sleep(30)

    return EventSourceResponse(event_generator())