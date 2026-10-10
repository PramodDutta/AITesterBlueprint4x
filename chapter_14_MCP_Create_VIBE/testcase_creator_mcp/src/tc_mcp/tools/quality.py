"""Quality tools: duplicates, coverage gaps, and linting a draft test."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from tc_mcp.models import TestCase, TestCaseDraft
from tc_mcp.repository import keeper_sort_key
from tc_mcp.resolver import resolve_module
from tc_mcp.tools.common import READ_ONLY, RepoProvider, ordered_counts
from tc_mcp.validation import validate_draft

RISK_TYPES = ("Security", "Negative", "Accessibility")


def register(mcp: FastMCP, repo: RepoProvider) -> None:
    @mcp.tool(annotations=READ_ONLY, tags={"quality"})
    def find_duplicate_tests(
        module: Annotated[str | None, Field(description="Limit to one module.")] = None,
        mode: Annotated[
            Literal["exact", "same_scenario"],
            Field(description="exact: same summary, browser and device (true duplicates). same_scenario: same summary on any browser/device (candidates to merge into one parameterized test)."),
        ] = "exact",
        limit: Annotated[int, Field(ge=1, le=100, description="Max groups to return.")] = 25,
    ) -> dict[str, Any]:
        """List groups of duplicate tests with a suggested keeper (Automated > Ready > Draft > Deprecated,
        then lowest key) and the redundant keys. Use for catalog cleanup."""
        r = repo()
        resolved = resolve_module(module, r.modules) if module else None
        if mode == "exact":
            groups = [g for g in r.exact_duplicate_groups if resolved is None or g[0].module == resolved]
        else:
            by_scenario: dict[str, list[TestCase]] = defaultdict(list)
            for tc in r.rows:
                if resolved is None or tc.module == resolved:
                    by_scenario[tc.scenario].append(tc)
            groups = [g for g in by_scenario.values() if len(g) > 1]
        groups.sort(key=lambda g: (-len(g), min(tc.key_number for tc in g)))

        results = []
        for group in groups[:limit]:
            keeper = min(group, key=keeper_sort_key)
            entry: dict[str, Any] = {
                "summary": keeper.summary,
                "module": keeper.module,
                "size": len(group),
                "keeper": keeper.key,
                "redundant_keys": [tc.key for tc in sorted(group, key=lambda tc: tc.key_number) if tc is not keeper][:20],
                "statuses": dict(Counter(tc.status for tc in group)),
            }
            if mode == "exact":
                entry.update(browser=keeper.browser, device=keeper.device)
            else:
                entry["browser_device_combinations"] = len({(tc.browser, tc.device) for tc in group})
                entry["suggestion"] = "Keep one test and run it as a browser/device matrix instead of separate copies."
            results.append(entry)
        return {
            "mode": mode,
            "module": resolved or "all",
            "groups": len(groups),
            "redundant_rows": sum(len(g) - 1 for g in groups),
            "returned": len(results),
            "results": results,
        }

    @mcp.tool(annotations=READ_ONLY, tags={"quality"})
    def find_coverage_gaps(
        module: Annotated[str | None, Field(description="Analyze one module in detail; omit for a catalog-wide summary.")] = None,
        max_items: Annotated[int, Field(ge=1, le=200, description="Cap on items per gap list.")] = 50,
    ) -> dict[str, Any]:
        """Find holes in live test coverage: feature x test type combinations with no tests (or only one),
        features with no Highest-priority test, features missing Security/Negative/Accessibility tests,
        features that only have Draft tests, and browser x device combinations with no tests."""
        r = repo()
        modules = [resolve_module(module, r.modules)] if module else r.modules
        live = [tc for tc in r.rows if tc.is_live and tc.module in modules]
        by_feature: dict[tuple[str, str], list[TestCase]] = defaultdict(list)
        for tc in live:
            by_feature[(tc.module, tc.feature)].append(tc)

        missing, thin, no_highest, missing_risk, draft_only = [], [], [], [], []
        for m in modules:
            for feature in r.features_by_module[m]:
                tests = by_feature.get((m, feature), [])
                label = f"{m}: {feature}"
                types = Counter(tc.test_type for tc in tests)
                for test_type in r.test_types:
                    if types[test_type] == 0:
                        missing.append({"feature": label, "test_type": test_type})
                    elif types[test_type] == 1:
                        thin.append({"feature": label, "test_type": test_type, "tests": 1})
                if not any(tc.priority == "Highest" for tc in tests):
                    no_highest.append(label)
                lacking = [t for t in RISK_TYPES if types[t] == 0]
                if lacking:
                    missing_risk.append({"feature": label, "missing": lacking})
                if tests and all(tc.status == "Draft" for tc in tests):
                    draft_only.append(label)

        empty_cells = []
        for m in modules:
            combos = {(tc.browser, tc.device) for tc in live if tc.module == m}
            for browser in r.browsers:
                for device in r.devices:
                    if (browser, device) not in combos:
                        empty_cells.append(f"{m}: {browser} / {device}")

        def capped(items: list) -> dict[str, Any]:
            return {"count": len(items), "items": items[:max_items], "truncated": len(items) > max_items}

        return {
            "scope": modules[0] if module else "all modules",
            "live_tests": len(live),
            "features_analyzed": sum(len(r.features_by_module[m]) for m in modules),
            "missing_feature_x_type": capped(missing),
            "thin_feature_x_type": capped(thin),
            "features_without_highest_priority": capped(no_highest),
            "features_missing_risk_types": capped(missing_risk),
            "features_with_only_drafts": capped(draft_only),
            "empty_browser_device_cells": capped(empty_cells),
            "live_by_test_type": ordered_counts(live, "test_type"),
        }

    @mcp.tool(annotations=READ_ONLY, tags={"quality", "authoring"})
    def validate_test_case(
        test_case: Annotated[TestCaseDraft, Field(description="The draft test to check.")],
        allow_duplicates: Annotated[bool, Field(description="Treat an exact duplicate as a warning instead of an error.")] = False,
    ) -> dict[str, Any]:
        """Lint a draft test before saving: summary pattern, module/type consistency, step format,
        vague or over-shared expected results, unknown browser/device, and duplicates of existing tests.
        Returns valid, errors, warnings, possible_duplicates and the normalized record."""
        return validate_draft(test_case, repo(), allow_duplicates=allow_duplicates).report()
