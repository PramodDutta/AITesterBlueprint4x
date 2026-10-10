"""The data layer must match numbers computed independently from the CSV."""

from collections import Counter

import pytest
from fastmcp.exceptions import ToolError

from tc_mcp.models import TestFilter
from tc_mcp.repository import generate_labels, normalize_labels, parse_steps
from tc_mcp.resolver import resolve_module


def test_catalog_shape(repo):
    assert len(repo.rows) == 5000
    assert repo.load_warnings == []
    assert len(repo.modules) == 17
    assert sum(len(f) for f in repo.features_by_module.values()) == 72
    assert repo.scenario_count == 1520
    assert len(repo.live_rows()) == 4585


def test_priority_and_status_counts(repo):
    assert Counter(tc.priority for tc in repo.rows) == {"Medium": 2198, "High": 1546, "Low": 860, "Highest": 396}
    assert Counter(tc.status for tc in repo.rows)["Deprecated"] == 415


def test_duplicates_flagged(repo):
    assert sum(1 for tc in repo.rows if tc.duplicate_of) == 466


def test_labels_are_repaired(repo):
    ab = [tc for tc in repo.rows if tc.module == "A/B Testing"]
    assert all(tc.labels[0] == "ab-testing" for tc in ab)
    assert not any("a" in tc.labels for tc in repo.rows)
    assert all(tc.labels.count("regression") == 1 for tc in repo.rows)
    assert normalize_labels("a functional regression", "A/B Testing") == ["ab-testing", "functional", "regression"]
    assert generate_labels("SDK / Server-Side API", "UI/UX") == ["sdk", "ui-ux", "regression"]


def test_steps_and_features_parsed(repo):
    assert all(len(tc.steps) == 4 for tc in repo.rows)
    assert all(tc.feature != "unknown" for tc in repo.rows)
    assert parse_steps("1. Open it. | 2. Click Save | now. | 3. Check.") == ["Open it.", "Click Save | now.", "Check."]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("ab testing", "A/B Testing"), ("A/B", "A/B Testing"), ("sdk", "SDK / Server-Side API"), ("billing", "Account & Billing"), ("REPORTS", "Reports")],
)
def test_module_aliases(repo, raw, expected):
    assert resolve_module(raw, repo.modules) == expected


def test_unknown_module_suggests(repo):
    with pytest.raises(ToolError, match="Did you mean 'Reports'"):
        resolve_module("Reportz", repo.modules)


def test_filter_priority_range_and_loose_values(repo):
    rows, applied = repo.filter(TestFilter(module="reports", min_priority="High", browser="safari", device="ios"))
    assert rows and all(tc.priority in ("High", "Highest") and tc.browser == "Safari 19" and tc.device == "mobile (iOS)" for tc in rows)
    assert applied["module"] == ["Reports"]


def test_deprecated_hidden_unless_requested(repo):
    assert len(repo.filter(None)[0]) == 4585
    assert len(repo.filter(TestFilter(include_deprecated=True))[0]) == 5000
    assert len(repo.filter(TestFilter(status=["Deprecated"]))[0]) == 415
