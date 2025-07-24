
import yaml, json
from pathlib import Path

root = {
    "openapi": "3.0.1",
    "info": {
        "title": "Dooray MCP API",
        "version": "1.0.0",
        "description": "Comprehensive Dooray API schema for LLMs"
    },
    "servers": [ 
        {
            "url": "https://kic-dooray-mcp.onrender.com"
        }
    ],
    "paths": {},
    "components": {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization"
            }
        }
    },
    "security": [{"ApiKeyAuth": []}]
}

for file in Path("schema").glob("*.yaml"):
    with open(file, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
        root["paths"].update(doc.get("paths", {}))

with open("schema.json", "w", encoding="utf-8") as f:
    json.dump(root, f, indent=2)
