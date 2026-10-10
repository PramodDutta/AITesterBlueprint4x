"""Turn a TestCaseDraft into a TestCase record and lint it against the catalog conventions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastmcp.exceptions import ToolError

from tc_mcp.models import TestCase, TestCaseDraft
from tc_mcp.repository import STEP_NUMBER_RE, SUMMARY_RE, Repository, generate_labels
from tc_mcp.resolver import resolve_module, resolve_value

GENERIC_EXPECTED_PHRASES = ("works as expected", "should work", "works correctly", "works fine", "no errors", "is successful", "as expected")
GENERIC_EXPECTED_SHARED_BY = 25  # an expected result reused by this many tests is too generic


@dataclass
class Validation:
    record: TestCase
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    possible_duplicates: list[dict[str, Any]] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors

    def report(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "possible_duplicates": self.possible_duplicates,
            "normalized": self.record.full(),
        }


def default_description(action: str, feature: str, module: str, test_type: str, browser: str, device: str) -> str:
    phrase = action.replace(feature, f"the {feature}", 1) if feature in action else f"{action} for the {feature}"
    return (
        f"As a QA engineer, {phrase} in the {module} module to make sure it behaves correctly "
        f"for {test_type.lower()} scenarios on {device} ({browser})."
    )


def validate_draft(
    draft: TestCaseDraft,
    r: Repository,
    *,
    allow_duplicates: bool = False,
    exclude_key: str | None = None,
    key: str = "(new)",
    check_shared_expected: bool = True,
) -> Validation:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        module = resolve_module(draft.module, r.modules)
    except ToolError as exc:
        errors.append(str(exc))
        module = draft.module.strip()

    feature = draft.feature.strip()
    known = {f.casefold(): f for f in r.features_by_module.get(module, [])}
    if feature.casefold() in known:
        feature = known[feature.casefold()]
    elif module in r.features_by_module:
        warnings.append(f"'{feature}' is a new feature for {module}. Known features: {', '.join(r.features_by_module[module])}.")

    def catalog_value(raw: str, allowed: list[str], name: str) -> str:
        try:
            return resolve_value(raw, allowed, name)
        except ToolError:
            warnings.append(f"{name} {raw!r} is not in the current catalog ({', '.join(allowed)}).")
            return raw.strip()

    browser = catalog_value(draft.browser, r.browsers, "browser")
    device = catalog_value(draft.device, r.devices, "device")

    summary = " ".join(draft.summary.split())
    action = feature
    match = SUMMARY_RE.match(summary)
    if not match:
        errors.append("Summary must look like '[Module] Test Type: action feature', e.g. '[Reports] Boundary: test limits of scheduled email'.")
    else:
        action = match.group("action")
        if match.group("module").casefold() != module.casefold():
            errors.append(f"Summary module [{match.group('module')}] does not match module '{module}'.")
        if match.group("type").casefold() != draft.test_type.casefold():
            errors.append(f"Summary type '{match.group('type')}' does not match test_type '{draft.test_type}'.")
        if feature.casefold() not in summary.casefold():
            warnings.append(f"Summary does not mention the feature '{feature}'.")

    steps = [STEP_NUMBER_RE.sub("", step).strip() for step in draft.steps]
    steps = [step for step in steps if step]
    if not steps:
        errors.append("At least one non-empty step is required.")
    if any(" | " in step for step in steps):
        errors.append("Steps must not contain ' | ' (it is the step separator in the CSV). Pass each step as its own list item.")
    if 0 < len(steps) < 3:
        warnings.append(f"Only {len(steps)} step(s). Catalog tests use 4: open module, navigate, act, observe.")
    if len(steps) > 12:
        warnings.append(f"{len(steps)} steps is long; consider splitting into two tests.")
    if any(len(step) < 8 for step in steps):
        warnings.append("Some steps are very short; make each step a concrete action.")
    if len(set(s.casefold() for s in steps)) < len(steps):
        warnings.append("Some steps are repeated.")

    expected = draft.expected_result.strip()
    if any(phrase in expected.casefold() for phrase in GENERIC_EXPECTED_PHRASES):
        warnings.append("Expected result is vague ('works as expected' style). State the exact observable outcome.")
    shared = r.expected_result_counts.get(expected.casefold(), 0) if check_shared_expected else 0
    if shared >= GENERIC_EXPECTED_SHARED_BY:
        warnings.append(f"Expected result text is shared by {shared} existing tests; make it specific to this test.")

    description = (draft.description or "").strip() or default_description(action, feature, module, draft.test_type, browser, device)
    record = TestCase(
        key=key,
        summary=summary,
        description=description,
        priority=draft.priority,
        module=module,
        labels=generate_labels(module, draft.test_type),
        test_type=draft.test_type,
        preconditions=draft.preconditions.strip(),
        steps=steps,
        expected_result=expected,
        browser=browser,
        device=device,
        status=draft.status,
        feature=feature,
        source="overlay",
    )

    validation = Validation(record=record, errors=errors, warnings=warnings)
    for tc in r.rows:
        if tc.key == exclude_key or tc.scenario != record.scenario:
            continue
        exact = tc.browser == record.browser and tc.device == record.device
        if exact or len(validation.possible_duplicates) < 5:
            validation.possible_duplicates.append(
                {"key": tc.key, "status": tc.status, "browser": tc.browser, "device": tc.device, "match": "exact duplicate" if exact else "same scenario, other browser/device"}
            )
        if exact:
            message = f"Exact duplicate of {tc.key} (same summary, browser and device)."
            if allow_duplicates:
                warnings.append(message)
            else:
                errors.append(message + " Change browser/device/summary, or pass allow_duplicates=true.")
    return validation
