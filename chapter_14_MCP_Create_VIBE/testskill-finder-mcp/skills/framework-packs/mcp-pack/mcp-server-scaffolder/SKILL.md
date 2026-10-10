---
name: mcp-server-scaffolder
description: >-
  Scaffolds a Python FastMCP server with tools, a resource, a prompt, stdio and HTTP entry
  points, pytest tests, and client config snippets. Use when an engineer says "scaffold an
  MCP server", "create a FastMCP server for our test data", "start a new MCP server in
  Python", or describes the tools they need. Produces a project layout, server.py, tests,
  and Claude config snippets, a draft the engineer runs and verifies.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: mcp
  version: 1.0.0
---

# MCP Server Scaffolder

You produce **a small, runnable FastMCP server with tests on day one**, built only from the tools described.

## When to use
- A team wants to expose test data or an internal tool to Claude or another MCP client.
- A prototype server is one messy script and needs structure, tests, and client config.
- A workshop needs a clean starting point for building MCP tools.

## Workflow
1. **Gather the spec.** Name; 2-5 tools (read or write); resources and prompts; data source; transport
   (stdio for local desktop clients, HTTP for shared use). Ask instead of inventing tools.
2. **Lay out the project with uv.** `uv init --package tc-server`, `uv add fastmcp`,
   `uv add --dev pytest pytest-asyncio`; add `asyncio_mode = "auto"` under `[tool.pytest.ini_options]`.
3. **Write the server.** `@mcp.tool` with typed params and "use when" docstrings, `@mcp.resource`, `@mcp.prompt`,
   recoverable `ToolError` messages; `stdio` by default, `transport="http"` serves Streamable HTTP at `/mcp`.
4. **Add tests.** In-memory `Client(mcp)`: `list_tools`, a valid call, bad args raising `ToolError`,
   `read_resource`, `get_prompt`. Smoke test over HTTP with the Inspector CLI:
   `npx @modelcontextprotocol/inspector --cli http://127.0.0.1:8000/mcp --transport http --method tools/list`
5. **Write client config.** Claude Code (stdio, then HTTP):
   `claude mcp add tc-server -- uv run --directory /abs/path/tc-server python src/tc_server/server.py`
   `claude mcp add --transport http tc-server http://127.0.0.1:8000/mcp`
   Claude Desktop `claude_desktop_config.json`, same command under `mcpServers.tc-server`:
   `{"command": "uv", "args": ["run", "--directory", "/abs/path/tc-server", "python", "src/tc_server/server.py"]}`
6. **List assumptions.** Data source, auth needs, absolute paths, and TODOs left in the code.

## Output shape
```python
# src/tc_server/server.py
from typing import Annotated
from fastmcp import FastMCP
from fastmcp.exceptions import ResourceError, ToolError
from pydantic import Field

mcp = FastMCP("tc-server")
CASES = {"TC-1": {"id": "TC-1", "title": "Login with valid credentials"}}  # TODO: real data source

@mcp.tool(annotations={"readOnlyHint": True})
def get_test_case(case_id: Annotated[str, Field(pattern=r"^TC-\d+$", description="e.g. TC-1")]) -> dict:
    """Get one test case by id. Use when the user names a specific case id."""
    if case_id not in CASES:
        raise ToolError(f"No test case {case_id}. Check the id, format is TC-<number>.")
    return CASES[case_id]

@mcp.resource("testcases://{case_id}")
def test_case_resource(case_id: str) -> dict:
    """Read-only test case document."""
    if case_id not in CASES:
        raise ResourceError(f"Unknown test case {case_id}")
    return CASES[case_id]

@mcp.prompt
def review_test_case(case_id: str) -> str:
    """Ask the model to review a test case for gaps."""
    return f"Review test case {case_id} for missing negative, boundary and cleanup steps."

if __name__ == "__main__":
    mcp.run(transport="stdio")  # shared use: mcp.run(transport="http", host="127.0.0.1", port=8000)
```

## Guardrails
- Never invent tools, data fields, or credentials; scaffold only what the spec names, mark TODOs.
- A stdio server must never print to stdout (it corrupts the JSON-RPC stream); log to stderr.
- HTTP binds to 127.0.0.1; add auth before exposing it on a network. Secrets come from env vars only.
- This is a draft scaffold: the engineer runs `uv run pytest` and the Inspector smoke test first.
