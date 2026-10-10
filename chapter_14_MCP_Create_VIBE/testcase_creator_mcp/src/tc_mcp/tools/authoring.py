"""Authoring tools: a template to write from, plus gated tools that add and edit tests."""

from __future__ import annotations

import dataclasses
from collections import Counter, defaultdict
from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from tc_mcp.models import Priority, TestCaseChanges, TestCaseDraft, TestType
from tc_mcp.repository import SUMMARY_RE, Repository
from tc_mcp.resolver import resolve_module, resolve_value
from tc_mcp.tools.common import READ_ONLY, WRITE, WRITE_UPDATE, RepoProvider, cached, ordered_counts
from tc_mcp.validation import default_description, validate_draft

TEMPLATE_RULES = [
    "Summary: '[Module] Test Type: action feature', e.g. '[Reports] Boundary: test limits of scheduled email'.",
    "Steps: a list of concrete actions without numbering; catalog tests use 4 (open module, navigate, act, observe).",
    "Expected result: one specific, observable outcome. Avoid 'works as expected'.",
    "Preconditions: setup items separated by '; '.",
    "New tests start as status 'Draft'.",
]


def _verb_by_type(r: Repository) -> dict[str, str]:
    """Most common action phrase per test type, e.g. Boundary -> 'test limits of'."""
    phrases: dict[str, Counter[str]] = defaultdict(Counter)
    for tc in r.rows:
        match = SUMMARY_RE.match(tc.summary)
        if match and tc.feature in match.group("action"):
            phrases[tc.test_type][match.group("action").replace(tc.feature, "").strip()] += 1
    return {test_type: counter.most_common(1)[0][0] for test_type, counter in phrases.items() if counter}


def register(mcp: FastMCP, repo: RepoProvider, writes_enabled: bool) -> None:
    @mcp.tool(annotations=READ_ONLY, tags={"authoring"})
    def get_test_case_template(
        module: Annotated[str, Field(description="Module the new test belongs to.")],
        test_type: TestType,
        feature: Annotated[str | None, Field(description="Feature inside the module; omit to see the module's features.")] = None,
        priority: Annotated[Priority | None, Field(description="Priority to pre-fill.")] = None,
        browser: Annotated[str | None, Field(description="Browser to pre-fill, e.g. 'Chrome 148'.")] = None,
        device: Annotated[str | None, Field(description="Device to pre-fill, e.g. 'desktop'.")] = None,
    ) -> dict[str, Any]:
        """Start writing a new test: returns a pre-filled skeleton in the catalog format, 3 real examples
        of the same module/feature/type to imitate, the feature's current coverage, and the writing rules.
        Fill the placeholders, then call validate_test_case and add_test_cases."""
        r = repo()
        resolved = resolve_module(module, r.modules)
        features = r.features_by_module[resolved]
        feature_name = resolve_value(feature, features, "feature") if feature else None
        browser_name = resolve_value(browser, r.browsers, "browser") if browser else f"<one of: {', '.join(r.browsers)}>"
        device_name = resolve_value(device, r.devices, "device") if device else f"<one of: {', '.join(r.devices)}>"
        verb = cached(r, "verb_by_type", _verb_by_type).get(test_type, "verify")
        shown_feature = feature_name or "<feature>"

        template = {
            "module": resolved,
            "feature": shown_feature,
            "test_type": test_type,
            "priority": priority or "<Highest | High | Medium | Low>",
            "summary": f"[{resolved}] {test_type}: {verb} {shown_feature}",
            "preconditions": f"A VWO account with access to {resolved}; at least one active project; {browser_name} on {device_name}.",
            "steps": [
                f"Log in to VWO and open the {resolved} module.",
                f"Navigate to the {shown_feature} screen.",
                f"<the {test_type.lower()} action under test, with concrete input values>",
                f"Observe the result on {device_name} using {browser_name}.",
            ],
            "expected_result": "<one specific, observable outcome>",
            "browser": browser_name,
            "device": device_name,
            "status": "Draft",
            "description": default_description(f"{verb} {shown_feature}", shown_feature, resolved, test_type, browser_name, device_name),
        }

        pool = [tc for tc in r.rows if tc.is_live and tc.duplicate_of is None and tc.module == resolved and tc.test_type == test_type]
        if feature_name:
            same_feature = [tc for tc in pool if tc.feature == feature_name]
            pool = same_feature or pool
        if not pool:
            pool = [tc for tc in r.rows if tc.is_live and tc.test_type == test_type]
        examples, seen = [], set()
        for tc in sorted(pool, key=lambda tc: (-tc.priority_rank, tc.status != "Ready", tc.key_number)):
            if tc.scenario not in seen:
                seen.add(tc.scenario)
                examples.append(tc.full())
            if len(examples) == 3:
                break

        payload: dict[str, Any] = {"template": template, "examples": examples, "rules": TEMPLATE_RULES}
        if feature_name:
            existing = [tc for tc in r.rows if tc.is_live and tc.module == resolved and tc.feature == feature_name]
            payload["existing_coverage"] = {"live_tests": len(existing), "by_test_type": ordered_counts(existing, "test_type")}
        else:
            payload["available_features"] = features
        payload["next_step"] = (
            "Fill the placeholders, call validate_test_case, then add_test_cases with dry_run=true, show the user, and repeat with dry_run=false."
            if writes_enabled
            else "This server is read-only (TC_MCP_ALLOW_WRITE is off). Validate the draft with validate_test_case and hand it to the user, or export it."
        )
        return payload

    @mcp.tool(annotations=WRITE, tags={"authoring", "write"})
    def add_test_cases(
        test_cases: Annotated[list[TestCaseDraft], Field(min_length=1, max_length=25, description="1-25 new tests in catalog format.")],
        dry_run: Annotated[bool, Field(description="true: validate and preview only. false: write to the overlay and assign keys.")] = True,
        allow_duplicates: Annotated[bool, Field(description="Allow exact duplicates of existing tests.")] = False,
    ) -> dict[str, Any]:
        """Save new test cases. Validates every draft; if any has errors nothing is written. New keys continue
        after the highest existing key (e.g. VWO-6001). The source CSV is untouched: rows go to an overlay CSV.
        Always run with dry_run=true first and show the preview to the user before writing."""
        r = repo()
        checks = [validate_draft(draft, r, allow_duplicates=allow_duplicates) for draft in test_cases]
        batch_seen: dict[tuple[str, str, str], int] = {}
        for index, check in enumerate(checks):
            signature = (check.record.scenario, check.record.browser, check.record.device)
            if signature in batch_seen:
                check.errors.append(f"Same summary, browser and device as item {batch_seen[signature]} in this batch.")
            batch_seen.setdefault(signature, index)

        if any(not c.valid for c in checks):
            return {
                "written": False,
                "reason": "Validation failed; nothing was written.",
                "items": [{"index": i, "valid": c.valid, "errors": c.errors, "warnings": c.warnings} for i, c in enumerate(checks)],
            }
        if dry_run:
            next_number = max((tc.key_number for tc in r.rows), default=0) + 1
            return {
                "written": False,
                "dry_run": True,
                "would_assign_keys": [f"{r.key_prefix}-{next_number + i}" for i in range(len(checks))],
                "items": [{"index": i, "warnings": c.warnings, "record": c.record.full()} for i, c in enumerate(checks)],
                "next_step": "Show this preview to the user. If approved, call again with dry_run=false.",
            }
        keys = r.write_new([c.record for c in checks])
        return {
            "written": True,
            "keys": keys,
            "overlay_file": str(r.overlay_path),
            "warnings": {keys[i]: c.warnings for i, c in enumerate(checks) if c.warnings},
        }

    @mcp.tool(annotations=WRITE_UPDATE, tags={"authoring", "write"})
    def update_test_case(
        issue_key: Annotated[str, Field(description="The test to change, e.g. 'VWO-1004'.")],
        changes: Annotated[TestCaseChanges, Field(description="Only the fields to change.")],
        dry_run: Annotated[bool, Field(description="true: show the before/after diff only. false: save.")] = True,
    ) -> dict[str, Any]:
        """Edit an existing test (status, priority, steps, expected result, etc.). Saves a new copy to the
        overlay; the latest copy wins. Run with dry_run=true first and confirm the diff with the user."""
        r = repo()
        current = r.get(issue_key)
        if current is None:
            raise ToolError(f"Unknown issue key {issue_key!r}.")
        updates = changes.model_dump(exclude_none=True)
        if not updates:
            raise ToolError("No changes given. Pass at least one field in 'changes'.")

        merged = {
            "module": current.module,
            "feature": current.feature,
            "test_type": current.test_type,
            "priority": current.priority,
            "summary": current.summary,
            "preconditions": current.preconditions,
            "steps": list(current.steps),
            "expected_result": current.expected_result,
            "browser": current.browser,
            "device": current.device,
            "description": current.description,
            "status": current.status,
        }
        merged.update(updates)
        if "description" not in updates and any(f in updates for f in ("feature", "test_type", "browser", "device")):
            merged["description"] = None  # regenerate so it matches the new values
        check = validate_draft(
            TestCaseDraft(**merged),
            r,
            exclude_key=current.key,
            key=current.key,
            allow_duplicates=True,
            check_shared_expected="expected_result" in updates,
        )

        before, after = current.full(), check.record.full()
        diff = {name: {"before": before[name], "after": after[name]} for name in after if name not in ("source", "duplicate_of") and before.get(name) != after[name]}
        if not check.valid:
            return {"written": False, "reason": "Validation failed; nothing was written.", "errors": check.errors, "warnings": check.warnings, "diff": diff}
        if not diff:
            return {"written": False, "reason": "The changes match the current values; nothing to save."}
        if dry_run:
            return {"written": False, "dry_run": True, "diff": diff, "warnings": check.warnings, "next_step": "Confirm with the user, then call again with dry_run=false."}
        r.write_update(dataclasses.replace(check.record, key=current.key))
        return {"written": True, "key": current.key, "diff": diff, "overlay_file": str(r.overlay_path)}
