"""A help page for people who open the MCP URL in a browser instead of an MCP client.

Browsers send GET with Accept: text/html, which the MCP transport rejects with a bare
JSON-RPC error. This ASGI middleware answers those requests with connection instructions
and passes everything else (MCP clients, SSE streams) straight through.
"""

from __future__ import annotations

import html

from starlette.responses import HTMLResponse
from starlette.types import ASGIApp, Receive, Scope, Send

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TestSkill Finder MCP</title>
<style>
  :root {{ --bg:#faf9f6; --fg:#1f1f1f; --muted:#5f5f5f; --card:#ffffff; --border:#e4e1da; --code:#f2efe8; --accent:#c2410c; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#161616; --fg:#ececec; --muted:#a3a3a3; --card:#1f1f1f; --border:#333; --code:#262626; --accent:#fb923c; }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--fg); font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif; }}
  main {{ max-width:760px; margin:0 auto; padding:32px 16px 48px; }}
  h1 {{ font-size:28px; margin:0 0 4px; }}
  h2 {{ font-size:17px; margin:28px 0 8px; }}
  p {{ margin:6px 0; color:var(--muted); }}
  .note {{ background:var(--card); border:1px solid var(--border); border-left:4px solid var(--accent); border-radius:8px; padding:12px 14px; margin:18px 0; color:var(--fg); }}
  pre {{ background:var(--code); border:1px solid var(--border); border-radius:8px; padding:12px; overflow-x:auto; margin:6px 0; font:13.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; white-space:pre; }}
  ul {{ padding-left:20px; margin:6px 0; }}
</style>
</head>
<body>
<main>
  <h1>TestSkill Finder MCP</h1>
  <p>Search and use 100 QA agent skills (STLC, Playwright, Selenium, Cypress, API, performance, security, LLM evals, agents, MCP) from any MCP client.</p>

  <div class="note">This address is an <strong>MCP endpoint</strong>, not a website. A browser cannot talk to it; add it to an MCP client instead.</div>

  <h2>Endpoint</h2>
  <pre>{url}</pre>

  <h2>MCP Inspector</h2>
  <pre>npx @modelcontextprotocol/inspector --transport http --server-url {url}</pre>

  <h2>Claude Code</h2>
  <pre>claude mcp add --transport http testskill-finder {url}</pre>

  <h2>VS Code (.vscode/mcp.json)</h2>
  <pre>{{ "servers": {{ "testskill-finder": {{ "type": "http", "url": "{url}" }} }} }}</pre>

  <h2>Cursor (~/.cursor/mcp.json)</h2>
  <pre>{{ "mcpServers": {{ "testskill-finder": {{ "url": "{url}" }} }} }}</pre>

  <h2>Things to ask</h2>
  <ul>
    <li>Find a skill for Playwright API testing</li>
    <li>Which skill writes a test plan from a Jira ticket?</li>
    <li>Plan the skills to take a story to automated Cypress tests</li>
    <li>Show me the LLM evaluation and MCP skills</li>
  </ul>
</main>
</body>
</html>
"""


def endpoint_url(scope: Scope, mcp_path: str) -> str:
    headers = {key.decode("latin-1").lower(): value.decode("latin-1") for key, value in scope.get("headers", [])}
    host = headers.get("x-forwarded-host") or headers.get("host") or "127.0.0.1:8000"
    local = host.startswith(("127.0.0.1", "localhost", "[::1]"))
    scheme = headers.get("x-forwarded-proto") or ("http" if local else "https")
    return f"{scheme}://{host}{mcp_path}"


class BrowserLandingPage:
    def __init__(self, app: ASGIApp, mcp_path: str = "/mcp") -> None:
        self.app = app
        self.mcp_path = mcp_path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] == "GET":
            accept = next((v.decode("latin-1") for k, v in scope.get("headers", []) if k.lower() == b"accept"), "")
            if "text/html" in accept and "text/event-stream" not in accept:
                url = html.escape(endpoint_url(scope, self.mcp_path), quote=True)
                await HTMLResponse(PAGE.format(url=url))(scope, receive, send)
                return
        await self.app(scope, receive, send)
