"""Reusable prompts: step-by-step workflows a user can pick from the client's prompt menu."""

from __future__ import annotations

from fastmcp import FastMCP


def register(mcp: FastMCP, writes_enabled: bool) -> None:
    @mcp.prompt(tags={"authoring"})
    def generate_test_cases(module: str, feature: str, test_type: str = "Functional", count: int = 5) -> str:
        """Write new test cases for a module feature in the catalog format."""
        save = (
            "5. Call add_test_cases with dry_run=true, show me the preview, and only after I approve call it again with dry_run=false."
            if writes_enabled
            else "5. This server is read-only, so do not try to save. Show me the validated drafts as a Markdown table."
        )
        return f"""Write {count} new {test_type} test cases for the '{feature}' feature of the {module} module.

1. Call get_test_case_template(module="{module}", feature="{feature}", test_type="{test_type}") and study the examples and existing_coverage.
2. Call find_coverage_gaps(module="{module}") and favor scenarios the catalog is missing.
3. Draft {count} tests that do not repeat existing scenarios. Each needs concrete input values and one specific expected result.
4. Call validate_test_case on each draft and fix every error and warning.
{save}"""

    @mcp.prompt(tags={"planning"})
    def plan_release_run(modules: str = "all", max_tests: int = 50, deadline_hours: float = 8) -> str:
        """Plan a test run for a release that fits a time budget."""
        return f"""Plan the test run for this release.

Modules in scope: {modules}. Time budget: {deadline_hours} hours. Upper bound: {max_tests} tests.

1. Call build_test_suite with suite_type="sanity", the modules above, and max_tests={max_tests}.
2. If effort.total_hours is over {deadline_hours}, rebuild with a smaller max_tests (or suite_type="smoke") until it fits.
3. If there is spare time, add the best remaining tests with get_top_tests_for_module for the riskiest modules.
4. Summarize: suite size, hours, composition by module and priority, and anything left out.
5. Offer to export the final list with export_test_cases(issue_keys=..., format="jira_csv")."""

    @mcp.prompt(tags={"quality"})
    def review_module_coverage(module: str) -> str:
        """Review test coverage and catalog hygiene for one module."""
        return f"""Review test coverage for the {module} module.

1. Call get_test_stats(group_by=["feature", "test_type"], filters={{"module": "{module}"}}).
2. Call find_coverage_gaps(module="{module}").
3. Call get_browser_device_matrix(module="{module}").
4. Call find_duplicate_tests(module="{module}", mode="exact").
5. Write a short report: the 5 biggest gaps (by risk), duplicate rows to remove, and the 3 next tests worth writing."""
