"""Authoring flow: validate, dry run, add, update. Writes go to a temp overlay, never the source CSV."""

from conftest import call

DRAFT = {
    "module": "Reports",
    "feature": "scheduled email",
    "test_type": "Negative",
    "priority": "High",
    "summary": "[Reports] Negative: reject invalid recipient in scheduled email",
    "preconditions": "A VWO account with access to Reports; at least one saved report; Chrome 148 on desktop.",
    "steps": [
        "Log in to VWO and open the Reports module.",
        "Open the scheduled email settings of a saved report.",
        "Enter 'not-an-email' as the recipient and click Save.",
        "Observe the form on desktop using Chrome 148.",
    ],
    "expected_result": "Save is blocked and the recipient field shows 'Enter a valid email address'.",
    "browser": "chrome",
    "device": "desktop",
}


async def test_write_server_lists_write_tools(write_client):
    names = {t.name for t in await write_client.list_tools()}
    assert {"add_test_cases", "update_test_case"} <= names


async def test_validation_catches_bad_drafts(write_client):
    bad = dict(DRAFT, summary="Reports negative test", steps=["Do it"], expected_result="Works as expected")
    data = await call(write_client, "validate_test_case", {"test_case": bad})
    assert not data["valid"]
    assert any("Summary must look like" in e for e in data["errors"])
    assert len(data["warnings"]) >= 2


async def test_add_flow(write_client, repo):
    source_before = repo.data_path.read_bytes()
    dry = await call(write_client, "add_test_cases", {"test_cases": [DRAFT]})
    assert dry["written"] is False and dry["would_assign_keys"] == ["VWO-6001"]

    added = await call(write_client, "add_test_cases", {"test_cases": [DRAFT], "dry_run": False})
    assert added["written"] is True and added["keys"] == ["VWO-6001"]

    fetched = (await call(write_client, "get_test_case", {"issue_keys": ["VWO-6001"]}))["found"][0]
    assert fetched["browser"] == "Chrome 148" and fetched["source"] == "overlay"

    again = await call(write_client, "add_test_cases", {"test_cases": [DRAFT], "dry_run": False})
    assert again["written"] is False and "Exact duplicate of VWO-6001" in again["items"][0]["errors"][0]
    assert repo.data_path.read_bytes() == source_before  # source CSV untouched


async def test_update_flow(write_client):
    changes = {"status": "Automated", "priority": "Highest"}
    dry = await call(write_client, "update_test_case", {"issue_key": "VWO-1004", "changes": changes})
    assert dry["diff"]["status"] == {"before": "Ready", "after": "Automated"}
    assert dry["warnings"] == []

    saved = await call(write_client, "update_test_case", {"issue_key": "VWO-1004", "changes": changes, "dry_run": False})
    assert saved["written"] is True
    after = (await call(write_client, "get_test_case", {"issue_keys": ["VWO-1004"]}))["found"][0]
    assert (after["status"], after["priority"]) == ("Automated", "Highest")
