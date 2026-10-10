---
name: mcp-server-tester
description: >-
  Tests an MCP server: lists tools, resources and prompts, calls tools with valid and
  invalid arguments, and checks errors with the MCP Inspector CLI and the FastMCP Client.
  Use when an engineer says "test my MCP server", "check these MCP tools work", "write
  pytest tests for my FastMCP server", or shares a server URL or server.py. Produces
  Inspector smoke commands and a pytest suite, a draft the engineer runs and verifies.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: mcp
  version: 1.0.0
---

# MCP Server Tester

You prove **every tool, resource, and prompt works for valid input and fails clearly for bad
input**, first over the real transport, then fast and repeatable with in-memory pytest.

## When to use
- A new or changed MCP server needs a test suite before it is shared or deployed.
- A client (Claude, Cursor, an agent) "cannot see" a tool or gets confusing errors.
- You want regression tests that run in CI without starting a server process.

## Workflow
1. **Identify the server and transport.** stdio command (e.g. `python server.py`) or Streamable
   HTTP URL (e.g. `http://127.0.0.1:8000/mcp`), auth headers, and the expected tools, resources,
   and prompts. Ask if not given; never guess tool names.
2. **Smoke test with the Inspector CLI.** For stdio, pass the command instead of the URL; add
   `--header "Authorization: Bearer $TOKEN"` when auth is on:
   `npx @modelcontextprotocol/inspector --cli http://127.0.0.1:8000/mcp --transport http --method tools/list`
   Repeat with `--method` `resources/list`, `resources/templates/list`, `prompts/list`, and
   `--method tools/call --tool-name search_test_cases --tool-arg query=login --tool-arg limit=5`.
3. **Check discovery quality.** Each tool has a description that says when to use it and an
   input schema with required fields, enums, and bounds; resources have URIs and MIME types.
4. **Write in-memory pytest.** `async with Client(mcp) as c` talks to the server object directly
   (no network, no subprocess). Set `asyncio_mode = "auto"` for pytest-asyncio.
5. **Call every tool both ways.** Valid args: `is_error` is false and `structured_content` has
   the right shape. Invalid args (wrong type, out of range, missing, bad enum, unknown id):
   `ToolError` whose message names the field or next step, never a stack trace.
6. **Cover resources, prompts, and size.** `read_resource(uri)`, `get_prompt(name, args)`,
   unknown URIs, and large queries that must be paginated or capped.
7. **List assumptions.** Import path of `mcp`, test data, services to stub, auth setup.

## Output shape
```python
# tests/test_server.py   (pyproject: [tool.pytest.ini_options] asyncio_mode = "auto")
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from tc_server.server import mcp

@pytest.fixture
async def client():
    async with Client(mcp) as c:  # in-memory: no network, no subprocess
        yield c

async def test_tools_are_listed_with_descriptions_and_schemas(client):
    tools = {t.name: t for t in await client.list_tools()}
    assert {"search_test_cases", "get_test_case"} <= set(tools)
    for name, tool in tools.items():
        assert tool.description and len(tool.description) > 20, f"{name}: weak description"
        assert tool.input_schema["type"] == "object"  # .inputSchema on FastMCP 2.x

async def test_valid_call_respects_limit(client):
    result = await client.call_tool("search_test_cases", {"query": "login", "limit": 5})
    assert not result.is_error and len(result.structured_content["items"]) <= 5

async def test_out_of_range_arg_names_the_field(client):
    with pytest.raises(ToolError, match="limit"):
        await client.call_tool("search_test_cases", {"query": "login", "limit": 0})
```

## Guardrails
- This is a draft the engineer must run; never claim the suite passes without running it.
- Never fabricate tool names, parameters, or schemas; read them from `tools/list` first.
- In-memory tests skip transport and auth, so keep at least one Inspector or HTTP smoke test.
- Never call write or destructive tools against real data; use a test store or fixtures.
- Assert on structure and error clarity, not exact wording that may be reworded later.
