## Plan: TestCreator MCP (TC MCP) on FastMCP

> **Status (2026-10-10): built.** The code is in `testcase_creator_mcp/`, with all 21 tools, 4 resources, 3 prompts and 33 passing tests. See its README for connection options. This plan has been updated to match what was built.

**TL;DR**: A Python MCP server built with FastMCP 4.1. It loads `data/vwo_5000_test_cases.csv` into memory once, cleans it up, and exposes 21 tools to any MCP client (Claude Code, Claude Desktop, Cursor, VS Code). The tools let a QA or dev find test cases (by module, priority, type, browser, device), rank the top tests to run, build smoke, sanity and regression suites, spot duplicates and coverage gaps, write new test cases in the same VWO format, and export to CSV, Jira CSV, Markdown or Gherkin. The server makes no LLM calls: the client's LLM does the writing and reasoning, and TC MCP stays deterministic, free and offline. We build it in 6 phases. The first usable version (Phase 2) ships 5 tools, and teammates can install it with one command.

---

### 1. What the data tells us

I profiled all 5,000 rows before designing any tools. Every design decision below traces back to these numbers.

| Column | Values | Notes |
|---|---|---|
| `Issue Type` | `Test` (all 5,000) | Constant, so it is not a filter |
| `Issue Key` | `VWO-1001` to `VWO-6000` | Unique. New tests start at `VWO-6001` |
| `Summary` | `[Module] Type: action feature` | Matches the pattern on 100% of rows. Only **1,520 unique summaries** |
| `Description` | `...the <feature> in the <Module> module...` | Gives the **feature** on 100% of rows: **72 features**, 4 to 6 per module, 38 to 95 tests each |
| `Priority` | Highest 396 · High 1,546 · Medium 2,198 · Low 860 | Ordered scale, so min and max filters work |
| `Component` (module) | 17 modules, 265 to 333 tests each | e.g. `A/B Testing`, `SDK / Server-Side API`, `Account & Billing` |
| `Test Type` | Functional 1,516 · Negative 810 · UI/UX 515 · API 415 · Boundary 406 · Regression 379 · Security 368 · Accessibility 321 · Performance 270 | 9 values |
| `Browser` | Chrome 148 · Firefox 141 · Safari 19 · Edge 148 | Evenly spread, about 1,200 to 1,300 each |
| `Device` | desktop · mobile (Android) · mobile (iOS) · tablet | Evenly spread |
| `Status` | Ready 2,234 · Automated 1,594 · Draft 757 · Deprecated 415 | Deprecated is hidden by default, which leaves **4,585 live tests** |
| `Steps` | Always exactly 4 steps, joined with ` \| ` | Split into a list when loading |
| `Expected Result` | Only 358 unique strings | Many are generic, which the linter will flag |

**Data quirks to fix while loading (the source CSV is never edited):**

1. **Broken A/B labels:** `A/B Testing` rows are labelled `a functional regression`, because the `/` broke the slug. We rebuild labels as `ab-testing`.
2. **Doubled label:** `Regression` type rows carry `regression regression`. We dedupe it.
3. **Duplicates:** 466 rows repeat an existing (Summary, Browser, Device) combination, with up to 4 copies. We flag them but keep them, and give the user a tool to list them.
4. **Variants of one scenario:** 1,520 scenarios fan out into 5,000 rows across browsers and devices. "Top N" results must spread across scenarios, or the top 10 ends up as 10 copies of "verify SSO login".

**Size budget for responses:** an average full row is 745 bytes (about 190 tokens). A compact row is about 45 tokens. That sets our limits: **100 compact rows or 25 full rows per call**, which is about 4 to 5k tokens at most.

---

### 2. Objective to tool mapping

| Ask in `00_Objective.md` | Covered by |
|---|---|
| Get test cases by **priority** | `search_test_cases(priority=[...])`, or `min_priority` / `max_priority` |
| Get test cases by **module** | `search_test_cases(module=...)`, `list_modules` |
| **Maximum and minimum limits** | `limit` (1 to 100) and `offset` on every list tool, `min_tests` / `max_tests` on `build_test_suite`, `min_priority` / `max_priority` filters. See open question 1 |
| **Top test cases to execute** for a module | `get_top_tests_for_module` (ranked, with a reason for each pick) |
| "A lot of tools useful for a test creator" | The other 16 tools: planning, quality, authoring and export |

---

### 3. Architecture

```
 QA / Dev in Claude Code · Claude Desktop · Cursor · VS Code
                │  MCP protocol (stdio locally, streamable HTTP when shared)
                ▼
┌──────────────────── TC MCP (FastMCP 4.1, Python 3.11-3.14) ───────────────────┐
│  21 Tools          4 Resources           3 Prompts                          │
│      │                                                                      │
│  Service layer:  filters · module resolver · ranking · suite builder · lint │
│      │                                                                      │
│  Repository: load CSV -> validate -> normalize -> build in-memory indexes   │
└──────┬──────────────────────────────────────────────┬───────────────────────┘
       ▼                                              ▼
 data/vwo_5000_test_cases.csv                  data/tc_additions.csv
 (source of truth, read-only)                  (overlay: new and edited tests,
                                                created on the first write)
```

**Request flow, using "top 5 Highest tests for Reports on Safari" as the example:**
LLM picks `get_top_tests_for_module(module="reports", count=5, browser="Safari 19")` -> resolver maps `reports` to `Reports` -> repository filters the live rows -> ranking scores each row and spreads picks across features -> response returns 5 compact rows, each with a `rank_reason`.

---

### 4. Tech stack and key decisions

| Decision | Choice | Why |
|---|---|---|
| MCP framework | `fastmcp>=4.1.0,<5`, Python `>=3.11,<3.15` | 4.1.0 is the current stable release on PyPI (it runs on MCP SDK 2.3). 4.1 does not resolve on Python 3.15 yet, so the Python version is capped |
| Packaging and runner | `uv` with `pyproject.toml` and a `tc-mcp` console script | Teammates get a one-line install (`uv run` or `uvx`) |
| Data layer | stdlib `csv` plus Pydantic models (Pydantic already comes with FastMCP) | 5,000 rows fit easily in memory. No pandas, so installs stay small |
| Storage for writes | A CSV overlay file that uses the same columns as the source. Moves to SQLite only for hosted HTTP mode | Diffable in git and simple. The base CSV is never changed |
| Search | Keyword scoring on summary, description, steps and expected result | Good enough for 5k templated rows. RAG was already covered in chapters 10 to 12 |
| Enums in tool schemas | `Literal[...]` types for priority, type, browser, device and status | The client LLM sees the allowed values in the schema and stops guessing |
| Module names | Case-insensitive resolver with aliases and "did you mean" suggestions | Users type `ab testing`, `sdk`, `billing` |
| Write safety | Write tools are only registered when `TC_MCP_ALLOW_WRITE=true` | Read-only by default: a dev's LLM never even sees a write tool |

**Config (environment variables):**

| Variable | Default | Purpose |
|---|---|---|
| `TC_MCP_DATA_PATH` | The CSV bundled in the package | Point at a different or newer CSV |
| `TC_MCP_OVERLAY_PATH` | `data/tc_additions.csv` | Where new and edited tests go |
| `TC_MCP_ALLOW_WRITE` | `false` | Turns on `add_test_cases` and `update_test_case` |
| `TC_MCP_EXPORT_DIR` | `./exports` | Where large exports are written |
| `TC_MCP_TRANSPORT` / `TC_MCP_PORT` | `stdio` / `8000` | Set to `http` for the shared server |
| `TC_MCP_AUTH_TOKEN` | unset | Bearer token, required in HTTP mode |

---

### 5. Tool catalog (21 tools)

Phase **P2** is the first usable version. **R** = read-only (`readOnlyHint`), **W** = write (gated). Each tool also gets a FastMCP tag (its group name) so a client profile can load only a subset.

#### A. Discovery (helps the LLM learn the catalog)

| # | Tool | Purpose | Key params | Returns | Phase |
|---|---|---|---|---|---|
| 1 | `list_modules` | All 17 modules, with test counts, features and priority split | `include_features: bool = true` | `[{module, total, live, by_priority, features[]}]` | P2 · R |
| 2 | `get_filter_options` | The exact allowed values for every filter, plus module aliases | none | `{priorities, test_types, browsers, devices, statuses, modules, aliases}` | P2 · R |
| 3 | `get_test_stats` | Counts grouped by 1 or 2 dimensions, with optional filters | `group_by: list[module\|priority\|test_type\|status\|browser\|device\|feature]` (1 to 2), plus `TestFilter` | Pivot table, e.g. module × priority | P3 · R |

#### B. Find and fetch

| # | Tool | Purpose | Key params | Returns | Phase |
|---|---|---|---|---|---|
| 4 | `get_test_case` | Full detail for 1 to 25 keys | `issue_keys: list[str]` | Full rows. Unknown keys are listed separately | P2 · R |
| 5 | `search_test_cases` | **The main filter tool.** Covers by module, by priority, and min/max limits | `TestFilter` + `sort_by: priority\|key` + `limit` (1 to 100, default 20) + `offset` + `detail: compact\|full` (full is capped at 25) | List envelope (see §7) | P2 · R |
| 6 | `search_by_keyword` | Free-text search ("rate limiting", "SSO", "invoice") | `query`, `module?`, `limit` | Ranked compact rows with the matched field | P3 · R |
| 7 | `get_top_tests_for_module` | **"What should I run first?"** A ranked shortlist | `module`, `count` (1 to 50, default 10), `test_types?`, `browser?`, `device?`, `unique_scenarios: bool = true` | Ranked rows, each with `score` and `rank_reason` | P2 · R |
| 8 | `get_similar_test_cases` | Same feature, different type, browser or device. Used for reviews and few-shot examples | `issue_key`, `limit` | Compact rows plus what differs from the given test | P3 · R |

**`TestFilter`** is one shared Pydantic model, reused by tools 3, 5, 12 and 19, so filters behave the same everywhere:
`module: str | list[str]`, `feature`, `priority: list[...]`, `min_priority`, `max_priority`, `test_type: list[...]`, `browser`, `device`, `status: list[...]`, `label`, `include_deprecated: bool = false`, `include_duplicates: bool = true`.
Priority order: `Low < Medium < High < Highest`, so `min_priority="High"` returns High and Highest.

#### C. Execution planning

| # | Tool | Purpose | Key params | Returns | Phase |
|---|---|---|---|---|---|
| 9 | `build_test_suite` | Builds a ready-to-run smoke, sanity or regression suite | `suite_type: smoke\|sanity\|regression`, `modules: list \| "all"`, `min_tests`, `max_tests`, `browsers?`, `devices?`, `include_drafts: bool = false` | Ordered suite, its makeup (by module, type and priority), an effort estimate, and any relaxations applied | P3 · R |
| 10 | `get_browser_device_matrix` | A 4 × 4 browser × device coverage grid | `module?`, `feature?` | Grid counts with empty cells flagged | P3 · R |
| 11 | `get_automation_candidates` | Ready but not yet Automated tests that are worth automating | `module?`, `min_priority = "High"`, `limit` | Ranked rows with a reason, e.g. "High priority API test, stable steps, 3 browser variants" | P3 · R |
| 12 | `estimate_execution_effort` | "How long will these take?" | `issue_keys` or `TestFilter`, `minutes_manual = 10`, `minutes_automated = 1` | Totals split by manual and automated, per module | P3 · R |

**Suite rules** (kept in `config.py` so they can be tuned):
- **smoke**: Highest only. Functional, API and Security types. One best-ranked test per feature (72 at most). Desktop Chrome preferred.
- **sanity**: Highest and High. Functional, Negative and API types. Up to 2 tests per feature.
- **regression**: All live tests, ranked. Drafts only when `include_drafts=true`.
- **min/max**: Results are trimmed to `max_tests` while keeping the feature spread. If fewer than `min_tests` match, the tool adds the next priority tier and reports that it did.

#### D. Quality

| # | Tool | Purpose | Key params | Returns | Phase |
|---|---|---|---|---|---|
| 13 | `find_duplicate_tests` | Groups exact and near-duplicate tests (466 duplicate rows today) | `module?`, `mode: exact\|same_scenario` | Groups with one suggested keeper per group | P3 · R |
| 14 | `find_coverage_gaps` | Finds holes in feature × test type coverage | `module?` | Missing combinations, features with no Highest test, features with no Security or Accessibility test, empty device or browser cells | P3 · R |
| 15 | `validate_test_case` | Lints a draft test before it is saved | `test_case: TestCaseDraft` | `errors[]` (wrong enum value, step format, summary pattern), `warnings[]` (generic expected result, fewer than 3 steps), `possible_duplicates[]` | P4 · R |

#### E. Authoring (the "Test Creator" part)

| # | Tool | Purpose | Key params | Returns | Phase |
|---|---|---|---|---|---|
| 16 | `get_test_case_template` | A pre-filled VWO-format skeleton plus 3 real examples for the client LLM to learn from | `module`, `feature`, `test_type`, `browser?`, `device?` | `{template, examples[3], rules}` | P4 · R |
| 17 | `add_test_cases` | Validates, assigns keys from `VWO-6001` up, and appends to the overlay | `test_cases: list[TestCaseDraft]` (1 to 25), `dry_run: bool = true` | Assigned keys, or the validation errors | P4 · **W** |
| 18 | `update_test_case` | Changes status, priority, steps or expected result. Writes a new copy to the overlay, and the latest copy wins | `issue_key`, `changes: dict` | Before and after diff | P4 · **W** |

`dry_run=true` by default means the LLM has to show the user the result before a second call that actually writes.

#### F. Export and convert

| # | Tool | Purpose | Key params | Returns | Phase |
|---|---|---|---|---|---|
| 19 | `export_test_cases` | Export a selection | `issue_keys` or `TestFilter`, `format: csv\|jira_csv\|markdown\|json` | Up to 50 rows: returned inline. More than 50: a file in `exports/`, and the tool returns its path | P4 · R |
| 20 | `convert_to_gherkin` | Turns tests into `.feature` scenarios (Preconditions → Given, Steps → When/And, Expected → Then) | `issue_keys` (1 to 10) | Gherkin text | P4 · R |
| 21 | `generate_automation_stub` | A pytest-playwright or Playwright TS skeleton, with the steps as comments | `issue_key`, `framework: pytest_playwright\|playwright_ts` | Code text | P5 stretch · R |

**Tool description rule:** every docstring opens with *when to use it* and names the sibling tool to use instead. For example, `search_test_cases` says "for 'what should I run first', use `get_top_tests_for_module`". With 21 tools, clear descriptions matter more than anything else for getting the LLM to pick the right tool.

---

### 6. Ranking logic (`get_top_tests_for_module`, `build_test_suite`)

```
score = priority_weight + status_weight + type_weight

priority_weight : Highest 40 · High 30 · Medium 20 · Low 10
status_weight   : Ready 10 · Automated 8 · Draft 2 · Deprecated -> excluded
                  (Draft tests are skipped unless include_drafts=true)
type_weight     : Security 6 · Functional 6 · Negative 5 · API 5 · Regression 4
                  Boundary 4 · Performance 3 · UI/UX 2 · Accessibility 2
tie-break       : lower Issue Key first (stable, repeatable output)

diversity (unique_scenarios=true):
  1. keep only the best-scoring row per scenario (Summary)
  2. round-robin across features, so the top 10 covers several features
     instead of 10 variants of one
```

Every result has a `rank_reason`, e.g. `"Highest · Ready · Security · first pick for feature 'SSO login'"`, so the person can trust the pick or challenge it. The weights live in `config.py`.

---

### 7. Resources, prompts and the response contract

**Resources** (read-only context the client can attach):

| URI | Content |
|---|---|
| `tc://schema` | Column definitions, allowed values and the summary and step formats |
| `tc://modules` | Modules, their features and counts |
| `tc://stats/summary` | Headline numbers (as in §1) |
| `tc://test/{issue_key}` | One test case. A resource template, so it can be @-mentioned in clients that support it |

**Prompts** (reusable workflows a user picks from the client menu):

| Prompt | What it guides the LLM to do |
|---|---|
| `generate_test_cases(module, feature, test_type, count)` | template → write drafts → `validate_test_case` → show the user → `add_test_cases(dry_run=false)` |
| `plan_release_run(modules, max_tests, deadline_hours)` | `build_test_suite` → `estimate_execution_effort` → trim to fit → export |
| `review_module_coverage(module)` | `get_test_stats` → `find_coverage_gaps` → `find_duplicate_tests` → a short report |

**Response contract** (the same for every list tool):

```json
{
  "total_matched": 312,
  "returned": 20,
  "offset": 0,
  "next_offset": 20,
  "filters_applied": {"module": "Reports", "min_priority": "High", "include_deprecated": false},
  "results": [
    {"key": "VWO-1004", "summary": "[Reports] Boundary: test limits of scheduled email",
     "module": "Reports", "feature": "scheduled email", "priority": "High",
     "test_type": "Boundary", "status": "Ready", "browser": "Edge 148", "device": "tablet"}
  ]
}
```

- `compact` rows hold the 9 fields above. `full` rows add description, preconditions, `steps[]`, expected result and labels.
- Limits: compact rows max 100, full rows max 25, default 20. The bounds are in the tool schema, so an out-of-range `limit` is rejected with a clear message. A `full` request above 25 rows is lowered to 25, and a note says so.
- Errors are raised as FastMCP `ToolError` with a helpful message, e.g. `Unknown module 'ab test'. Did you mean 'A/B Testing'? Valid: ...`.
- An empty result is not an error: the tool returns `total_matched: 0` and a hint about which filter to loosen.

---

### 8. Project layout

```
chapter_14_MCP_Create_VIBE/
├── 00_Objective.md
├── 01_TestCreatorMCP.plan.md            # this file
├── data/
│   ├── vwo_5000_test_cases.csv          # source of truth, never edited
│   └── tc_additions.csv                 # overlay, created on the first write
└── testcase_creator_mcp/
    ├── pyproject.toml                   # fastmcp pin, tc-mcp script, bundles the CSV into the wheel
    ├── README.md                        # connection strings + client configs for teammates
    ├── src/tc_mcp/
    │   ├── server.py                    # create_server() wires everything; main() picks stdio or http
    │   ├── config.py                    # env vars, ranking weights, suite rules, limits
    │   ├── models.py                    # TestCase, TestCaseDraft, TestCaseChanges, TestFilter, enums
    │   ├── repository.py                # load, validate, normalize, index, overlay merge, auto-reload
    │   ├── resolver.py                  # module aliases + did-you-mean
    │   ├── ranking.py                   # score + feature diversity
    │   ├── validation.py                # draft -> record + lint rules (shared by validate/add/update)
    │   ├── tools/
    │   │   ├── common.py                # response envelope, limits, caching
    │   │   ├── discovery.py             # 1-3
    │   │   ├── search.py                # 4-8
    │   │   ├── planning.py              # 9-12
    │   │   ├── quality.py               # 13-15
    │   │   ├── authoring.py             # 16-18 (write tools hidden unless writes are allowed)
    │   │   └── export.py                # 19-21
    │   ├── resources.py
    │   └── prompts.py
    ├── exports/                         # gitignored
    └── tests/
        ├── conftest.py                  # in-memory FastMCP Client fixtures, temp overlay
        ├── test_repository.py
        ├── test_tools_read.py
        └── test_tools_write.py
```

---

### 9. Sharing with other QA and devs

Three options. Start with A, move to B to share it, and use C only if a whole team uses it every day.

**A. Local stdio (while building, or for anyone who has the repo cloned)**
```bash
claude mcp add tc-mcp -- uv run --directory /abs/path/chapter_14_MCP_Create_VIBE/testcase_creator_mcp tc-mcp
```
Claude Desktop and Cursor use an `mcpServers` block. VS Code uses `.vscode/mcp.json` with a `servers` key:
```json
{
  "mcpServers": {
    "tc-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "/abs/path/chapter_14_MCP_Create_VIBE/testcase_creator_mcp", "tc-mcp"],
      "env": { "TC_MCP_ALLOW_WRITE": "false" }
    }
  }
}
```

**B. `uvx` from git (recommended for sharing: nothing to clone)**
```bash
claude mcp add tc-mcp -- uvx --from "git+https://github.com/PramodDutta/AITesterBlueprint4x#subdirectory=chapter_14_MCP_Create_VIBE/testcase_creator_mcp" tc-mcp
```
This only works if the CSV is bundled into the package at build time (hatch `force-include`). `TC_MCP_DATA_PATH` can still override it. Each person gets their own overlay.

**C. Hosted HTTP (one server, shared data and shared writes)**
```bash
TC_MCP_TRANSPORT=http TC_MCP_PORT=8000 TC_MCP_AUTH_TOKEN=... tc-mcp          # on a VM or in Docker
claude mcp add --transport http tc-mcp https://tc-mcp.<your-domain>/mcp --header "Authorization: Bearer <token>"
```
- Clients that only support stdio can connect through a stdio-to-HTTP bridge such as `fastmcp-remote`.
- Concurrent writes need SQLite instead of the CSV overlay. This is the only option that requires that change.

**Access profiles:** devs get the read-only setup (the default). QA leads who write tests get `TC_MCP_ALLOW_WRITE=true`.

---

### 10. Phased build plan

| Phase | Scope | Done when |
|---|---|---|
| **0. Setup** | `uv init`, `pyproject.toml` (fastmcp pin, `tc-mcp` script), `config.py`, one `ping` tool | The MCP Inspector (`npx @modelcontextprotocol/inspector`) connects and lists `ping` |
| **1. Data layer** | `models.py`, `repository.py`, `resolver.py`: load, validate, fix labels, split steps, extract features, flag duplicates, scenario ids | Unit tests confirm 5,000 rows, 17 modules, 72 features, 1,520 scenarios, 466 flagged duplicates, 4,585 live, no `a` label |
| **2. MVP read tools** | Tools 1, 2, 4, 5, 7 + `ranking.py` + resources | In Claude Code, "top 5 Highest tests for Reports on Safari" and "all High+ Negative tests for SDK, max 10" return correct results |
| **3. Planning + quality** | Tools 3, 6, 8 to 14 | `build_test_suite("smoke", "all")` returns at most 72 tests covering every feature, and the gap report matches hand counts |
| **4. Authoring + export** | Tools 15 to 20, the overlay, write gating, prompts | A new test goes through draft → validate → dry run → add and comes back as `VWO-6001` from `get_test_case`. With writes off, the tool is not listed |
| **5. Share** | README, client snippets, CSV bundled for `uvx`, optional HTTP + auth + SQLite overlay, tool 21 as a stretch goal | A teammate on a clean machine installs it with one command and runs the 10 golden questions |

---

### 11. Testing and verification

1. **Unit tests (pytest + FastMCP's in-memory `Client`, no subprocess):** call every tool and check results against numbers computed independently from the CSV. Examples: Highest = 396, Reports = 333, unfiltered search `total_matched` = 4,585.
2. **Edge cases:** an unknown module, `limit=0` and `limit=1000`, `min_priority` above `max_priority`, an empty result, calling a write tool while writes are off, adding a duplicate, a malformed step string, an unknown issue key.
3. **Golden questions (tool-selection eval):** 10 plain-English questions run through Claude Code, each checking that the right tool was picked with the right arguments. Examples: "what should I run first for Heatmaps?" → `get_top_tests_for_module`, and "how many Security tests per module?" → `get_test_stats`. This ties into chapter 19 (LLM Eval).
4. **Performance:** startup load under 1 s, every tool call under 100 ms on 5k rows.
5. **Contract check:** every list response contains the envelope fields, and no response goes over the token limits in §7.

---

### 12. What we are NOT doing (and why)

- **No LLM calls inside the server.** The client's LLM writes the test cases, and the server supplies templates, examples and validation. This keeps TC MCP free, offline and repeatable, with no API keys to share.
- **No separate `get_by_priority` or `get_by_module` tools.** One `search_test_cases` with filters covers both. Tools with overlapping jobs confuse the LLM's tool choice.
- **No vector DB or embeddings.** Keyword search is enough for 5k templated rows. Revisit only if the golden questions show semantic misses.
- **No edits to the source CSV.** All changes go to the overlay, so the original is always recoverable and diffs stay readable.
- **No direct Jira push in v1.** `export_test_cases(format="jira_csv")` covers the handoff, and an Atlassian MCP can push to Jira if needed.
- **No pandas.** stdlib `csv` and Pydantic are enough, and teammates' installs stay light.

---

### 13. Open questions

1. **"Maximum and minimum limitations":** read here as result-count limits (`limit`, `min_tests`, `max_tests`) plus a priority range (`min_priority`, `max_priority`). If it means something else (e.g. only Boundary tests), that is already a `test_type` filter. Please confirm.
2. **Write access:** should shared users be able to add and edit tests, or should the shared build be read-only?
3. **Sharing target:** a few people (option B) or a whole team on one hosted server (option C)?
4. **Source of truth long term:** will this CSV stay static, or be re-exported from Jira/Xray regularly? If re-exported, we add a `reload_data` tool and a version stamp.
5. **Effort defaults:** are 10 min per manual test and 1 min per automated test reasonable for VWO?
