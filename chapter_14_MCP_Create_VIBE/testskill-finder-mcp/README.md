# TestSkill Finder MCP

![TestSkill Finder MCP: 100 QA skills, find the right skill, use it from any LLM](../assets/testskill-finder-hero.png)

An MCP server, built on FastMCP 4.1, that lets any LLM search, read, chain and use a library of **100 QA agent skills**. It covers the 7 STLC phases plus Playwright, Selenium, Cypress, API testing, performance, security, LLM evaluation, AI agents, MCP and automation.

The [`skills/`](skills/) folder is the source of truth. Every skill is a folder with a `SKILL.md` (YAML frontmatter plus instructions). The server reloads automatically whenever a file in that folder changes, and every skill is also exposed as an MCP prompt and a resource.

- **36 skills** are synced from [PramodDutta/skillmasterclass](https://github.com/PramodDutta/skillmasterclass/tree/main/skillmasterclass/skills) (see [`skills/.upstream.json`](skills/.upstream.json) for the commit).
- **64 skills** were added here in the same format.
- The full list is in [`skills/CATALOG.md`](skills/CATALOG.md).

## Connect

**MCP Inspector (HTTP):**

```bash
cd chapter_14_MCP_Create_VIBE/testskill-finder-mcp
uv run testskill-finder-mcp --transport http      # http://127.0.0.1:8110/mcp
npx @modelcontextprotocol/inspector --transport http --server-url http://127.0.0.1:8110/mcp
```

**MCP Inspector (stdio):**

```bash
npx @modelcontextprotocol/inspector uv run --directory /ABS/PATH/chapter_14_MCP_Create_VIBE/testskill-finder-mcp testskill-finder-mcp
```

**Claude Code:**

```bash
claude mcp add testskill-finder -- uv run --directory /ABS/PATH/chapter_14_MCP_Create_VIBE/testskill-finder-mcp testskill-finder-mcp
# or, with the HTTP server running:
claude mcp add --transport http testskill-finder http://127.0.0.1:8110/mcp
```

**VS Code (`.vscode/mcp.json`):**

```json
{ "servers": { "testskill-finder": { "type": "http", "url": "http://127.0.0.1:8110/mcp" } } }
```

**Claude Desktop or Cursor (`mcpServers`):**

```json
{
  "mcpServers": {
    "testskill-finder": {
      "command": "uv",
      "args": ["run", "--directory", "/ABS/PATH/chapter_14_MCP_Create_VIBE/testskill-finder-mcp", "testskill-finder-mcp"]
    }
  }
}
```

**No clone needed (the 100 skills are bundled in the package):**

```bash
claude mcp add testskill-finder -- uvx --from "git+https://github.com/PramodDutta/AITesterBlueprint4x#subdirectory=chapter_14_MCP_Create_VIBE/testskill-finder-mcp" testskill-finder-mcp
```

HTTP mode runs stateless, so it works behind proxies and tunnels. Opening the URL in a browser shows a "how to connect" page instead of a JSON error. To share it beyond your machine, set `TSF_AUTH_TOKEN` and add `--header "Authorization: Bearer <token>"` on the client.

## Tools (15)

| Group | Tool | What it does |
|---|---|---|
| Discover | `list_categories` | The 7 STLC phases in order, plus every pack, with counts and skill names |
| | `list_skills` | Browse skills, filtered by phase/pack, kind or source |
| | `get_catalog_stats` | Totals by kind, category and source, plus the upstream commit and sync time |
| Find | `search_skills` | Keyword search with stemming and synonyms (`pw` = playwright, creator ~ writer ~ generator, bug ~ defect) |
| | `find_skill_for_task` | Plain-English task in, best skills out, matched against each skill's trigger phrases |
| | `get_skill` | One skill: metadata, triggers, when to use, workflow, output shape, guardrails, files. Accepts typos ("Did you mean ...") |
| | `get_skill_file` | Read a supporting file (template, checklist, script, Copilot prompt). Path traversal is blocked |
| | `get_related_skills` | STLC hand-offs before and after, same-pack siblings, look-alikes in other packs |
| | `compare_skills` | 2-5 skills side by side |
| Workflow | `suggest_skill_chain` | An ordered chain of skills across the STLC for a bigger goal, plus pack tooling |
| | `get_stlc_pipeline` | The STLC as a pipeline with the skills for each phase |
| | `export_skill` | Output as a Claude Code skill folder, GitHub Copilot prompt file, Cursor rule or Markdown |
| Quality | `validate_skills` | Check one or all skills against the catalog format |
| Write* | `create_skill` | Create a new skill in the house format, in the right folder (`dry_run` first) |
| | `sync_skills_from_github` | Pull the upstream catalog. Adds and updates upstream files only; never touches local skills |

\* Write tools only appear when the server starts with `--allow-write` or `TSF_ALLOW_WRITE=true`.

**Prompts (103):**
- `use_skill`, `find_skill` and `plan_with_skills`.
- **One prompt per skill**, named after the skill. In Claude Code, `/mcp__testskill-finder__test-plan-generator JIRA-123` loads that skill's instructions plus your task.

**Resources:**
- `skills://catalog`, `skills://catalog.md`, `skills://categories`, `skills://stlc-pipeline` and `skills://stats`.
- `skill://{name}` for any SKILL.md.
- `skill://{name}/files/{path}` for its supporting files.

Try asking:
- "Find a skill for Playwright API testing"
- "Which skill writes a test plan from a Jira ticket?"
- "I need a test strategy and a way to report bugs"
- "Plan the skills to take a story to automated Cypress tests"
- "Show me the LLM evaluation and MCP skills"

## The catalog

![STLC Skill Map: the 7 phases the lifecycle skills follow](../assets/stlc-skill-map.png)

| Category | Skills | From upstream | Examples |
|---|---|---|---|
| 1 Requirement Analysis | 3 | 1 | `jira-requirement-analyzer`, `acceptance-criteria-writer` |
| 2 Test Planning | 5 | 1 | `test-plan-generator`, `test-strategy-designer`, `test-estimation-calculator` |
| 3 Test Design | 6 | 2 | `test-scenario-designer`, `bdd-scenario-writer`, `test-technique-designer` |
| 4 Test Case Development | 4 | 2 | `test-case-writer`, `test-data-generator`, `test-case-reviewer` |
| 5 Test Execution | 5 | 3 | `automation-script-generator`, `regression-suite-selector`, `ci-failure-analyzer` |
| 6 Defect Management | 5 | 3 | `bug-reporter`, `bug-triage-assistant`, `rca-analyzer` |
| 7 Test Closure | 4 | 2 | `test-closure-reporter`, `release-readiness-checker` |
| Playwright | 11 | 11 | `pw-api-tester`, `pw-locator-fixer`, `pw-flaky-debugger` |
| Selenium | 11 | 11 | `se-wait-fixer`, `se-page-object-builder`, `se-grid-configurator` |
| Cypress | 8 | 0 | `cy-test-generator`, `cy-intercept-mocker`, `cy-component-tester` |
| API Testing | 6 | 0 | `restassured-api-tester`, `postman-collection-builder`, `api-contract-tester` |
| Performance | 6 | 0 | `k6-load-test-generator`, `jmeter-test-plan-builder`, `performance-results-analyzer` |
| Security | 6 | 0 | `owasp-web-test-designer`, `owasp-api-security-tester`, `zap-dast-configurator` |
| LLM Evaluation | 7 | 0 | `deepeval-test-writer`, `rag-evaluation-designer`, `llm-judge-rubric-designer` |
| AI Agents | 5 | 0 | `agent-test-designer`, `agent-trajectory-evaluator`, `prompt-injection-tester` |
| MCP | 5 | 0 | `mcp-server-tester`, `mcp-tool-designer`, `mcp-security-reviewer` |
| Automation | 3 | 0 | `automation-framework-architect`, `flaky-test-quarantine-manager`, `appium-mobile-test-generator` |
| **Total** | **100** | **36** | |

Every skill uses the same format:
- **Frontmatter:** `name` (same as the folder), a `description` with "Use when ..." trigger phrases, `license`, and `metadata` with author, version, and exactly one of `stlc-phase` or `pack`.
- **Body:** When to use, Workflow, Output shape and Guardrails sections. Lifecycle skills end their workflow at a human review gate.

## How search works

1. **Tokenize and stem:** "creator", "generator" and "writer" become `creat`, `generat` and `writ`.
2. **Expand synonyms** at weight 0.6: `pw` -> playwright, `k6` -> performance, bug <-> defect, locator <-> selector.
3. **Score** each skill by term weight x IDF x field weight. The fields are name 6, title 4, trigger phrases 3, category 3, description 2, when-to-use 1.5 and body 0.5.
4. **Scale by coverage** of the words you typed, with a bonus when every word is in the skill's name.
5. `find_skill_for_task` also compares your sentence with each skill's quoted trigger phrases.

These golden queries are pinned in [`tests/test_search.py`](tests/test_search.py), along with 11 more:

| Query | Top result |
|---|---|
| Playwright API | `pw-api-tester` |
| test case creator | `test-case-writer` |
| test plan creator | `test-plan-generator` |
| test strategy | `test-strategy-designer` |
| k6 load test | `k6-load-test-generator` |
| deepeval | `deepeval-test-writer` |

## Keep the folder up to date

```bash
uv run tsf-mcp sync              # pull upstream skills (local skills are never touched)
uv run tsf-mcp validate          # check every SKILL.md against the format
uv run tsf-mcp catalog           # regenerate skills/CATALOG.md
```

To add a skill, you have two options:
- Create a folder with a `SKILL.md` under the right phase or `framework-packs/<pack>-pack/`, then run `tsf-mcp validate`.
- Call `create_skill` on a server started with `--allow-write`.

Sync writes only files under the upstream path. It refuses paths that escape the folder and files over 1 MB, and records each synced file in `.upstream.json`. That record is how every skill is labelled `upstream` or `local`. Downloaded scripts are stored as text and never run.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `TSF_SKILLS_DIR` | `./skills` (or the bundled copy) | Point at another skills folder |
| `TSF_ALLOW_WRITE` | `false` | Enable `create_skill` and `sync_skills_from_github` |
| `TSF_TRANSPORT`, `TSF_HOST`, `TSF_PORT` | `stdio`, `127.0.0.1`, `8110` | Same as `--transport`, `--host`, `--port` |
| `TSF_AUTH_TOKEN` | unset | Bearer token required in HTTP mode |
| `GITHUB_TOKEN` | unset | Optional, raises the GitHub API rate limit for sync |

## Develop

```bash
uv sync
uv run pytest -q    # 42 tests: catalog integrity, golden searches, every tool, resources, prompts, sync with a mocked GitHub
```

Layout: `src/tsf_mcp/` holds:
- `catalog.py`: parse SKILL.md files, auto-reload
- `text.py` and `search.py`: stemming, synonyms, scoring
- `validation.py`
- `sync.py`: GitHub download
- `tools/`: finder, workflow, authoring
- `resources.py`, `prompts.py`, `landing.py`, `server.py`
