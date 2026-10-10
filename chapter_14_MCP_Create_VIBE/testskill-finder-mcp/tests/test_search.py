"""Golden queries: the searches the goal names must land on the right skill."""

import pytest

from tsf_mcp.search import SearchIndex


@pytest.fixture(scope="module")
def index(catalog):
    return SearchIndex(catalog)


@pytest.mark.parametrize(
    ("query", "expected_top"),
    [
        ("Playwright API", "pw-api-tester"),
        ("test case creator", "test-case-writer"),
        ("test plan creator", "test-plan-generator"),
        ("test strategy", "test-strategy-designer"),
        ("selenium flaky tests", "se-flaky-debugger"),
        ("cypress intercept network mocking", "cy-intercept-mocker"),
        ("k6 load test", "k6-load-test-generator"),
        ("jmeter", "jmeter-test-plan-builder"),
        ("owasp api security", "owasp-api-security-tester"),
        ("deepeval", "deepeval-test-writer"),
        ("rag evaluation", "rag-evaluation-designer"),
        ("prompt injection", "prompt-injection-tester"),
        ("mcp server testing", "mcp-server-tester"),
        ("rest assured", "restassured-api-tester"),
        ("root cause analysis", "rca-analyzer"),
        ("gherkin bdd scenarios", "bdd-scenario-writer"),
        ("appium mobile", "appium-mobile-test-generator"),
    ],
)
def test_golden_queries(index, query, expected_top):
    hits = index.search(query, limit=3)
    assert hits and hits[0].skill.name == expected_top, [h.skill.name for h in hits]


@pytest.mark.parametrize(("query", "pack"), [("playwright", "playwright"), ("selenium", "selenium"), ("cypress", "cypress")])
def test_framework_queries_return_that_pack(index, query, pack):
    hits = index.search(query, limit=5)
    assert len(hits) == 5 and all(h.skill.pack == pack for h in hits)


def test_test_bugs_strategy_finds_strategy_and_bug_skills(index):
    names = [h.skill.name for h in index.search("test bugs strategy", limit=5)]
    assert "test-strategy-designer" in names[:3]
    assert any(n in names for n in ("bug-reporter", "bug-triage-assistant", "defect-trend-analyzer", "bug-repro-minimizer"))


def test_abbreviations_and_synonyms(index):
    assert index.search("pw locator", limit=1)[0].skill.name == "pw-locator-fixer"
    assert index.search("defect report", limit=3)[0].skill.name == "bug-reporter"


def test_task_matching_uses_trigger_phrases(index):
    hits = index.match_task("write a test plan for JIRA-1234", limit=1)
    assert hits[0].skill.name == "test-plan-generator"
    assert hits[0].best_trigger == "write a test plan for JIRA-1234"


def test_nonsense_finds_nothing(index):
    assert index.search("zzqx flurble", limit=5) == []
