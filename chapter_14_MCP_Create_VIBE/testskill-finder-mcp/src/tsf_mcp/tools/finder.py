"""Discovery and finder tools: list, browse, search, match a task, read, relate, compare."""

from __future__ import annotations

from collections import Counter
from pathlib import PurePosixPath
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from tsf_mcp import config
from tsf_mcp.catalog import Skill, find_section, first_sentence
from tsf_mcp.state import StateProvider

READ_ONLY = {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
Kind = Literal["all", "stlc", "pack"]
Section = Literal["all", "overview", "when_to_use", "workflow", "output_shape", "guardrails", "raw"]


def filter_skills(skills: list[Skill], category: str | None, kind: str, source: str = "all") -> list[Skill]:
    if category:
        wanted = category.strip().lower()
        skills = [
            s for s in skills
            if wanted in (s.category.lower(), (s.pack or "").lower(), (s.phase or "").lower())
            or wanted in s.rel_dir.lower().split("/")
            or wanted.replace(" ", "-") in s.rel_dir.lower()
        ]
    if kind != "all":
        skills = [s for s in skills if s.kind == kind]
    if source != "all":
        skills = [s for s in skills if s.source == source]
    return skills


def how_to_use(skill: Skill) -> dict[str, str]:
    return {
        "prompt": skill.name,
        "resource": f"skill://{skill.name}",
        "install_claude_code": f"cp -r skills/{skill.rel_dir} ~/.claude/skills/",
    }


def register(mcp: FastMCP, state: StateProvider) -> None:
    @mcp.tool(annotations=READ_ONLY, tags={"discovery"})
    def list_skills(
        category: Annotated[str | None, Field(description="STLC phase (e.g. 'Test Planning') or pack (e.g. 'playwright', 'cypress', 'security', 'llm-eval', 'mcp'). Omit for all.")] = None,
        kind: Annotated[Kind, Field(description="'stlc' for lifecycle skills, 'pack' for framework/specialty packs.")] = "all",
        source: Annotated[Literal["all", "upstream", "local"], Field(description="'upstream' = synced from GitHub, 'local' = added in this folder.")] = "all",
        limit: Annotated[int, Field(ge=1, le=100)] = 100,
        offset: Annotated[int, Field(ge=0)] = 0,
    ) -> dict[str, Any]:
        """List skills in catalog order (STLC phases first, then packs) with a one-line summary each.
        Use to browse. To find skills for a need, use search_skills or find_skill_for_task instead."""
        st = state()
        skills = filter_skills(list(st.catalog.skills.values()), category, kind, source)
        page = skills[offset : offset + limit]
        return {
            "total": len(skills),
            "returned": len(page),
            "next_offset": offset + limit if offset + limit < len(skills) else None,
            "skills": [s.summary() for s in page],
        }

    @mcp.tool(annotations=READ_ONLY, tags={"discovery"})
    def list_categories() -> dict[str, Any]:
        """List the 7 STLC phases (in testing order) and the framework/specialty packs, with skill
        counts and names. Use to see what areas the catalog covers."""
        st = state()
        groups = st.catalog.categories()
        phases = [
            {"phase": phase, "order": i + 1, "folder": config.PHASE_FOLDERS[phase], "count": len(groups.get(phase, [])), "skills": [s.name for s in groups.get(phase, [])]}
            for i, phase in enumerate(config.STLC_PHASES)
        ]
        packs = []
        for label, skills in groups.items():
            if skills and skills[0].kind == "pack":
                packs.append({"pack": skills[0].pack, "label": label, "count": len(skills), "skills": [s.name for s in skills]})
        return {"total_skills": len(st.catalog.skills), "stlc_phases": phases, "packs": packs}

    @mcp.tool(annotations=READ_ONLY, tags={"discovery"})
    def get_catalog_stats() -> dict[str, Any]:
        """Headline numbers: total skills, lifecycle vs pack, per category, upstream vs local,
        supporting files, and when the upstream catalog was last synced."""
        st = state()
        skills = list(st.catalog.skills.values())
        manifest = st.catalog.manifest or {}
        return {
            "total_skills": len(skills),
            "by_kind": dict(Counter(s.kind for s in skills)),
            "by_category": {label: len(items) for label, items in st.catalog.categories().items()},
            "by_source": dict(Counter(s.source for s in skills)),
            "skills_with_supporting_files": sum(1 for s in skills if s.files),
            "skills_folder": str(st.catalog.root),
            "upstream": {k: manifest.get(k) for k in ("repo", "ref", "commit", "synced_at")} if manifest else None,
            "load_problems": st.catalog.load_problems,
        }

    @mcp.tool(annotations=READ_ONLY, tags={"search"})
    def search_skills(
        query: Annotated[str, Field(min_length=2, description="Keywords, e.g. 'playwright', 'playwright api', 'test case creator', 'test strategy', 'flaky selenium', 'k6 load test'.")],
        category: Annotated[str | None, Field(description="Optional STLC phase or pack to search within.")] = None,
        kind: Kind = "all",
        limit: Annotated[int, Field(ge=1, le=config.MAX_RESULTS)] = config.DEFAULT_RESULTS,
    ) -> dict[str, Any]:
        """Keyword search over skill names, titles, trigger phrases, descriptions and bodies. Understands
        abbreviations and synonyms (pw = playwright, creator ~ writer ~ generator, bug ~ defect, k6 ~ performance).
        Returns ranked skills with a score and which fields matched."""
        st = state()
        candidates = filter_skills(list(st.catalog.skills.values()), category, kind)
        hits = st.index.search(query, candidates, limit=limit)
        payload: dict[str, Any] = {"query": query, "returned": len(hits), "results": [h.as_dict() for h in hits]}
        if not hits:
            payload["hint"] = "No matches. Try broader words, or call list_categories to browse."
        return payload

    @mcp.tool(annotations=READ_ONLY, tags={"search"})
    def find_skill_for_task(
        task: Annotated[str, Field(min_length=5, description="What the user wants to get done, in plain English, e.g. 'I need to write API tests for our /orders endpoint in Playwright'.")],
        top_k: Annotated[int, Field(ge=1, le=10)] = 3,
    ) -> dict[str, Any]:
        """Recommend the best skill(s) for a task described in plain English. Matches the task against each
        skill's trigger phrases ('Use when a tester says ...') as well as its content, and says how to use the pick."""
        st = state()
        hits = st.index.match_task(task, limit=top_k)
        results = []
        for rank, hit in enumerate(hits, start=1):
            row = hit.as_dict()
            row["rank"] = rank
            row["why"] = (
                f"Matches {', '.join(hit.matched_terms[:6])} in {', '.join(hit.matched_fields[:4]) or 'body'}"
                + (f"; closest trigger: \"{hit.best_trigger}\"" if hit.best_trigger else "")
            )
            row["how_to_use"] = how_to_use(hit.skill)
            results.append(row)
        payload: dict[str, Any] = {"task": task, "results": results}
        if results:
            payload["next_step"] = f"Call get_skill('{results[0]['name']}') for the full workflow, or use the '{results[0]['name']}' prompt."
        else:
            payload["hint"] = "Nothing matched. Rephrase with the testing activity (plan, design, automate, report) and the tool (Playwright, k6, DeepEval)."
        return payload

    @mcp.tool(annotations=READ_ONLY, tags={"search"})
    def get_skill(
        name: Annotated[str, Field(description="Skill name, e.g. 'test-plan-generator' (titles and close spellings also work).")],
        section: Annotated[Section, Field(description="'all' (structured), one section, or 'raw' for the full SKILL.md text.")] = "all",
    ) -> dict[str, Any]:
        """Read one skill: metadata, trigger phrases, when-to-use, workflow steps, output shape, guardrails,
        supporting files, and how to use it. Use after search to open a result."""
        st = state()
        skill = st.resolve(name)
        if section == "raw":
            return {"name": skill.name, "path": f"{skill.rel_dir}/SKILL.md", "content": skill.raw}
        detail = skill.detail()
        detail["how_to_use"] = how_to_use(skill)
        if section == "all":
            detail["intro"] = skill.intro
            return detail
        if section == "overview":
            keys = ("name", "title", "category", "kind", "phase", "pack", "description", "triggers", "source", "path", "how_to_use")
            return {k: detail[k] for k in keys} | {"intro": skill.intro}
        return {"name": skill.name, section: detail[section]}

    @mcp.tool(annotations=READ_ONLY, tags={"search"})
    def get_skill_file(
        name: Annotated[str, Field(description="Skill name.")],
        path: Annotated[str, Field(description="Supporting file path inside the skill folder, as listed in get_skill's supporting_files, e.g. 'references/test-plan-template.md'.")],
    ) -> dict[str, Any]:
        """Read a supporting file that ships with a skill (templates, checklists, scripts, Copilot prompts).
        Scripts are returned as text only; they are never executed by this server."""
        st = state()
        skill = st.resolve(name)
        rel = PurePosixPath(path)
        if rel.is_absolute() or ".." in rel.parts or path not in skill.files:
            available = ", ".join(skill.files) or "none"
            raise ToolError(f"'{path}' is not a supporting file of {skill.name}. Available: {available}")
        file_path = st.catalog.root / skill.rel_dir / path
        text = file_path.read_text(encoding="utf-8", errors="replace")
        truncated = len(text) > config.MAX_FILE_CHARS
        return {"skill": skill.name, "path": path, "content": text[: config.MAX_FILE_CHARS], "truncated": truncated}

    @mcp.tool(annotations=READ_ONLY, tags={"search"})
    def get_related_skills(
        name: Annotated[str, Field(description="Skill to find neighbours for.")],
        limit: Annotated[int, Field(ge=1, le=20)] = 6,
    ) -> dict[str, Any]:
        """Find skills related to one skill: the STLC hand-off before and after it, siblings in the same
        phase or pack, and skills with similar content in other packs (e.g. pw-flaky-debugger <-> se-flaky-debugger)."""
        st = state()
        skill = st.resolve(name)
        skills = st.catalog.skills.values()
        handoff: dict[str, list[str]] = {}
        if skill.phase_number:
            for label, number in (("previous_phase", skill.phase_number - 1), ("next_phase", skill.phase_number + 1)):
                handoff[label] = [s.name for s in skills if s.phase_number == number]
        siblings = [s.name for s in skills if s.category == skill.category and s.name != skill.name]
        query = " ".join([skill.title, *skill.triggers])
        similar = [
            {"name": h.skill.name, "category": h.skill.category, "score": round(h.score, 1)}
            for h in st.index.search(query, limit=limit + 10)
            if h.skill.name != skill.name and h.skill.category != skill.category
        ][:limit]
        return {"skill": skill.name, "category": skill.category, "stlc_handoff": handoff or None, "same_category": siblings[:limit], "similar_elsewhere": similar}

    @mcp.tool(annotations=READ_ONLY, tags={"search"})
    def compare_skills(
        names: Annotated[list[str], Field(min_length=2, max_length=5, description="2-5 skill names to compare side by side.")],
    ) -> dict[str, Any]:
        """Compare 2-5 skills side by side: purpose, category, triggers, number of workflow steps, whether
        they stop at a human review gate, output format, and guardrails. Use to pick between similar skills."""
        st = state()
        rows = []
        for name in names:
            skill = st.resolve(name)
            fence = find_section(skill.sections, "output shape").split("\n", 1)[0]
            language = fence[3:].strip() if fence.startswith("```") else ""
            rows.append(
                {
                    "name": skill.name,
                    "category": skill.category,
                    "purpose": first_sentence(skill.description),
                    "triggers": skill.triggers[:3],
                    "workflow_steps": len(skill.workflow),
                    "human_review_gate": skill.has_review_gate,
                    "output_format": language or "text",
                    "guardrails": len(skill.guardrails),
                    "supporting_files": len(skill.files),
                }
            )
        return {"compared": len(rows), "skills": rows}
