"""The skills folder is the source of truth: check its size, shape and format."""

from collections import Counter

from tsf_mcp import config
from tsf_mcp.validation import validate_text

EXPECTED_PACKS = {"playwright", "selenium", "cypress", "api", "performance", "security", "llm-eval", "ai-agents", "mcp", "automation"}


def test_catalog_has_100_skills(catalog):
    assert len(catalog.skills) == 100
    assert catalog.load_problems == []


def test_upstream_and_local_split(catalog):
    sources = Counter(s.source for s in catalog.skills.values())
    assert sources == {"upstream": 36, "local": 64}
    assert catalog.manifest["repo"] == config.UPSTREAM_REPO


def test_every_stlc_phase_and_pack_is_covered(catalog):
    phases = {s.phase for s in catalog.skills.values() if s.phase}
    packs = {s.pack for s in catalog.skills.values() if s.pack}
    assert phases == set(config.STLC_PHASES)
    assert packs == EXPECTED_PACKS


def test_every_skill_passes_validation(catalog):
    failures = {}
    for skill in catalog.skills.values():
        report = validate_text(skill.raw, skill.rel_dir.rsplit("/", 1)[-1], skill.rel_dir)
        if not report["valid"] or report["warnings"]:
            failures[skill.name] = report["errors"] + report["warnings"]
    assert failures == {}


def test_every_skill_has_parsed_sections(catalog):
    for skill in catalog.skills.values():
        assert skill.triggers, f"{skill.name} has no trigger phrases"
        assert len(skill.workflow) >= 3, f"{skill.name} workflow not parsed"
        assert skill.guardrails and skill.when_to_use and skill.output_shape, skill.name
        if skill.kind == "stlc":
            assert skill.has_review_gate, f"{skill.name} has no human review gate"


def test_new_skills_follow_house_style(catalog):
    """Skills added in this repo avoid em and en dashes."""
    offenders = [s.name for s in catalog.skills.values() if s.source == "local" and (chr(0x2014) in s.raw or chr(0x2013) in s.raw)]
    assert offenders == []
