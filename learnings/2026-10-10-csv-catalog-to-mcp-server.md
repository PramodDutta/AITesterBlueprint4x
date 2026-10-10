# Turning a CSV test catalog into a shareable MCP server

**Problem:** Expose a 5,000-row test case CSV as MCP tools (FastMCP) that QA and devs can query, rank, plan from, write to, and export, and that teammates can install with one command.

## Approach

1. **Profile the data before designing tools.** Count unique values per column, empty cells, duplicates, step format, and bytes per row. Here that showed 466 exact duplicate rows, only 1,520 unique scenarios behind 5,000 rows, a broken label (`A/B Testing` became `a`), and a doubled `regression` label. Every tool decision came from those numbers.
2. **Check the library version at the source.** Run `pip index versions <pkg>`. A web search said FastMCP v4 was beta, but PyPI showed 4.1.0 as stable. The resolver then failed on Python 3.15, so `requires-python` is capped at `<3.15`.
3. **Probe the API with a toy server before writing real tools.** One in-memory script checked tools, Pydantic filter models, `Literal` enums in the schema, `ToolError`, resource templates, prompts, `disable(tags=...)`, and the `Client` result shape. That took five minutes and saved rewriting 21 tools.
4. **Layer the code.** config, models, a repository (load, normalize, index, overlay), a resolver (aliases and did-you-mean), ranking, validation, then thin tool modules with a `register(mcp, repo)` function each. `create_server(repo, allow_write=...)` makes tests trivial: in-memory `Client`, temp overlay.
5. **Verify in three rings.** pytest against independently computed counts, a real stdio and HTTP client, then the official MCP Inspector CLI (`npx @modelcontextprotocol/inspector --cli <url> --transport http --method tools/list`).

## Judgment calls (what was NOT done)

- **No LLM calls inside the server.** The client's model writes the tests. The server supplies templates, real examples, and validation, so it is free, offline, and deterministic.
- **No separate `get_by_priority` or `get_by_module` tools.** One filter tool covers both. Overlapping tools make the model pick the wrong one.
- **Write tools are not "registered but refusing".** They are hidden with `mcp.disable(tags={"write"})`, so a read-only user's model never sees them. Writes also default to `dry_run=true`.
- **The source CSV is never mutated.** Writes go to an overlay CSV (latest row wins) under a file lock, and the repository reloads when either file's mtime or size changes.
- **No pandas, no vector DB.** 5k rows fit in a list. Keyword scoring was enough for templated text.
- **"Top N" is not a plain sort.** A plain sort returned N browser variants of one scenario. Instead: keep the best variant per scenario, then a greedy pick with a per-feature penalty (8 points, smaller than one priority tier) so results spread across features without a Low test outranking a Highest one.

## Reusable rule

Profile the data and probe the framework with a throwaway script before designing tools. Duplicates, skew, and version drift decide the design more than the feature list does.
