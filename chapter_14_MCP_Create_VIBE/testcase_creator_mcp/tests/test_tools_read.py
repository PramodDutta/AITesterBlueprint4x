"""Read-only tools, resources and prompts, called through the in-memory MCP client."""

import json

from conftest import call, call_error

READ_ONLY_TOOLS = {
    "list_modules", "get_filter_options", "get_test_stats", "get_test_case", "search_test_cases",
    "search_by_keyword", "get_top_tests_for_module", "get_similar_test_cases", "build_test_suite",
    "get_browser_device_matrix", "get_automation_candidates", "estimate_execution_effort",
    "find_duplicate_tests", "find_coverage_gaps", "validate_test_case", "get_test_case_template",
    "export_test_cases", "convert_to_gherkin", "generate_automation_stub",
}


async def test_read_only_server_hides_write_tools(client):
    names = {t.name for t in await client.list_tools()}
    assert names == READ_ONLY_TOOLS


async def test_list_modules(client):
    data = await call(client, "list_modules")
    assert data["module_count"] == 17
    reports = next(m for m in data["modules"] if m["module"] == "Reports")
    assert reports["total"] == 333 and len(reports["features"]) == 4


async def test_stats_pivot(client):
    data = await call(client, "get_test_stats", {"group_by": ["module", "priority"]})
    assert data["total"] == 4585
    assert sum(data["column_totals"].values()) == 4585


async def test_get_test_case_accepts_bare_numbers(client):
    data = await call(client, "get_test_case", {"issue_keys": ["1001", "VWO-99999"]})
    assert data["found"][0]["key"] == "VWO-1001"
    assert data["not_found"] == ["VWO-99999"]


async def test_search_pagination_and_sorting(client):
    page1 = await call(client, "search_test_cases", {"limit": 10})
    assert page1["total_matched"] == 4585 and page1["next_offset"] == 10
    assert all(r["priority"] == "Highest" for r in page1["results"])
    page2 = await call(client, "search_test_cases", {"limit": 10, "offset": 10})
    assert {r["key"] for r in page1["results"]}.isdisjoint(r["key"] for r in page2["results"])


async def test_full_detail_is_capped(client):
    data = await call(client, "search_test_cases", {"detail": "full", "limit": 80})
    assert data["returned"] == 25 and "steps" in data["results"][0]


async def test_search_errors_are_helpful(client):
    assert "Did you mean 'Reports'" in await call_error(client, "search_test_cases", {"filters": {"module": "Reportz"}})
    assert "above max_priority" in await call_error(client, "search_test_cases", {"filters": {"min_priority": "Highest", "max_priority": "Low"}})
    assert "less than or equal to 100" in await call_error(client, "search_test_cases", {"limit": 1000})


async def test_keyword_search(client):
    data = await call(client, "search_by_keyword", {"query": "rate limiting"})
    assert data["results"][0]["feature"] == "rate limiting"


async def test_top_tests_are_ranked_and_diverse(client):
    data = await call(client, "get_top_tests_for_module", {"module": "reports", "count": 4})
    results = data["results"]
    assert [r["rank"] for r in results] == [1, 2, 3, 4]
    assert len({r["feature"] for r in results}) == 4  # one per feature before any repeats
    assert all(r["status"] in ("Ready", "Automated") for r in results)
    assert all("rank_reason" in r for r in results)


async def test_smoke_suite(client):
    data = await call(client, "build_test_suite", {"suite_type": "smoke", "max_tests": 100})
    assert data["size"] == data["qualified"] <= 72
    assert set(data["composition"]["by_priority"]) == {"Highest"}
    assert len(data["issue_keys"]) == data["size"]


async def test_suite_min_tests_relaxes_rules(client):
    data = await call(client, "build_test_suite", {"suite_type": "sanity", "modules": ["sdk"], "max_tests": 20, "min_tests": 15})
    assert data["size"] >= 15 and data["relaxations"]


async def test_effort_and_matrix(client):
    effort = await call(client, "estimate_execution_effort", {"filters": {"module": "Reports", "min_priority": "High"}})
    total = effort["total"]
    assert total["manual_tests"] + total["automated_tests"] == total["tests"]
    matrix = await call(client, "get_browser_device_matrix", {"module": "Heatmaps"})
    assert sum(matrix["browser_totals"].values()) == matrix["total"]


async def test_duplicates_and_gaps(client):
    dupes = await call(client, "find_duplicate_tests", {})
    assert dupes["redundant_rows"] == 466
    gaps = await call(client, "find_coverage_gaps", {"module": "Reports"})
    assert gaps["features_analyzed"] == 4


async def test_export_inline_and_file(client):
    small = await call(client, "export_test_cases", {"issue_keys": ["VWO-1001"], "format": "jira_csv"})
    assert small["content"].startswith("Issue Type,Issue Key,Summary")
    big = await call(client, "export_test_cases", {"filters": {"module": "Reports"}, "format": "csv"})
    assert big["rows"] == 306 and big["file"].endswith(".csv")


async def test_gherkin_and_stub(client):
    gherkin = (await call(client, "convert_to_gherkin", {"issue_keys": ["VWO-1004"]}))["gherkin"]
    assert "Feature: Reports: scheduled email" in gherkin and "And Edge 148 on tablet" in gherkin
    stub = await call(client, "generate_automation_stub", {"issue_key": "VWO-1004"})
    assert "def test_vwo_1004_" in stub["code"]


async def test_resources_and_prompts(client):
    stats = json.loads((await client.read_resource("tc://stats/summary"))[0].text)
    assert stats["total_tests"] == 5000 and stats["exact_duplicate_rows"] == 466
    one = json.loads((await client.read_resource("tc://test/VWO-1001"))[0].text)
    assert one["module"] == "SmartCode"
    prompt = await client.get_prompt("review_module_coverage", {"module": "Reports"})
    assert "find_coverage_gaps" in prompt.messages[0].content.text
