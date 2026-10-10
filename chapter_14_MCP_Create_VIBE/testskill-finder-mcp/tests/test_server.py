"""Tools, resources and prompts through the in-memory MCP client."""

import json

import httpx

from conftest import call, call_error
from tsf_mcp.sync import read_manifest, sync_from_github

READ_ONLY_TOOLS = {
    "list_skills", "list_categories", "get_catalog_stats", "search_skills", "find_skill_for_task",
    "get_skill", "get_skill_file", "get_related_skills", "compare_skills", "suggest_skill_chain",
    "get_stlc_pipeline", "export_skill", "validate_skills",
}


async def test_tool_surface(client, write_client):
    assert {t.name for t in await client.list_tools()} == READ_ONLY_TOOLS
    assert {t.name for t in await write_client.list_tools()} == READ_ONLY_TOOLS | {"create_skill", "sync_skills_from_github"}


async def test_one_prompt_per_skill_plus_workflows(client):
    names = {p.name for p in await client.list_prompts()}
    assert {"use_skill", "find_skill", "plan_with_skills", "test-plan-generator", "pw-api-tester"} <= names
    assert len(names) == 103
    rendered = await client.get_prompt("pw-api-tester", {"task": "POST /orders"})
    text = rendered.messages[0].content.text
    assert "Task: POST /orders" in text and "# PW API Tester" in text


async def test_listing_and_categories(client):
    cats = await call(client, "list_categories")
    assert cats["total_skills"] == 100 and len(cats["stlc_phases"]) == 7
    page = await call(client, "list_skills", {"category": "cypress"})
    assert page["total"] == 8 and all(s["pack"] == "cypress" for s in page["skills"])


async def test_search_and_find(client):
    hits = await call(client, "search_skills", {"query": "Playwright API", "limit": 3})
    assert hits["results"][0]["name"] == "pw-api-tester"
    task = await call(client, "find_skill_for_task", {"task": "I need load tests for our checkout API with k6"})
    assert task["results"][0]["name"] == "k6-load-test-generator"
    assert task["results"][0]["how_to_use"]["prompt"] == "k6-load-test-generator"


async def test_get_skill_sections_and_typos(client):
    workflow = await call(client, "get_skill", {"name": "Test Plan Generator", "section": "workflow"})
    assert len(workflow["workflow"]) == 4
    raw = await call(client, "get_skill", {"name": "bug-reporter", "section": "raw"})
    assert raw["content"].startswith("---\nname: bug-reporter")
    assert "Did you mean 'test-plan-generator'" in await call_error(client, "get_skill", {"name": "test-plan-generatr"})


async def test_skill_files_are_readable_but_traversal_is_blocked(client):
    data = await call(client, "get_skill_file", {"name": "test-plan-generator", "path": "references/test-plan-template.md"})
    assert data["content"].startswith("# Test Plan")
    assert "not a supporting file" in await call_error(client, "get_skill_file", {"name": "test-plan-generator", "path": "../../README.md"})


async def test_related_compare_chain_pipeline(client):
    related = await call(client, "get_related_skills", {"name": "pw-flaky-debugger"})
    assert "se-flaky-debugger" in [s["name"] for s in related["similar_elsewhere"]]
    compared = await call(client, "compare_skills", {"names": ["pw-flaky-debugger", "se-flaky-debugger", "cy-flaky-debugger"]})
    assert compared["compared"] == 3
    chain = await call(client, "suggest_skill_chain", {"goal": "take a Jira story to automated Playwright tests and a closure report"})
    phases = [s["phase"] for s in chain["steps"]]
    assert phases[0] == "Requirement Analysis" and phases[-1] == "Test Closure"
    assert any(t["pack"] == "Playwright" for t in chain["tooling"])
    pipeline = await call(client, "get_stlc_pipeline")
    assert [p["order"] for p in pipeline["phases"]] == list(range(1, 8))


async def test_export_formats(client):
    copilot = await call(client, "export_skill", {"name": "bug-reporter", "format": "copilot_prompt"})
    assert copilot["target_file"] == ".github/prompts/bug-reporter.prompt.md" and copilot["content"].startswith("---\nmode: agent")
    claude = await call(client, "export_skill", {"name": "test-plan-generator", "format": "claude_skill"})
    assert "references/test-plan-template.md" in claude["files"]
    cursor = await call(client, "export_skill", {"name": "k6-load-test-generator", "format": "cursor_rule"})
    assert cursor["target_file"].endswith(".mdc")


async def test_validate_whole_catalog(client):
    report = await call(client, "validate_skills")
    assert report["checked"] == 100 and report["valid"] == 100


async def test_resources(client):
    index = json.loads((await client.read_resource("skills://catalog"))[0].text)
    assert len(index) == 100
    skill = (await client.read_resource("skill://cy-test-generator"))[0].text
    assert "name: cy-test-generator" in skill
    template = (await client.read_resource("skill://test-plan-generator/files/references/requirement-checklist.md"))[0].text
    assert template.strip()
    md = (await client.read_resource("skills://stlc-pipeline"))[0].text
    assert md.startswith("# STLC pipeline")


async def test_create_skill_dry_run_then_write(write_client, skills_copy):
    args = {
        "name": "contract-test-reviewer",
        "pack": "api",
        "summary": "Review existing API contract tests for gaps and brittle assertions.",
        "triggers": ["review my contract tests", "are our Pact tests good enough"],
        "produces": "Returns findings with suggested fixes, as a draft for the engineer to verify.",
        "when_to_use": ["A team has Pact or schema tests and wants a quality review.", "Contract tests keep breaking on harmless changes."],
        "workflow": ["Collect the tests: ask for the contract files and test code.", "Check coverage: compare interactions against the API spec.", "Check brittleness: flag exact-value matches on volatile fields.", "List assumptions: note what could not be verified."],
        "output_shape": "| Finding | Test | Fix |\n|---|---|---|",
        "guardrails": ["Never fabricate an interaction or a field.", "The review is a draft the engineer must verify."],
    }
    dry = await call(write_client, "create_skill", args)
    assert dry["valid"] and dry["written"] is False
    assert "Use when a tester says" in " ".join(dry["content"].split())  # the description is wrapped
    saved = await call(write_client, "create_skill", {**args, "dry_run": False})
    assert saved["written"] and saved["total_skills"] == 101
    assert (skills_copy / "framework-packs/api-pack/contract-test-reviewer/SKILL.md").exists()
    found = await call(write_client, "search_skills", {"query": "contract test review", "limit": 1})
    assert found["results"][0]["name"] == "contract-test-reviewer"
    assert "contract-test-reviewer" in {p.name for p in await write_client.list_prompts()}
    assert "already exists" in await call_error(write_client, "create_skill", {**args, "dry_run": False})


def test_sync_writes_only_safe_upstream_files(tmp_path):
    files = {
        "skillmasterclass/skills/README.md": b"# upstream readme\n",
        "skillmasterclass/skills/02-test-planning/test-plan-generator/SKILL.md": b"---\nname: test-plan-generator\n---\n",
        "skillmasterclass/skills/../evil.md": b"nope",
        "other/ignored.md": b"not under the skills path",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.endswith("/commits/main"):
            return httpx.Response(200, json={"sha": "abc123"})
        if "/git/trees/" in url:
            return httpx.Response(200, json={"tree": [{"type": "blob", "path": p, "size": len(b)} for p, b in files.items()]})
        path = url.split("/abc123/", 1)[1]
        return httpx.Response(200, content=files[path])

    target = tmp_path / "skills"
    (target / "local-skill").mkdir(parents=True)
    (target / "local-skill" / "SKILL.md").write_text("mine")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        report = sync_from_github(target, client=client).as_dict()
        again = sync_from_github(target, client=client).as_dict()
    assert report["counts"] == {"added": 2, "updated": 0, "unchanged": 0, "skipped": 1}
    assert again["counts"]["unchanged"] == 2
    assert (target / "local-skill" / "SKILL.md").read_text() == "mine"  # local skills untouched
    assert not (tmp_path / "evil.md").exists()
    assert read_manifest(target)["commit"] == "abc123"
