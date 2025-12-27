"""
SEO MCP Server - Stdio client for seomcp backend
Reads MCP protocol from stdin, proxies to backend, writes responses to stdout.
"""
import sys
import json
import os
import asyncio
from typing import Any, Optional

import httpx


class StdioMCPClient:
    """Proxies MCP protocol through stdin/stdout to backend API."""

    def __init__(self, backend_url: str = "https://api.seomcp.run", api_key: str = ""):
        self.backend_url = backend_url.rstrip("/")
        self.api_key = api_key
        self.tools: dict[str, Any] = {}

    async def initialize_tools(self) -> dict[str, Any]:
        """Fetch available tools from backend; fallback to local schemas."""
        if self.tools:
            return self.tools

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                resp = await client.get(
                    f"{self.backend_url}/mcp/tools",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                if resp.status_code == 200:
                    self.tools = resp.json().get("tools", {})
                    return self.tools
        except Exception as e:  # noqa: BLE001
            print(f"Error fetching tools: {e}", file=sys.stderr)

        # Fallback: define tools locally
        self.tools = {
            "analyze_serp": {
                "name": "analyze_serp",
                "description": "Analyze SERP and derive patterns",
                "inputSchema": {
                    "type": "object",
                    "properties": {"keyword": {"type": "string"}},
                    "required": ["keyword"],
                },
            },
            "research_perplexity": {
                "name": "research_perplexity",
                "description": "Research using Perplexity API",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string"},
                        "patterns": {"type": "string"},
                    },
                    "required": ["keyword", "patterns"],
                },
            },
            "brainstorm_outline": {
                "name": "brainstorm_outline",
                "description": "Generate article outline",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "patterns": {"type": "string"},
                        "facts": {"type": "string"},
                    },
                    "required": ["patterns", "facts"],
                },
            },
            "gather_details": {
                "name": "gather_details",
                "description": "Gather details for outline",
                "inputSchema": {
                    "type": "object",
                    "properties": {"outline": {"type": "string"}},
                    "required": ["outline"],
                },
            },
            "generate_article": {
                "name": "generate_article",
                "description": "Generate article draft",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "outline": {"type": "string"},
                        "facts": {"type": "string"},
                        "details": {"type": "string"},
                    },
                    "required": ["outline", "facts", "details"],
                },
            },
            "embed_links": {
                "name": "embed_links",
                "description": "Embed links in article",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "article": {"type": "string"},
                        "research": {"type": "string"},
                    },
                    "required": ["article", "research"],
                },
            },
        }
        return self.tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Call a tool on the backend."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                resp = await client.post(
                    f"{self.backend_url}/mcp/call",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"tool": name, "arguments": arguments},
                )
                if resp.status_code == 200:
                    return resp.json().get("result", "")
                return json.dumps({"error": f"Backend error: {resp.status_code}"}, ensure_ascii=False)
        except Exception as e:  # noqa: BLE001
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle a single MCP protocol request."""
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            await self.initialize_tools()
            return {
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "seo-mcp-server", "version": "0.1.0"},
                },
            }

        if method == "resources/list":
            return {"result": {"resources": []}}

        if method == "tools/list":
            tools = await self.initialize_tools()
            return {
                "result": {
                    "tools": [
                        {
                            "name": t["name"],
                            "description": t["description"],
                            "inputSchema": t["inputSchema"],
                        }
                        for t in tools.values()
                    ]
                }
            }

        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = await self.call_tool(tool_name, arguments)
            return {"result": {"content": [{"type": "text", "text": result}]}}

        return {"error": {"code": -32601, "message": "Method not found"}}


def main_sync():
    """Synchronous wrapper for CLI."""
    asyncio.run(main())


def _env_or_default(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


async def main():
    api_key = _env_or_default("SEOMCP_API_KEY", "")
    backend_url = _env_or_default("SEOMCP_BACKEND_URL", "https://api.seomcp.run")

    if not api_key:
        print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "SEOMCP_API_KEY not set"}}))
        sys.exit(1)

    client = StdioMCPClient(backend_url=backend_url, api_key=api_key)

    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        line = await reader.readline()
        if not line:
            continue
        try:
            request = json.loads(line.decode().strip())
            response = await client.handle_request(request)
            if "id" in request:
                response["id"] = request["id"]
            response["jsonrpc"] = "2.0"
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}) + "\n")
            sys.stdout.flush()
        except Exception as e:  # noqa: BLE001
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main_sync()
