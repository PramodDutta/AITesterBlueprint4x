"""Helpers shared by every tool group."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from typing import Any

from tc_mcp import config
from tc_mcp.models import PRIORITY_ORDER, STATUS_ORDER, TEST_TYPE_ORDER, TestCase
from tc_mcp.repository import Repository

RepoProvider = Callable[[], Repository]

READ_ONLY = {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
WRITE_UPDATE = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}

DIMENSION_ORDER = {
    "priority": PRIORITY_ORDER,
    "status": STATUS_ORDER,
    "test_type": TEST_TYPE_ORDER,
}


def dimension_value(tc: TestCase, dimension: str) -> str:
    if dimension == "feature":
        return f"{tc.module}: {tc.feature}"
    return getattr(tc, dimension)


def ordered_counts(rows: Iterable[TestCase], dimension: str) -> dict[str, int]:
    counter = Counter(dimension_value(tc, dimension) for tc in rows)
    order = DIMENSION_ORDER.get(dimension)
    if order:
        known = [value for value in order if value in counter]
        extra = sorted(set(counter) - set(order))
        return {value: counter[value] for value in known + extra}
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def fit_limit(limit: int, detail: str) -> tuple[int, str | None]:
    if detail == "full" and limit > config.MAX_FULL_ROWS:
        return config.MAX_FULL_ROWS, f"limit lowered to {config.MAX_FULL_ROWS}: full detail is capped to protect the context window."
    return limit, None


def envelope(
    rows: list[TestCase],
    *,
    offset: int,
    limit: int,
    applied: dict[str, Any],
    detail: str = "compact",
    notes: list[str] | None = None,
) -> dict[str, Any]:
    page = rows[offset : offset + limit]
    next_offset = offset + limit if offset + limit < len(rows) else None
    payload: dict[str, Any] = {
        "total_matched": len(rows),
        "returned": len(page),
        "offset": offset,
        "next_offset": next_offset,
        "filters_applied": applied,
        "results": [tc.view(detail) for tc in page],
    }
    notes = [n for n in (notes or []) if n]
    if not rows:
        notes.append("No tests matched. Loosen a filter (module, priority range, test_type, browser, device) or call get_filter_options for valid values.")
    if notes:
        payload["notes"] = notes
    return payload


def cached(r: Repository, name: str, builder: Callable[[Repository], Any]) -> Any:
    """Memoize a derived index on the repository until the data files change."""
    signature_attr = f"_{name}_signature"
    if getattr(r, signature_attr, None) != r._signature:
        setattr(r, f"_{name}", builder(r))
        setattr(r, signature_attr, r._signature)
    return getattr(r, f"_{name}")
