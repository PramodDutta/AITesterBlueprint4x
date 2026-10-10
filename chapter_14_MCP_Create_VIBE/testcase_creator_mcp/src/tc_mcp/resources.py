"""Read-only resources a client can attach as context."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ResourceError

from tc_mcp.models import CSV_COLUMNS, PRIORITY_ORDER, STATUS_ORDER
from tc_mcp.tools.common import RepoProvider, ordered_counts


def register(mcp: FastMCP, repo: RepoProvider) -> None:
    @mcp.resource("tc://schema", name="schema", mime_type="application/json")
    def schema() -> dict[str, Any]:
        """Column definitions, allowed values, and the summary and step formats of the catalog."""
        r = repo()
        return {
            "columns": list(CSV_COLUMNS),
            "derived_fields": {
                "feature": "Parsed from Description ('...the <feature> in the <Module> module...').",
                "duplicate_of": "Key of the kept test when this row repeats its summary, browser and device.",
            },
            "allowed_values": {
                "priority": list(PRIORITY_ORDER),
                "status": list(STATUS_ORDER),
                "test_type": r.test_types,
                "browser": r.browsers,
                "device": r.devices,
                "module": r.modules,
            },
            "formats": {
                "summary": "[Module] Test Type: action feature",
                "steps": "'1. step | 2. step | ...' in the CSV; a list of strings in tool results",
                "issue_key": f"{r.key_prefix}-<number>",
            },
        }

    @mcp.resource("tc://modules", name="modules", mime_type="application/json")
    def modules() -> dict[str, Any]:
        """Modules with their features and live test counts."""
        r = repo()
        live = r.live_rows()
        counts = ordered_counts(live, "module")
        return {m: {"live_tests": counts.get(m, 0), "features": r.features_by_module[m]} for m in r.modules}

    @mcp.resource("tc://stats/summary", name="stats_summary", mime_type="application/json")
    def stats_summary() -> dict[str, Any]:
        """Headline numbers for the whole catalog."""
        r = repo()
        live = r.live_rows()
        return {
            "total_tests": len(r.rows),
            "live_tests": len(live),
            "added_or_edited_via_tc_mcp": r.overlay_count,
            "modules": len(r.modules),
            "features": sum(len(f) for f in r.features_by_module.values()),
            "unique_scenarios": r.scenario_count,
            "exact_duplicate_rows": sum(1 for tc in r.rows if tc.duplicate_of),
            "by_priority": ordered_counts(r.rows, "priority"),
            "by_status": ordered_counts(r.rows, "status"),
            "by_test_type": ordered_counts(r.rows, "test_type"),
        }

    @mcp.resource("tc://test/{issue_key}", name="test_case", mime_type="application/json")
    def test_case(issue_key: str) -> dict[str, Any]:
        """One test case with full detail, e.g. tc://test/VWO-1001."""
        tc = repo().get(issue_key)
        if tc is None:
            raise ResourceError(f"Unknown issue key {issue_key!r}.")
        return tc.full()
