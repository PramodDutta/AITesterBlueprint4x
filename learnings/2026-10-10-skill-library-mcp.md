# Turning a folder of agent skills into a searchable MCP server

**Problem:** Serve 100 QA agent skills (SKILL.md files, 36 synced from GitHub and 64 new) over MCP. "Test case creator" must find `test-case-writer`, and "Playwright API" must find `pw-api-tester`.

## Approach

1. **Read the source format before writing anything.** Print the frontmatter of every upstream SKILL.md, then read two full examples. That gives the contract: `name` = folder, a `description` with "Use when" and quoted trigger phrases, `metadata` with exactly one of `stlc-phase` or `pack`, and four sections (When to use, Workflow, Output shape, Guardrails).
2. **Download through the product's own code.** Write `sync.py` first and run it to fill `skills/`. The first real sync tests the feature, and its manifest (`.upstream.json`) is how each skill is later labelled `upstream` or `local`.
3. **Parallelize the writing, not the design.** Write one strict spec file (format, folder table, banned characters, a self-check command). Give 5 writer agents about 12-15 skills each. Build the server while they write.
4. **Turn the goal's examples into tests.** Each example query in the request becomes a golden test (`query -> expected top skill`). Tune the search until they pass, then keep them as regression tests.
5. **Search = stem + synonyms + field weights.** A Porter-lite stemmer turns creator, generator and writer into `creat`, `generat` and `writ`. Synonym groups, stemmed with the same function, link them at weight 0.6. Name and trigger matches outweigh body matches, and the score is scaled by how many of the user's words matched.
6. **Validate with the server's own validator,** in tests and from the command line (`tsf-mcp validate`). One check covers all 100 skills, whoever wrote them.

## Judgment calls

- **No embeddings.** For 100 short, structured documents, stems, synonyms and field weights beat semantic search on the queries users actually type, and stay explainable ("matched in name, triggers").
- **One prompt per skill (103 in total), not one generic prompt.** It makes every skill a slash command. Prompts are registered at runtime, so the module must not use `from __future__ import annotations` (Pydantic can't resolve string annotations on runtime-built functions).
- **Sync never deletes and never executes.** It writes only under the upstream path, refuses `..` and absolute paths, and skips files over 1 MB. Downloaded scripts are stored as text.
- **Don't rename folders while writers are using them.** A pack-to-folder map (`ai-agents` -> `ai-agent-pack`) fixed the validator warning instead.
- **Accept upstream variance instead of editing upstream files.** Headings are matched by prefix ("Workflow (follow in order)"), and `### 1.` steps count as workflow steps. Upstream files stay byte-identical, so the next sync shows no diff.
- **When a tool fails, read the error before retrying.** The image model in the Codex config was not allowed on a ChatGPT login, so the one retry used a model from the local cache. "Address already in use" was confirmed with `lsof` before the default port was moved.

## Reusable rule

Make the request's own examples into failing tests first, and have parallel workers share one written spec and one validator. Then "done" is something you can run, not an opinion.
