# 02 Prompts: how TestCreator MCP was built

These are the exact prompts used on 2026-10-10 to go from a CSV file to a working, shared MCP server, in the order they were sent. Each prompt is quoted as typed, typos included, followed by a short note on what happened.

**Starting point:** [`00_Objective.md`](00_Objective.md) (the goal) and `data/vwo_5000_test_cases.csv` (5,000 VWO test cases).

---

## Prompt 1: Plan first, no code

```text
@chapter_14_MCP_Create_VIBE/data/vwo_5000_test_cases.csv  Lets discuss don't code, we want to build a TestCreator MCP (TC MCP), which we can share with the other QA or Dev if required. lets create a Plan how this is going to created and also we will use the FastMCP for the same, tools also, give me the list of tools which we should give them by reading it and also prepare a 01_TestCreatorMCP.plan.md
```

**What happened**
- Claude read `00_Objective.md` and profiled all 5,000 rows before suggesting any tools. The profile showed 17 modules, 72 features, 4 priorities, 9 test types, 4 browsers and 4 devices.
- The profile also found problems a tool list has to handle:
  - only 1,520 unique scenarios, plus 466 exact duplicate rows
  - 415 deprecated tests
  - a broken `A/B Testing` label (saved as just `a`)
  - a doubled `regression` label
- Claude wrote [`01_TestCreatorMCP.plan.md`](01_TestCreatorMCP.plan.md). It proposes 21 tools in 6 groups, a ranking formula for "top tests", limits on response size, ways to share the server, a phased build plan, and open questions.

## Prompt 2: Build it

```text
use the folder  testcase_Creator_mcp and create and give me the mcp connection string to connect with it.
```

**What happened**
- **Checked the real versions first.** PyPI showed **FastMCP 4.1.0** as the current stable release, not 3.x as the plan assumed. FastMCP 4.1 doesn't install on Python 3.15 yet, so the project is capped below it.
- **Tested the FastMCP 4 API before writing real code.** A tiny throwaway server confirmed how tools, filters, errors, resources, prompts, and hiding tools by tag behave.
- **Built the server** in `testcase_creator_mcp/`:
  - all 21 tools, 4 resources and 3 prompts
  - write tools hidden by default
  - edits saved to a separate overlay file, so the source CSV is never changed
- **Tested it** with 33 pytest tests, a real stdio client, an HTTP client, and the official MCP Inspector CLI.
- **Shared the connection strings:** `http://127.0.0.1:8000/mcp` (HTTP) and `uv run --directory <path> tc-mcp` (stdio).

## Prompt 3: Updates, and use the Inspector (sent while Prompt 2 was running)

```text
share updates and link of the mcp when ready we will connect to it via the mcp inspector
```

**What happened**
- Claude posted progress updates while building.
- Started the server over HTTP and checked that MCP Inspector 2.10.1 could list and call the tools.
- Wrote [`testcase_creator_mcp/README.md`](testcase_creator_mcp/README.md) with every way to connect.

## Prompt 4: Restart the Inspector on this server

```text
close the mcp inspector and restart with this mcp testcase creator
```

**What happened**
- Found and stopped an old Inspector that had been running for 6 days with a different MCP config.
- MCP Inspector v2 changed its command-line flags, so Claude read the installed package to find the new ones.
- Relaunched the Inspector web UI already pointed at TC MCP:
  `npx @modelcontextprotocol/inspector --transport http --server-url http://127.0.0.1:8000/mcp`

## Prompt 5: Share it publicly for students

```text
lets host this mcp on the tryclouflare for sometime so that students can check
```

**What happened**
- **Checked the server was safe to expose:** read-only, it accepts a public hostname, and exports return inline instead of writing files to the host.
- **Opened a Cloudflare quick tunnel:** `cloudflared tunnel --url http://127.0.0.1:8000`.
- **Tested the public `https://<random>.trycloudflare.com/mcp` URL** with a FastMCP client and the Inspector CLI. It listed 19 tools and answered calls in about 150 to 200 ms.
- **Shared a message for students** with the URL and connection lines for the Inspector, Claude Code, VS Code and Cursor.

## Prompt 6: An error from a student

```text
{"jsonrpc":"2.0","id":null,"error":{"code":-32600,"message":"Bad Request: Missing session ID"}}
```

**What happened**
- **Found the cause in the logs.** About 20 students had opened the MCP URL in a browser. A browser sends a plain `GET`, which an MCP endpoint rejects. 14 students had already connected successfully with real MCP clients.
- **Fix 1: stateless HTTP mode.** The server keeps no per-user state, so clients behind proxies or tunnels no longer need a session ID.
- **Fix 2: a browser help page** (`src/tc_mcp/landing.py`). Opening the URL in a browser now shows how to connect instead of a JSON error.

## Prompt 7: Stop it (sent while Prompt 6 was running)

```text
stop the public MCP now
```

**What happened**
- Closed the Cloudflare tunnel. The public URL now returns HTTP 530, meaning there is no tunnel behind it.
- Checked both fixes from Prompt 6 on a local-only port. All 33 tests pass.
- The local server and Inspector were left running on the Mac only.

## Prompt 8: Record the prompts

```text
Can you please also write in the 02_prompt.md file whatever the prompt I have used to create this MCP? Whatever the conversation that we have till now today
```

**What happened:** this file.

---

## What came out of it

| File | What it is |
|---|---|
| [`01_TestCreatorMCP.plan.md`](01_TestCreatorMCP.plan.md) | The plan, updated to match the build |
| [`testcase_creator_mcp/`](testcase_creator_mcp/) | The FastMCP 4.1 server: 21 tools, 4 resources, 3 prompts, 33 tests |
| [`testcase_creator_mcp/README.md`](testcase_creator_mcp/README.md) | Connection options for the Inspector, Claude Code, VS Code, Cursor, `uvx` and a shared server |
| [`../learnings/2026-10-10-csv-catalog-to-mcp-server.md`](../learnings/2026-10-10-csv-catalog-to-mcp-server.md) | The approach and judgment calls, written down for reuse |

## Lessons from this session

1. **Plan before you build.** Prompt 1 said "don't code", so the data got profiled first, and the duplicates and broken labels shaped the tool design.
2. **One clear outcome per prompt.** Each prompt asked for something specific and checkable: a plan file, a connection string, a running Inspector, a public URL.
3. **Paste errors exactly as you see them.** Prompt 6 was only the raw error text. That was enough to find the cause in the server logs.
4. **Keep a stop switch for anything public.** Prompt 7 shut down public access in one line.
