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

from dooray_client import get_projects as dooray_get_projects, create_project_post as dooray_create_task, get_project_members as dooray_get_members, get_project_tags as dooray_get_tags, get_drive_list as dooray_get_drive_list, get_drive_files as dooray_get_drive_files, download_file_base64 as dooray_download_file, get_file_chunk as dooray_get_file_chunk

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
        },
        {
            "name": "dooray_downloadFile",
            "description": "Initiates a file download from Dooray Drive, returning the first chunk of data.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "drive_id": {"type": "string", "description": "The ID of the drive."},
                    "file_id": {"type": "string", "description": "The ID of the file."}
                },
                "required": ["drive_id", "file_id"]
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "fileName": {"type": "string"},
                    "totalChunks": {"type": "integer"},
                    "chunkSessionId": {"type": "string"},
                    "chunkData": {"type": "string", "description": "Base64 encoded first chunk of the file."}
                }
            }
        },
        {
            "name": "dooray_getFileChunk",
            "description": "Gets a specific chunk of a file that is being downloaded.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "chunkSessionId": {"type": "string", "description": "The session ID from the initial downloadFile call."},
                    "chunkIndex": {"type": "integer", "description": "The index of the chunk to retrieve."}
                },
                "required": ["chunkSessionId", "chunkIndex"]
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "chunkSessionId": {"type": "string"},
                    "chunkIndex": {"type": "integer"},
                    "chunkData": {"type": "string", "description": "Base64 encoded chunk of the file."}
                }
            }
        },
        {
            "name": "dooray_setToken",
            "description": "Set Dooray API token for authentication",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "Your Dooray API token"}
                },
                "required": ["token"]
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
    
    # Handle token setting first (no authentication required)
    if tool_name == "dooray_setToken":
        token = arguments.get("token")
        if not token:
            return {
                "jsonrpc": "2.0", "id": request_id,
                "error": {"code": -32602, "message": "Invalid params", "data": "Token is required"}
            }
        
        # Get conversation ID for session-based token storage
        conversation_id = request.headers.get("claude-conversation-id") or request.headers.get("X-Conversation-ID") or "default"
        SESSION_TOKENS[conversation_id] = token
        
        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": "Dooray API token has been set successfully. You can now use other Dooray functions."}]}}

    # Handle chunk fetching (no authentication required)
    if tool_name == "dooray_getFileChunk":
        session_id = arguments.get("chunkSessionId")
        chunk_index = arguments.get("chunkIndex")
        if not session_id or chunk_index is None:
            return {
                "jsonrpc": "2.0", "id": request_id,
                "error": {"code": -32602, "message": "Invalid params", "data": "chunkSessionId and chunkIndex are required"}
            }
        result = dooray_get_file_chunk(session_id, chunk_index)
        if "error" in result:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": "Server error", "data": result["error"]}}
        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "json", "json": result}]}}
    
    # Get API token for other functions
    conversation_id = request.headers.get("claude-conversation-id") or request.headers.get("X-Conversation-ID")
    if conversation_id:
        token = SESSION_TOKENS.get(conversation_id)
        if not token:
            return {
                "jsonrpc": "2.0", "id": request_id,
                "result": {"content": [{"type": "text", "text": "🔐 Dooray API 토큰이 설정되지 않았습니다.\n\n먼저 'dooray_setToken' 도구를 사용하여 API 토큰을 설정해주세요:\n\n1. Dooray에서 API 토큰을 발급받으세요\n2. 'dooray_setToken' 도구에 토큰을 입력하세요\n3. 그 후 다른 Dooray 기능을 사용할 수 있습니다"}]}
            }
        
    else:
        token = os.getenv("DOORAY_API_TOKEN")
        if not token:
            return {
                "jsonrpc": "2.0", "id": request_id,
                "result": {"content": [{"type": "text", "text": "🔐 Dooray API 토큰이 설정되지 않았습니다.\n\n먼저 'dooray_setToken' 도구를 사용하여 API 토큰을 설정해주세요:\n\n1. Dooray에서 API 토큰을 발급받으세요\n2. 'dooray_setToken' 도구에 토큰을 입력하세요\n3. 그 후 다른 Dooray 기능을 사용할 수 있습니다"}]}
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

        elif tool_name == "dooray_downloadFile":
            result = dooray_download_file(
                access_token=token,
                drive_id=arguments.get("drive_id"),
                file_id=arguments.get("file_id"),
                media=arguments.get("media", "raw")
            )
            if "error" in result:
                raise Exception(result.get("response", result.get("error")))
            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "json", "json": result}]}}

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