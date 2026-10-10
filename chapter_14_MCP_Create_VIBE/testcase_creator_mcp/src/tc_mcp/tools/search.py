"""Find-and-fetch tools: lookups, filtered search, keyword search, top tests, similar tests."""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from tc_mcp import config, ranking
from tc_mcp.models import Priority, TestCase, TestFilter, TestType
from tc_mcp.repository import Repository
from tc_mcp.resolver import resolve_module
from tc_mcp.tools.common import READ_ONLY, RepoProvider, cached, envelope, fit_limit

STOPWORDS = {"the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "with", "is", "are", "be", "vwo", "test", "tests", "case", "cases", "check"}
KEYWORD_FIELDS = (
    ("summary", 3.0),
    ("feature", 3.0),
    ("module", 2.0),
    ("expected_result", 1.5),
    ("description", 1.0),
    ("steps", 1.0),
    ("preconditions", 0.5),
)

Detail = Annotated[Literal["compact", "full"], Field(description="'compact' (9 key fields) or 'full' (adds description, preconditions, steps, expected result, labels).")]
Limit = Annotated[int, Field(ge=1, le=config.MAX_COMPACT_ROWS, description="Rows per page (1-100; full detail is capped at 25).")]


def _stem(token: str) -> str:
    return token[:-1] if len(token) > 3 and token.endswith("s") else token


def tokenize(text: str) -> set[str]:
    return {_stem(t) for t in re.findall(r"[a-z0-9]+", text.casefold()) if len(t) > 1 and t not in STOPWORDS}


def _build_keyword_index(r: Repository) -> dict[str, dict[str, set[str]]]:
    return {
        tc.key: {
            "summary": tokenize(tc.summary),
            "feature": tokenize(tc.feature),
            "module": tokenize(tc.module),
            "expected_result": tokenize(tc.expected_result),
            "description": tokenize(tc.description),
            "steps": tokenize(" ".join(tc.steps)),
            "preconditions": tokenize(tc.preconditions),
        }
        for tc in r.rows
    }


def register(mcp: FastMCP, repo: RepoProvider) -> None:
    @mcp.tool(annotations=READ_ONLY, tags={"search"})
    def get_test_case(
        issue_keys: Annotated[
            list[str],
            Field(min_length=1, max_length=config.MAX_FULL_ROWS, description="1-25 issue keys, e.g. ['VWO-1001', 'VWO-1002']. A bare number like '1001' also works."),
        ],
    ) -> dict[str, Any]:
        """Get the full detail (description, preconditions, steps, expected result, labels) of specific
        test cases by issue key. Use when the user names keys or after a search to open a few results."""
        r = repo()
        found, not_found = [], []
        for key in issue_keys:
            tc = r.get(key)
            (found.append(tc.full()) if tc else not_found.append(key))
        result: dict[str, Any] = {"found": found}
        if not_found:
            result["not_found"] = not_found
        return result

    @mcp.tool(annotations=READ_ONLY, tags={"search"})
    def search_test_cases(
        filters: Annotated[TestFilter | None, Field(description="Any combination of module, feature, priority, min/max priority, test_type, browser, device, status, label.")] = None,
        sort_by: Annotated[Literal["priority", "key"], Field(description="'priority' (Highest first, then key) or 'key' (catalog order).")] = "priority",
        limit: Limit = config.DEFAULT_LIMIT,
        offset: Annotated[int, Field(ge=0, description="Skip this many rows; use next_offset from the previous page.")] = 0,
        detail: Detail = "compact",
    ) -> dict[str, Any]:
        """Filter test cases by exact fields: module, feature, priority (exact list or min/max range),
        test type, browser, device, status, label. Paginated with limit/offset; returns total_matched.

        Use for 'show me all High priority Negative tests in Reports' style requests.
        For 'what should I run first' use get_top_tests_for_module. For free text use search_by_keyword.
        Deprecated tests are hidden unless filters.include_deprecated=true.
        """
        r = repo()
        rows, applied = r.filter(filters)
        if sort_by == "priority":
            rows = sorted(rows, key=lambda tc: (-tc.priority_rank, tc.key_number))
        limit, note = fit_limit(limit, detail)
        return envelope(rows, offset=offset, limit=limit, applied=applied, detail=detail, notes=[note])

    @mcp.tool(annotations=READ_ONLY, tags={"search"})
    def search_by_keyword(
        query: Annotated[str, Field(min_length=2, description="Words to look for, e.g. 'rate limiting', 'SSO login', 'invoice download'.")],
        filters: Annotated[TestFilter | None, Field(description="Optional filter applied before matching.")] = None,
        unique_scenarios: Annotated[bool, Field(description="Collapse browser/device variants of the same scenario into one result.")] = True,
        limit: Annotated[int, Field(ge=1, le=50)] = config.DEFAULT_LIMIT,
    ) -> dict[str, Any]:
        """Free-text search across summary, feature, module, expected result, description, steps and
        preconditions. Results are ranked by relevance, then priority.

        Use when the user describes behavior in their own words instead of exact field values.
        """
        r = repo()
        terms = tokenize(query)
        if not terms:
            raise ToolError("The query has no searchable words. Use specific terms like 'webhook delivery' or 'seat limit'.")
        rows, applied = r.filter(filters)
        index = cached(r, "keyword_index", _build_keyword_index)
        phrase = query.strip().casefold()
        scored: list[tuple[float, TestCase, list[str]]] = []
        for tc in rows:
            fields = index[tc.key]
            score, matched_terms, matched_in = 0.0, set(), []
            for field, weight in KEYWORD_FIELDS:
                hits = terms & fields[field]
                if hits:
                    score += weight * len(hits)
                    matched_terms |= hits
                    matched_in.append(field)
            if not matched_terms:
                continue
            score *= len(matched_terms) / len(terms)
            if phrase in tc.summary.casefold() or phrase in tc.description.casefold():
                score += 4
            scored.append((round(score, 2), tc, matched_in))
        scored.sort(key=lambda item: (-item[0], -item[1].priority_rank, item[1].key_number))

        variants: dict[str, int] = {}
        if unique_scenarios:
            seen: dict[str, tuple[float, TestCase, list[str]]] = {}
            for item in scored:
                variants[item[1].scenario] = variants.get(item[1].scenario, 0) + 1
                seen.setdefault(item[1].scenario, item)
            scored = list(seen.values())

        results = []
        for score, tc, matched_in in scored[:limit]:
            row = tc.compact()
            row.update(match_score=score, matched_in=matched_in)
            if unique_scenarios:
                row["variants"] = variants[tc.scenario]
            results.append(row)
        payload: dict[str, Any] = {
            "query_terms": sorted(terms),
            "total_matched": len(scored),
            "returned": len(results),
            "filters_applied": applied,
            "results": results,
        }
        if not results:
            payload["notes"] = ["No matches. Try fewer or broader words, or check spelling with get_filter_options."]
        return payload

    @mcp.tool(annotations=READ_ONLY, tags={"search", "planning"})
    def get_top_tests_for_module(
        module: Annotated[str, Field(description="Module name, e.g. 'Reports', 'A/B Testing'. Aliases like 'ab', 'sdk' work.")],
        count: Annotated[int, Field(ge=1, le=50, description="How many tests to return (1-50).")] = 10,
        test_types: Annotated[list[TestType] | None, Field(description="Only these test types.")] = None,
        browser: Annotated[str | None, Field(description="Only this browser, e.g. 'Safari 19'.")] = None,
        device: Annotated[str | None, Field(description="Only this device, e.g. 'desktop'.")] = None,
        min_priority: Annotated[Priority | None, Field(description="Lowest priority to consider.")] = None,
        unique_scenarios: Annotated[bool, Field(description="One test per scenario (skip browser/device variants of a test already picked).")] = True,
        include_drafts: Annotated[bool, Field(description="Also consider Draft tests (normally skipped as not ready to execute).")] = False,
        detail: Detail = "compact",
    ) -> dict[str, Any]:
        """Answer 'which tests should I run first for <module>?'. Returns a ranked shortlist, each row with
        a score and a rank_reason. Score = priority + status + test type weight; picks are spread across
        the module's features so the list is not ten variants of one scenario.

        Skips Deprecated tests, exact duplicates, and (unless include_drafts) Draft tests.
        """
        r = repo()
        resolved = resolve_module(module, r.modules)
        statuses = ["Ready", "Automated"] + (["Draft"] if include_drafts else [])
        flt = TestFilter(
            module=resolved,
            test_type=test_types,
            browser=browser,
            device=device,
            min_priority=min_priority,
            status=statuses,
            include_duplicates=False,
        )
        rows, applied = r.filter(flt)
        count, note = fit_limit(count, detail)
        picks = ranking.rank(rows, count, unique_scenarios=unique_scenarios)
        payload: dict[str, Any] = {
            "module": resolved,
            "requested": count,
            "returned": len(picks),
            "candidates_considered": len(rows),
            "filters_applied": applied,
            "ranking": "score = priority (Highest 40, High 30, Medium 20, Low 10) + status (Ready 10, Automated 8, Draft 2) + type (Security/Functional 6 ... UI/UX/Accessibility 2), minus 8 per earlier pick from the same feature",
            "results": [p.as_dict(detail) for p in picks],
        }
        notes = [n for n in [note] if n]
        if len(picks) < count:
            notes.append(f"Only {len(picks)} tests matched. Loosen test_types/browser/device/min_priority or set unique_scenarios=false.")
        if notes:
            payload["notes"] = notes
        return payload

    @mcp.tool(annotations=READ_ONLY, tags={"search"})
    def get_similar_test_cases(
        issue_key: Annotated[str, Field(description="The reference test, e.g. 'VWO-1004'.")],
        limit: Annotated[int, Field(ge=1, le=50)] = 10,
        include_deprecated: bool = False,
    ) -> dict[str, Any]:
        """Find tests for the same module and feature as a given test: its browser/device variants and
        sibling tests of other types. Use for reviews, spotting overlap, or as examples when writing a new test."""
        r = repo()
        ref = r.get(issue_key)
        if ref is None:
            raise ToolError(f"Unknown issue key {issue_key!r}.")
        compared = ("test_type", "priority", "status", "browser", "device")
        scored = []
        for tc in r.rows:
            if tc.key == ref.key or tc.module != ref.module or tc.feature != ref.feature:
                continue
            if not include_deprecated and not tc.is_live:
                continue
            similarity = (
                4 * (tc.scenario == ref.scenario)
                + 3 * (tc.test_type == ref.test_type)
                + (tc.browser == ref.browser)
                + (tc.device == ref.device)
                + (tc.priority == ref.priority)
            )
            scored.append((similarity, tc))
        scored.sort(key=lambda item: (-item[0], -item[1].priority_rank, item[1].key_number))
        results = []
        for similarity, tc in scored[:limit]:
            row = tc.compact()
            row.update(
                similarity=similarity,
                relationship="variant of the same scenario" if tc.scenario == ref.scenario else "same feature",
                differs_in=[f for f in compared if getattr(tc, f) != getattr(ref, f)],
            )
            if tc.duplicate_of == ref.key or ref.duplicate_of == tc.key:
                row["relationship"] = "exact duplicate"
            results.append(row)
        return {"reference": ref.compact(), "total_matched": len(scored), "returned": len(results), "results": results}
