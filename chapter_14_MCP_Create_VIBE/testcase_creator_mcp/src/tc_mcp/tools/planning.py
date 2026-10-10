"""Execution planning tools: suites, browser x device coverage, automation candidates, effort."""

from __future__ import annotations

from collections import defaultdict
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from tc_mcp import config, ranking
from tc_mcp.models import PRIORITY_RANK, Priority, TestCase, TestFilter, TestType
from tc_mcp.resolver import resolve_many, resolve_module, resolve_modules
from tc_mcp.tools.common import READ_ONLY, RepoProvider, ordered_counts

MinutesManual = Annotated[float, Field(gt=0, le=480, description="Minutes to run one manual (not Automated) test.")]
MinutesAutomated = Annotated[float, Field(gt=0, le=480, description="Minutes to run one Automated test.")]


def compute_effort(rows: list[TestCase], minutes_manual: float, minutes_automated: float) -> dict[str, Any]:
    automated = sum(1 for tc in rows if tc.status == "Automated")
    manual = len(rows) - automated
    manual_minutes = manual * minutes_manual
    automated_minutes = automated * minutes_automated
    total = manual_minutes + automated_minutes
    return {
        "tests": len(rows),
        "manual_tests": manual,
        "automated_tests": automated,
        "manual_minutes": round(manual_minutes, 1),
        "automated_minutes": round(automated_minutes, 1),
        "total_minutes": round(total, 1),
        "total_hours": round(total / 60, 2),
        "assumptions": f"{minutes_manual:g} min per manual test, {minutes_automated:g} min per automated test",
    }


def register(mcp: FastMCP, repo: RepoProvider) -> None:
    @mcp.tool(annotations=READ_ONLY, tags={"planning"})
    def build_test_suite(
        suite_type: Annotated[Literal["smoke", "sanity", "regression"], Field(description="smoke: Highest, Functional/API/Security, 1 per feature. sanity: Highest+High, Functional/Negative/API, up to 2 per feature. regression: every live test, ranked.")],
        modules: Annotated[list[str] | None, Field(description="Modules to include; omit (or ['all']) for every module.")] = None,
        max_tests: Annotated[int, Field(ge=1, le=config.MAX_SUITE_TESTS, description="Upper bound on suite size (1-300).")] = 50,
        min_tests: Annotated[int, Field(ge=0, le=config.MAX_SUITE_TESTS, description="Lower bound. If too few tests match, rules are relaxed step by step and each relaxation is reported.")] = 0,
        browsers: Annotated[list[str] | None, Field(description="Only these browsers.")] = None,
        devices: Annotated[list[str] | None, Field(description="Only these devices.")] = None,
        include_drafts: Annotated[bool, Field(description="Allow Draft tests in the suite.")] = False,
        minutes_manual: MinutesManual = config.DEFAULT_MINUTES_MANUAL,
        minutes_automated: MinutesAutomated = config.DEFAULT_MINUTES_AUTOMATED,
    ) -> dict[str, Any]:
        """Build a ready-to-run smoke, sanity or regression suite, ranked and spread across features,
        bounded by min_tests/max_tests, with its makeup (module, priority, type, status) and an effort estimate.

        Skips Deprecated tests and exact duplicates. Returns every issue key plus details for the first 100.
        """
        if min_tests > max_tests:
            raise ToolError(f"min_tests ({min_tests}) is larger than max_tests ({max_tests}).")
        r = repo()
        rule = config.SUITE_RULES[suite_type]
        module_list = resolve_modules(modules, r.modules)
        browser_list = resolve_many(browsers, r.browsers, "browser")
        device_list = resolve_many(devices, r.devices, "device")

        state = {
            "priorities": list(rule.priorities),
            "test_types": list(rule.test_types) if rule.test_types else None,
            "per_feature": rule.per_feature,
            "drafts": include_drafts,
        }

        def pick() -> tuple[list[ranking.Ranked], dict[str, Any]]:
            flt = TestFilter(
                module=module_list,
                priority=state["priorities"],
                test_type=state["test_types"],
                browser=browser_list,
                device=device_list,
                status=["Ready", "Automated"] + (["Draft"] if state["drafts"] else []),
                include_duplicates=False,
            )
            rows, applied = r.filter(flt)
            # Greedy ranking is prefix-stable, so ranking up to the cap and slicing gives the same
            # top max_tests while also telling us how many tests qualified in total.
            picks = ranking.rank(
                rows,
                config.MAX_SUITE_TESTS,
                unique_scenarios=rule.unique_scenarios,
                per_feature=state["per_feature"],
                prefer_browser=None if browser_list else rule.preferred_browser,
                prefer_device=None if device_list else rule.preferred_device,
            )
            return picks, applied

        relax_steps = []
        if rule.relax_priorities:
            relax_steps.append((f"added priority {', '.join(rule.relax_priorities)}", lambda: state["priorities"].extend(rule.relax_priorities)))
        if rule.test_types:
            relax_steps.append(("allowed every test type", lambda: state.update(test_types=None)))
        if rule.per_feature is not None:
            relax_steps.append(("removed the per-feature cap", lambda: state.update(per_feature=None)))
        if not include_drafts:
            relax_steps.append(("included Draft tests", lambda: state.update(drafts=True)))

        picks, applied = pick()
        relaxations = []
        for label, apply in relax_steps:
            if len(picks) >= min_tests:
                break
            apply()
            relaxations.append(label)
            picks, applied = pick()
        qualified = len(picks)
        picks = picks[:max_tests]

        rows = [p.tc for p in picks]
        payload: dict[str, Any] = {
            "suite_type": suite_type,
            "size": len(picks),
            "qualified": qualified,
            "bounds": {"min_tests": min_tests, "max_tests": max_tests},
            "rules": {
                "priorities": state["priorities"],
                "test_types": state["test_types"] or "all",
                "per_feature_cap": state["per_feature"],
                "one_variant_per_scenario": rule.unique_scenarios,
                "preferred_browser_device": [rule.preferred_browser, rule.preferred_device] if rule.preferred_browser else None,
            },
            "filters_applied": applied,
            "relaxations": relaxations,
            "composition": {
                "by_module": ordered_counts(rows, "module"),
                "by_priority": ordered_counts(rows, "priority"),
                "by_test_type": ordered_counts(rows, "test_type"),
                "by_status": ordered_counts(rows, "status"),
            },
            "effort": compute_effort(rows, minutes_manual, minutes_automated),
            "issue_keys": [tc.key for tc in rows],
            "results": [p.as_dict() for p in picks[: config.MAX_COMPACT_ROWS]],
        }
        notes = []
        if qualified > len(picks):
            notes.append(f"{qualified} tests qualified{'' if qualified < config.MAX_SUITE_TESTS else ' (or more)'}; showing the top {len(picks)}. Raise max_tests to include more.")
        if len(picks) < min_tests:
            notes.append(f"Only {len(picks)} tests available even after relaxing rules; min_tests={min_tests} not reached.")
        if len(picks) > config.MAX_COMPACT_ROWS:
            notes.append(f"Details shown for the first {config.MAX_COMPACT_ROWS}; all keys are in issue_keys. Use export_test_cases(issue_keys=...) for a file.")
        if notes:
            payload["notes"] = notes
        return payload

    @mcp.tool(annotations=READ_ONLY, tags={"planning"})
    def get_browser_device_matrix(
        module: Annotated[str | None, Field(description="Limit to one module.")] = None,
        feature: Annotated[str | None, Field(description="Limit to one feature (within the module if given).")] = None,
        include_deprecated: bool = False,
    ) -> dict[str, Any]:
        """Show a browser x device grid of test counts and flag empty or thin cells.
        Use for cross-browser / cross-device coverage questions."""
        r = repo()
        flt = TestFilter(module=module, feature=feature, include_deprecated=include_deprecated)
        rows, applied = r.filter(flt)
        matrix = {b: dict.fromkeys(r.devices, 0) for b in r.browsers}
        for tc in rows:
            matrix[tc.browser][tc.device] += 1
        cells = [(b, d, n) for b, devices in matrix.items() for d, n in devices.items()]
        average = len(rows) / len(cells) if cells else 0
        return {
            "filters_applied": applied,
            "total": len(rows),
            "browsers": r.browsers,
            "devices": r.devices,
            "matrix": matrix,
            "browser_totals": {b: sum(v.values()) for b, v in matrix.items()},
            "device_totals": {d: sum(matrix[b][d] for b in r.browsers) for d in r.devices},
            "empty_cells": [f"{b} / {d}" for b, d, n in cells if n == 0],
            "thin_cells": [f"{b} / {d} ({n})" for b, d, n in cells if 0 < n < average * 0.5],
        }

    @mcp.tool(annotations=READ_ONLY, tags={"planning"})
    def get_automation_candidates(
        module: Annotated[str | None, Field(description="Limit to one module.")] = None,
        min_priority: Annotated[Priority, Field(description="Lowest priority to consider.")] = "High",
        test_types: Annotated[list[TestType] | None, Field(description="Only these test types.")] = None,
        limit: Annotated[int, Field(ge=1, le=100)] = config.DEFAULT_LIMIT,
    ) -> dict[str, Any]:
        """Rank Ready (not yet Automated) scenarios that are worth automating next. Scores favor high
        priority, automation-friendly types (API, Regression, Functional, Boundary), scenarios with many
        browser/device variants, and scenarios that already have an automated variant to reuse."""
        r = repo()
        resolved = resolve_module(module, r.modules) if module else None
        live = [tc for tc in r.rows if tc.is_live and tc.duplicate_of is None and (resolved is None or tc.module == resolved)]
        by_scenario: dict[str, list[TestCase]] = defaultdict(list)
        for tc in live:
            by_scenario[tc.scenario].append(tc)

        threshold = PRIORITY_RANK[min_priority]
        candidates = []
        for variants in by_scenario.values():
            ready = [tc for tc in variants if tc.status == "Ready" and tc.priority_rank >= threshold and (not test_types or tc.test_type in test_types)]
            if not ready:
                continue
            automated = sum(1 for tc in variants if tc.status == "Automated")
            best = max(ready, key=lambda tc: (tc.priority_rank, -tc.key_number))
            score = (
                config.PRIORITY_WEIGHT[best.priority]
                + config.AUTOMATION_TYPE_WEIGHT.get(best.test_type, 0)
                + 2 * min(len(ready), 4)
                + (4 if automated else 0)
            )
            reuse = f"{automated} variant(s) already automated, reuse that script" if automated else "no automated variant yet"
            candidates.append(
                {
                    "summary": best.summary,
                    "module": best.module,
                    "feature": best.feature,
                    "priority": best.priority,
                    "test_type": best.test_type,
                    "ready_keys": [tc.key for tc in sorted(ready, key=lambda tc: tc.key_number)][:10],
                    "ready_count": len(ready),
                    "already_automated_variants": automated,
                    "automation_score": score,
                    "reason": f"{best.priority} {best.test_type} test; {len(ready)} Ready variant(s) across browsers/devices; {reuse}",
                }
            )
        candidates.sort(key=lambda c: (-c["automation_score"], c["ready_keys"][0]))
        return {
            "module": resolved or "all",
            "min_priority": min_priority,
            "total_candidates": len(candidates),
            "returned": min(limit, len(candidates)),
            "results": candidates[:limit],
        }

    @mcp.tool(annotations=READ_ONLY, tags={"planning"})
    def estimate_execution_effort(
        issue_keys: Annotated[list[str] | None, Field(max_length=1000, description="Specific tests to estimate (up to 1000).")] = None,
        filters: Annotated[TestFilter | None, Field(description="Or estimate every test matching this filter.")] = None,
        minutes_manual: MinutesManual = config.DEFAULT_MINUTES_MANUAL,
        minutes_automated: MinutesAutomated = config.DEFAULT_MINUTES_AUTOMATED,
    ) -> dict[str, Any]:
        """Estimate how long a set of tests takes to execute: manual vs automated counts and minutes,
        totals in hours, broken down per module. Pass issue_keys or filters (one is required)."""
        if not issue_keys and filters is None:
            raise ToolError("Pass issue_keys or filters to say which tests to estimate.")
        r = repo()
        not_found: list[str] = []
        if issue_keys:
            rows = []
            for key in dict.fromkeys(issue_keys):
                tc = r.get(key)
                (rows.append(tc) if tc else not_found.append(key))
            applied: dict[str, Any] = {"issue_keys": len(issue_keys)}
        else:
            rows, applied = r.filter(filters)
        per_module: dict[str, list[TestCase]] = defaultdict(list)
        for tc in rows:
            per_module[tc.module].append(tc)
        payload: dict[str, Any] = {
            "filters_applied": applied,
            "total": compute_effort(rows, minutes_manual, minutes_automated),
            "by_module": {
                module: {k: v for k, v in compute_effort(items, minutes_manual, minutes_automated).items() if k != "assumptions"}
                for module, items in sorted(per_module.items(), key=lambda item: -len(item[1]))
            },
        }
        if not_found:
            payload["not_found"] = not_found
        return payload
