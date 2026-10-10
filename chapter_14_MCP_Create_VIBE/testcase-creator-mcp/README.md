# TestCreator MCP (TC MCP)

![TestCreator MCP: 5,000 test cases, 21 tools, top tests, smoke suites and Gherkin](../assets/testcase-creator-hero.png)

An MCP server, built on FastMCP 4.1, that turns the VWO test case catalog (`../data/vwo_5000_test_cases.csv`, 5,000 tests across 17 modules) into tools any MCP client can use. Ask your assistant to find tests, rank what to run first, build smoke, sanity or regression suites, spot duplicates and coverage gaps, write new tests in the catalog format, and export to CSV, Jira CSV, Markdown, JSON, Gherkin or Playwright stubs.

The server never calls an LLM, so it needs no API keys. It never edits the source CSV either: new and edited tests go to an overlay file.

## Connect

### MCP Inspector

**Option 1: HTTP.** Start the server, then point the Inspector at it.

```bash
cd chapter_14_MCP_Create_VIBE/testcase-creator-mcp
uv run tc-mcp --transport http --port 8000        # serves http://127.0.0.1:8000/mcp
npx @modelcontextprotocol/inspector               # opens the Inspector UI
```

In the Inspector, set **Transport Type** to `Streamable HTTP` and **URL** to `http://127.0.0.1:8000/mcp`, then click **Connect**.

**Option 2: stdio.** The Inspector starts the server itself:

```bash
npx @modelcontextprotocol/inspector uv run --directory /ABS/PATH/chapter_14_MCP_Create_VIBE/testcase-creator-mcp tc-mcp
```

### Claude Code

```bash
# stdio (local clone)
claude mcp add tc-mcp -- uv run --directory /ABS/PATH/chapter_14_MCP_Create_VIBE/testcase-creator-mcp tc-mcp

# HTTP (server already running)
claude mcp add --transport http tc-mcp http://127.0.0.1:8000/mcp
```

### Claude Desktop, Cursor (`mcpServers`) or VS Code (`.vscode/mcp.json`, key `servers`)

```json
{
  "mcpServers": {
    "tc-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "/ABS/PATH/chapter_14_MCP_Create_VIBE/testcase-creator-mcp", "tc-mcp"],
      "env": { "TC_MCP_ALLOW_WRITE": "false" }
    }
  }
}
```

### Teammates without a clone (after this folder is pushed)

```bash
claude mcp add tc-mcp -- uvx --from "git+https://github.com/PramodDutta/AITesterBlueprint4x#subdirectory=chapter_14_MCP_Create_VIBE/testcase-creator-mcp" tc-mcp
```

The CSV is bundled into the package, so this works anywhere. In this mode the overlay and exports live in `~/.tc_mcp/`.

### Shared team server

```bash
TC_MCP_AUTH_TOKEN=<long-random-token> uv run tc-mcp --transport http --host 0.0.0.0 --port 8000
claude mcp add --transport http tc-mcp http://<server>:8000/mcp --header "Authorization: Bearer <long-random-token>"
```

In HTTP mode, exports come back inline (up to 200 rows) instead of being written to the server's disk. The server also runs stateless, so clients behind proxies or tunnels don't need a session ID, and anyone who opens the URL in a browser gets a "how to connect" page instead of a JSON error.

## Tools (21)

| Group | Tools |
|---|---|
| Discovery | `list_modules`, `get_filter_options`, `get_test_stats` |
| Find | `get_test_case`, `search_test_cases`, `search_by_keyword`, `get_top_tests_for_module`, `get_similar_test_cases` |
| Planning | `build_test_suite`, `get_browser_device_matrix`, `get_automation_candidates`, `estimate_execution_effort` |
| Quality | `find_duplicate_tests`, `find_coverage_gaps`, `validate_test_case` |
| Authoring | `get_test_case_template`, `add_test_cases`*, `update_test_case`* |
| Export | `export_test_cases`, `convert_to_gherkin`, `generate_automation_stub` |

\* Write tools only appear when writes are enabled (`--allow-write` or `TC_MCP_ALLOW_WRITE=true`). Both default to `dry_run=true`.

The server also provides:
- **Resources:** `tc://schema`, `tc://modules`, `tc://stats/summary`, `tc://test/{issue_key}`
- **Prompts:** `generate_test_cases`, `plan_release_run`, `review_module_coverage`

Try asking:
- "Top 5 tests to run for Reports on Safari"
- "All High and Highest Negative tests for SDK, max 10"
- "Build a smoke suite for A/B Testing and Heatmaps under 2 hours"
- "Which Reports features have no Security tests?"
- "Write 3 Boundary tests for seat limit in Account & Billing"

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `TC_MCP_DATA_PATH` | `../data/vwo_5000_test_cases.csv`, or the bundled copy | Use a different or newer CSV |
| `TC_MCP_OVERLAY_PATH` | `../data/tc_additions.csv` (`~/.tc_mcp/` when installed) | Where added or edited tests are stored |
| `TC_MCP_ALLOW_WRITE` | `false` | Enable `add_test_cases` and `update_test_case` |
| `TC_MCP_EXPORT_DIR` | `./exports` (`~/.tc_mcp/exports` when installed) | Where large exports are written |
| `TC_MCP_TRANSPORT`, `TC_MCP_HOST`, `TC_MCP_PORT` | `stdio`, `127.0.0.1`, `8000` | Same as `--transport`, `--host`, `--port` |
| `TC_MCP_AUTH_TOKEN` | unset | Bearer token required in HTTP mode |

The server reloads automatically when the CSV or overlay changes on disk.

## Develop

```bash
uv sync
uv run pytest -q          # 33 tests, in-memory MCP client, temp overlay
```

Layout: `src/tc_mcp/` contains `server.py` (wiring), `repository.py` (load, clean, index, overlay), `ranking.py`, `validation.py`, `resolver.py` (module aliases, did-you-mean), and `tools/` (one file per tool group). The design is described in `../01_TestCreatorMCP.plan.md`.
