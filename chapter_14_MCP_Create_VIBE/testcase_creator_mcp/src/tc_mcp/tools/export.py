"""Export and convert tools: CSV / Jira CSV / Markdown / JSON, Gherkin, and automation stubs."""

from __future__ import annotations

import csv
import io
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from tc_mcp import config
from tc_mcp.models import CSV_COLUMNS, OVERLAY_COLUMNS, TestCase, TestFilter
from tc_mcp.tools.common import READ_ONLY, RepoProvider

ExportFormat = Literal["csv", "jira_csv", "markdown", "json"]
EXTENSIONS = {"csv": ".csv", "jira_csv": ".csv", "markdown": ".md", "json": ".json"}
HTTP_INLINE_LIMIT = 200

# Leading words safe to lowercase after Given/When/Then; anything else (Edge 148, SSO, VWO) keeps its case.
GHERKIN_LOWERCASE_LEADS = {
    "a", "an", "the", "at", "log", "navigate", "perform", "observe", "set", "open", "click", "enter",
    "select", "submit", "send", "trigger", "create", "delete", "verify", "check", "attempt", "call",
    "apply", "upload", "download", "save", "configure", "run", "wait", "load", "go", "sign", "use",
}

PLAYWRIGHT_DEVICES = {"mobile (iOS)": "iPhone 15", "mobile (Android)": "Pixel 7", "tablet": "iPad (gen 7)"}


def slug(text: str, sep: str = "-") -> str:
    return re.sub(r"[^a-z0-9]+", sep, text.casefold()).strip(sep)


def playwright_browser(browser: str) -> tuple[str, str | None]:
    """Map a catalog browser to (Playwright browser, channel)."""
    name = browser.casefold()
    if "edge" in name:
        return "chromium", "msedge"
    if "firefox" in name:
        return "firefox", None
    if "safari" in name:
        return "webkit", None
    return "chromium", None


def render(rows: list[TestCase], fmt: str) -> str:
    if fmt in ("csv", "jira_csv"):
        columns = list(CSV_COLUMNS) if fmt == "jira_csv" else list(OVERLAY_COLUMNS)
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for tc in rows:
            writer.writerow(tc.to_csv_row(include_feature=fmt == "csv"))
        return buffer.getvalue()
    if fmt == "json":
        return json.dumps([tc.full() for tc in rows], indent=2, ensure_ascii=False)

    def cell(text: str) -> str:
        return text.replace("|", "\\|").replace("\n", " ")

    lines = [
        "| Key | Summary | Priority | Type | Status | Browser | Device | Steps | Expected Result |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for tc in rows:
        steps = "<br>".join(f"{i}. {cell(step)}" for i, step in enumerate(tc.steps, start=1))
        lines.append(
            f"| {tc.key} | {cell(tc.summary)} | {tc.priority} | {tc.test_type} | {tc.status} | {tc.browser} | {tc.device} | {steps} | {cell(tc.expected_result)} |"
        )
    return "\n".join(lines) + "\n"


def gherkin(rows: list[TestCase]) -> str:
    groups: dict[tuple[str, str], list[TestCase]] = defaultdict(list)
    for tc in rows:
        groups[(tc.module, tc.feature)].append(tc)

    def sentence(text: str) -> str:
        text = text.strip().rstrip(".")
        first = text.split(" ", 1)[0]
        return text[:1].lower() + text[1:] if first.casefold() in GHERKIN_LOWERCASE_LEADS else text

    blocks = []
    for (module, feature), tests in groups.items():
        lines = [f"@{slug(module)}", f"Feature: {module}: {feature}", ""]
        for tc in tests:
            title = tc.summary.split(": ", 1)[-1]
            tags = [tc.key, tc.priority, tc.test_type, tc.browser, tc.device, tc.status]
            lines.append("  " + " ".join(f"@{slug(t)}" if t != tc.key else f"@{t}" for t in tags))
            lines.append(f"  Scenario: {title[:1].upper() + title[1:]} ({tc.browser}, {tc.device})")
            preconditions = [p for p in (x.strip() for x in tc.preconditions.split(";")) if p]
            for i, item in enumerate(preconditions):
                lines.append(f"    {'Given' if i == 0 else 'And'} {sentence(item)}")
            for i, step in enumerate(tc.steps):
                lines.append(f"    {'When' if i == 0 else 'And'} {sentence(step)}")
            lines.append(f"    Then {sentence(tc.expected_result)}")
            lines.append("")
        blocks.append("\n".join(lines).rstrip() + "\n")
    return "\n".join(blocks)


def pytest_stub(tc: TestCase) -> str:
    action = slug(tc.summary.split(": ", 1)[-1], "_")[:50]
    name = f"test_{slug(tc.key, '_')}_{action}"
    browser, channel = playwright_browser(tc.browser)
    device = PLAYWRIGHT_DEVICES.get(tc.device)
    run = f"pytest -k {name} --browser {browser}" + (f" --browser-channel {channel}" if channel else "") + (f' --device "{device}"' if device else "")
    lines = [
        "import pytest",
        "from playwright.sync_api import Page, expect",
        "",
        "",
        f"@pytest.mark.{slug(tc.priority, '_')}",
        f"@pytest.mark.{slug(tc.test_type, '_')}",
        f"def {name}(page: Page) -> None:",
        f'    """{tc.key}: {tc.summary}',
        "",
        f"    Preconditions: {tc.preconditions}",
        f"    Target: {tc.browser} on {tc.device}",
        f"    Run: {run}",
        '    """',
    ]
    for i, step in enumerate(tc.steps, start=1):
        lines += [f"    # Step {i}: {step}", "    # TODO: implement", ""]
    lines += [
        f"    # Expected: {tc.expected_result}",
        "    # TODO: replace with a real assertion, e.g. expect(page.get_by_role('alert')).to_be_visible()",
        "    pytest.skip('Generated stub: steps not implemented yet')",
        "",
    ]
    return "\n".join(lines)


def playwright_ts_stub(tc: TestCase) -> str:
    browser, channel = playwright_browser(tc.browser)
    device = PLAYWRIGHT_DEVICES.get(tc.device)
    title = tc.summary.split(": ", 1)[-1].replace("'", "\\'")
    use = f"test.use({{ ...devices['{device}'] }});" if device else "// Desktop viewport: no device emulation needed."
    project = f"browserName: '{browser}'" + (f", channel: '{channel}'" if channel else "")
    lines = [
        "import { test, expect, devices } from '@playwright/test';",
        "",
        f"// Target: {tc.browser} on {tc.device}. Suggested project config: {{ {project} }}",
        f"// Preconditions: {tc.preconditions}",
        f"test.describe('{tc.module.replace(chr(39), '')}: {tc.feature}', () => {{",
        f"  {use}",
        "",
        f"  test('{tc.key} {title} @{slug(tc.priority)} @{slug(tc.test_type)}', async ({{ page }}) => {{",
    ]
    for step in tc.steps:
        escaped = step.replace("'", "\\'")
        lines += [f"    await test.step('{escaped}', async () => {{", "      // TODO: implement", "    });", ""]
    lines += [
        f"    // Expected: {tc.expected_result}",
        "    // TODO: replace with a real assertion, e.g. await expect(page.getByRole('alert')).toBeVisible();",
        "    test.fixme(true, 'Generated stub: steps not implemented yet');",
        "  });",
        "});",
        "",
    ]
    return "\n".join(lines)


def register(mcp: FastMCP, repo: RepoProvider, inline_only: bool) -> None:
    @mcp.tool(
        annotations={"readOnlyHint": inline_only, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
        tags={"export"},
    )
    def export_test_cases(
        issue_keys: Annotated[list[str] | None, Field(max_length=1000, description="Export these tests, in this order.")] = None,
        filters: Annotated[TestFilter | None, Field(description="Or export every test matching this filter (live tests if both are omitted).")] = None,
        format: Annotated[ExportFormat, Field(description="csv (all columns + Feature), jira_csv (Jira import columns), markdown (table), json (full records).")] = "markdown",
        max_rows: Annotated[int, Field(ge=1, le=5000)] = 500,
        file_name: Annotated[str | None, Field(description="Write to this file name in the export folder. Without it, up to 50 rows come back inline and larger exports go to a timestamped file.")] = None,
    ) -> dict[str, Any]:
        """Export test cases as CSV, Jira-import CSV, a Markdown table or JSON. Small exports return the
        content inline; large ones are written to the server's export folder and the path is returned."""
        r = repo()
        not_found: list[str] = []
        if issue_keys:
            rows = []
            for key in dict.fromkeys(issue_keys):
                tc = r.get(key)
                (rows.append(tc) if tc else not_found.append(key))
        else:
            rows, _ = r.filter(filters)
        total = len(rows)
        rows = rows[:max_rows]
        payload: dict[str, Any] = {"format": format, "rows": len(rows)}
        if total > len(rows):
            payload["truncated_from"] = total
        if not_found:
            payload["not_found"] = not_found

        inline_cap = HTTP_INLINE_LIMIT if inline_only else config.INLINE_EXPORT_ROWS
        if inline_only or (file_name is None and len(rows) <= inline_cap):
            if len(rows) > inline_cap:
                raise ToolError(
                    f"{len(rows)} rows is too many to return inline from a shared server (limit {inline_cap}). Narrow the filter or lower max_rows."
                )
            payload["content"] = render(rows, format)
            return payload

        folder = config.export_dir()
        folder.mkdir(parents=True, exist_ok=True)
        name = Path(file_name).name if file_name else f"tc_export_{datetime.now():%Y%m%d_%H%M%S}"
        path = (folder / name).with_suffix(EXTENSIONS[format])
        path.write_text(render(rows, format), encoding="utf-8")
        payload.update(file=str(path), bytes=path.stat().st_size, first_keys=[tc.key for tc in rows[:5]])
        return payload

    @mcp.tool(annotations=READ_ONLY, tags={"export"})
    def convert_to_gherkin(
        issue_keys: Annotated[list[str], Field(min_length=1, max_length=10, description="1-10 tests to convert.")],
    ) -> dict[str, Any]:
        """Convert tests to Gherkin (.feature) text: preconditions become Given/And, steps become When/And,
        the expected result becomes Then. Tests are grouped into one Feature per module and feature, and
        tagged with key, priority, type, browser, device and status."""
        r = repo()
        rows, not_found = [], []
        for key in dict.fromkeys(issue_keys):
            tc = r.get(key)
            (rows.append(tc) if tc else not_found.append(key))
        if not rows:
            raise ToolError(f"None of these keys exist: {', '.join(issue_keys)}")
        payload: dict[str, Any] = {"scenarios": len(rows), "gherkin": gherkin(rows)}
        if not_found:
            payload["not_found"] = not_found
        return payload

    @mcp.tool(annotations=READ_ONLY, tags={"export"})
    def generate_automation_stub(
        issue_key: Annotated[str, Field(description="The test to scaffold, e.g. 'VWO-1001'.")],
        framework: Annotated[Literal["pytest_playwright", "playwright_ts"], Field(description="pytest_playwright (Python) or playwright_ts (TypeScript).")] = "pytest_playwright",
    ) -> dict[str, Any]:
        """Generate an automation skeleton for one test: steps become commented blocks (or test.step calls),
        with the right Playwright browser and device emulation for the test's target. Selectors and
        assertions are left as TODOs for the engineer."""
        r = repo()
        tc = r.get(issue_key)
        if tc is None:
            raise ToolError(f"Unknown issue key {issue_key!r}.")
        if framework == "pytest_playwright":
            return {"framework": framework, "suggested_file": f"tests/test_{slug(tc.key, '_')}.py", "code": pytest_stub(tc)}
        return {"framework": framework, "suggested_file": f"tests/{slug(tc.key)}.spec.ts", "code": playwright_ts_stub(tc)}
