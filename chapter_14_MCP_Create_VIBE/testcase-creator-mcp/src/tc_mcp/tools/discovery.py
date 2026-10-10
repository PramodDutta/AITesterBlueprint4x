"""Discovery tools: help the client learn what is in the catalog."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from tc_mcp.models import PRIORITY_ORDER, STATUS_ORDER, TestFilter
from tc_mcp.resolver import MODULE_ALIASES
from tc_mcp.tools.common import READ_ONLY, RepoProvider, dimension_value, ordered_counts

Dimension = Literal["module", "feature", "priority", "test_type", "status", "browser", "device"]


def register(mcp: FastMCP, repo: RepoProvider) -> None:
    @mcp.tool(annotations=READ_ONLY, tags={"discovery"})
    def list_modules(
        include_features: Annotated[bool, Field(description="Include each module's features with test counts.")] = True,
    ) -> dict[str, Any]:
        """List every module (VWO product area) with total and live test counts, priority split, and features.

        Use first when the user names a module loosely or asks what areas are covered.
        Counts in by_priority exclude Deprecated tests.
        """
        r = repo()
        modules = []
        for module in r.modules:
            rows = [tc for tc in r.rows if tc.module == module]
            live = [tc for tc in rows if tc.is_live]
            entry: dict[str, Any] = {
                "module": module,
                "total": len(rows),
                "live": len(live),
                "by_priority": ordered_counts(live, "priority"),
            }
            if include_features:
                entry["features"] = [
                    {"feature": feature, "tests": r.feature_counts[module][feature]}
                    for feature in r.features_by_module[module]
                ]
            modules.append(entry)
        return {"module_count": len(modules), "modules": modules}

    @mcp.tool(annotations=READ_ONLY, tags={"discovery"})
    def get_filter_options() -> dict[str, Any]:
        """Return the exact allowed values for every filter field (priorities, test types, browsers,
        devices, statuses, modules, features, labels) plus the module aliases the server understands.

        Use when unsure which value to pass to search_test_cases or any other filter.
        """
        r = repo()
        return {
            "priorities_high_to_low": list(PRIORITY_ORDER),
            "test_types": r.test_types,
            "browsers": r.browsers,
            "devices": r.devices,
            "statuses": list(STATUS_ORDER),
            "modules": r.modules,
            "features_by_module": r.features_by_module,
            "labels": r.labels,
            "module_aliases": {alias: module for alias, module in sorted(MODULE_ALIASES.items())},
            "notes": [
                "Deprecated tests are excluded unless include_deprecated=true or status lists 'Deprecated'.",
                "Priority order for min_priority/max_priority: Low < Medium < High < Highest.",
            ],
        }

    @mcp.tool(annotations=READ_ONLY, tags={"discovery"})
    def get_test_stats(
        group_by: Annotated[
            list[Dimension],
            Field(min_length=1, max_length=2, description="One dimension for a count list, two for a pivot table, e.g. ['module', 'priority']."),
        ],
        filters: Annotated[TestFilter | None, Field(description="Optional filter applied before counting.")] = None,
    ) -> dict[str, Any]:
        """Count tests grouped by one or two dimensions (module, feature, priority, test_type, status,
        browser, device), after an optional filter.

        Use for 'how many', 'breakdown', 'distribution' questions. Not for listing tests (use search_test_cases).
        """
        r = repo()
        rows, applied = r.filter(filters)
        if len(group_by) == 1 or group_by[0] == group_by[1]:
            dimension = group_by[0]
            return {"total": len(rows), "filters_applied": applied, "group_by": [dimension], "counts": ordered_counts(rows, dimension)}

        row_dim, col_dim = group_by
        row_values = list(ordered_counts(rows, row_dim))
        col_values = list(ordered_counts(rows, col_dim))
        table = {row: dict.fromkeys(col_values, 0) for row in row_values}
        for tc in rows:
            table[dimension_value(tc, row_dim)][dimension_value(tc, col_dim)] += 1
        return {
            "total": len(rows),
            "filters_applied": applied,
            "group_by": [row_dim, col_dim],
            "columns": col_values,
            "table": table,
            "row_totals": {row: sum(cols.values()) for row, cols in table.items()},
            "column_totals": {col: sum(table[row][col] for row in row_values) for col in col_values},
        }
