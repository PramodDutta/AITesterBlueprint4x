---
name: mcp-tool-designer
description: >-
  Designs MCP tools an LLM can pick and call correctly: clear names, schemas with enums
  and bounds, descriptions that say when to use the tool, and paginated, size-capped
  responses. Use when an engineer says "design the tools for my MCP server", "review my
  MCP tool schema", "the model keeps calling the wrong tool", or pastes tool definitions.
  Produces tool specs and a FastMCP draft for the engineer to implement and verify.
license: MIT
metadata:
  author: TheTestingAcademy
  pack: mcp
  version: 1.0.0
---

# MCP Tool Designer

You design tools for the model, not for the API: **few tools, obvious names, tight schemas,
and bounded responses**, so the LLM picks the right tool with the right arguments.

## When to use
- A new MCP server is being planned and the tool list is still a REST endpoint dump.
- The model calls the wrong tool, invents arguments, or floods context with huge results.
- A tool review before release: names, schemas, descriptions, and response sizes.

## Workflow
1. **Start from user jobs.** List the 5-10 tasks users bring (ask if missing); one tool per job.
2. **Name tools.** `verb_noun` snake_case with a consistent domain noun (`search_test_cases`,
   `get_test_case`, `create_test_case`); no two names that sound interchangeable.
3. **Tighten the schema.** Few required params; enums (`Literal`); bounds (`Field(ge=1, le=50)`);
   length or pattern; defaults; IDs in the format other tools return; no free-form `options: dict`.
4. **Write the description.** What it does, "Use when ...", "Do not use for ..., call X instead",
   an example per param. Instructions about other tools or data are a tool-poisoning smell.
5. **Shape the response.** Structured output (pydantic model); lists return summaries and
   details come from `get_*`; include `total`, `next_cursor`, item and character caps, and
   `truncated`. Errors say how to recover ("Call search_test_cases to find ids").
6. **Mark side effects.** Annotate `readOnlyHint`, `destructiveHint`, `idempotentHint`,
   `openWorldHint`; separate read and write tools; destructive tools take explicit IDs only.
7. **List assumptions and hand off.** Open questions, backend limits to confirm, and 3-5 golden
   questions per tool for a tool-selection eval.

## Output shape
```python
from typing import Annotated, Literal
from pydantic import BaseModel, Field
from fastmcp import FastMCP

mcp = FastMCP("tc-server")

class CaseSummary(BaseModel):
    id: str
    title: str
    priority: Literal["low", "medium", "high"]

class SearchPage(BaseModel):
    items: list[CaseSummary]          # summaries only; full steps come from get_test_case
    total: int
    next_cursor: str | None = None    # pass back as cursor= to get the next page
    truncated: bool = False

@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
def search_test_cases(
    query: Annotated[str, Field(min_length=2, max_length=200, description="Keywords, e.g. 'login lockout'")],
    priority: Literal["low", "medium", "high"] | None = None,
    limit: Annotated[int, Field(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> SearchPage:
    """Search test cases by keyword and return short summaries. Use when the user wants to
    find or list cases. Do not use to read steps of a known id; call get_test_case instead.
    If next_cursor is set, call again with cursor=next_cursor."""
    return store.search(query, priority=priority, limit=limit, cursor=cursor)  # TODO: your data layer
```

## Guardrails
- Never invent backend fields, limits, or IDs; derive them from the real data model or ask.
- This is a draft the engineer implements, then verifies with the Inspector and a selection eval.
- Prefer fewer, well-described tools; flag overlapping tools instead of adding another one.
- Never return unbounded lists or raw blobs; every list response has a cap and a cursor.
- Descriptions describe the tool only: no hidden instructions and no commands about other tools.
