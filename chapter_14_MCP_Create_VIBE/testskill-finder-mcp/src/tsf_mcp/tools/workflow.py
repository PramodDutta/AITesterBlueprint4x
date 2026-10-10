"""Workflow tools: chain skills across the STLC, show the pipeline, export a skill to other agents."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from tsf_mcp import config
from tsf_mcp.catalog import Skill, first_sentence
from tsf_mcp.state import StateProvider
from tsf_mcp.tools.finder import READ_ONLY

ExportFormat = Literal["claude_skill", "copilot_prompt", "cursor_rule", "markdown"]


def export_files(skill: Skill, fmt: str, root) -> dict[str, Any]:
    summary = first_sentence(skill.description).replace('"', "'")
    if fmt == "claude_skill":
        files = {"SKILL.md": skill.raw}
        for rel in skill.files:
            files[rel] = (root / skill.rel_dir / rel).read_text(encoding="utf-8", errors="replace")
        return {
            "target_folder": f"~/.claude/skills/{skill.name}/",
            "files": files,
            "install": f"cp -r skills/{skill.rel_dir} ~/.claude/skills/",
        }
    if fmt == "copilot_prompt":
        content = f"---\nmode: agent\ndescription: {summary}\n---\n{skill.body}\n"
        return {"target_file": f".github/prompts/{skill.name}.prompt.md", "content": content, "usage": f"In Copilot Chat: /{skill.name} <your input>"}
    if fmt == "cursor_rule":
        content = f"---\ndescription: {summary}\nglobs:\nalwaysApply: false\n---\n{skill.body}\n"
        return {"target_file": f".cursor/rules/{skill.name}.mdc", "content": content, "usage": f"Mention @{skill.name} in Cursor chat, or let Cursor attach it by description."}
    content = f"# {skill.title}\n\n> {skill.description}\n\n{skill.body.split(chr(10), 1)[1] if skill.body.startswith('# ') else skill.body}\n"
    return {"target_file": f"{skill.name}.md", "content": content}


def register(mcp: FastMCP, state: StateProvider) -> None:
    @mcp.tool(annotations=READ_ONLY, tags={"workflow"})
    def suggest_skill_chain(
        goal: Annotated[str, Field(min_length=5, description="End-to-end goal, e.g. 'take JIRA-123 from story to automated Playwright tests and a closure report'.")],
        include_packs: Annotated[bool, Field(description="Add the best framework/specialty pack skills as tooling.")] = True,
        full_lifecycle: Annotated[bool, Field(description="Include every STLC phase, not just the span the goal touches.")] = False,
    ) -> dict[str, Any]:
        """Plan an ordered chain of skills for a multi-step QA goal. Picks the best lifecycle skill per STLC
        phase the goal touches (filling gaps between them so hand-offs work) and adds the best matching
        pack skills (Playwright, Cypress, k6, DeepEval, ...) as tooling."""
        st = state()
        hits = st.index.match_task(goal, limit=40)
        stlc_hits = [h for h in hits if h.skill.kind == "stlc"]
        pack_hits = [h for h in hits if h.skill.kind == "pack"]
        top_stlc = stlc_hits[0].score if stlc_hits else 0
        best_by_phase: dict[int, Any] = {}
        for hit in stlc_hits:
            if hit.score >= top_stlc * 0.15 and hit.skill.phase_number not in best_by_phase:
                best_by_phase[hit.skill.phase_number] = hit

        if full_lifecycle or not best_by_phase:
            span = range(1, len(config.STLC_PHASES) + 1)
        else:
            span = range(min(best_by_phase), max(best_by_phase) + 1)
        by_phase_default = {}
        for skill in st.catalog.skills.values():
            if skill.phase_number and skill.phase_number not in by_phase_default:
                by_phase_default[skill.phase_number] = skill

        steps = []
        for number in span:
            hit = best_by_phase.get(number)
            skill = hit.skill if hit else by_phase_default.get(number)
            if skill is None:
                continue
            why = f"matches {', '.join(hit.matched_terms[:5])}" if hit else "fills the gap so the hand-off between phases stays intact"
            steps.append({"order": len(steps) + 1, "phase": skill.phase, "skill": skill.name, "summary": first_sentence(skill.description), "why": why})

        tooling = []
        if include_packs and pack_hits:
            top_pack = pack_hits[0].score
            tooling = [
                {"skill": h.skill.name, "pack": h.skill.category, "summary": first_sentence(h.skill.description), "use_during": "Test Execution" if h.skill.pack in ("playwright", "selenium", "cypress", "api", "automation") else h.skill.category}
                for h in pack_hits
                if h.score >= top_pack * 0.4
            ][:3]
        for i, step in enumerate(steps[:-1]):
            step["hands_off_to"] = steps[i + 1]["skill"]
        return {
            "goal": goal,
            "steps": steps,
            "tooling": tooling,
            "note": "Each lifecycle skill stops at a human review gate; review its output before starting the next step.",
        }

    @mcp.tool(annotations=READ_ONLY, tags={"workflow"})
    def get_stlc_pipeline() -> dict[str, Any]:
        """Show the Software Testing Life Cycle as an ordered pipeline (requirement -> plan -> design ->
        cases -> execution -> defects -> closure) with the skills available at each phase and the packs
        that plug into execution."""
        st = state()
        groups = st.catalog.categories()
        phases = [
            {
                "order": i + 1,
                "phase": phase,
                "skills": [{"name": s.name, "summary": first_sentence(s.description)} for s in groups.get(phase, [])],
            }
            for i, phase in enumerate(config.STLC_PHASES)
        ]
        packs = {label: [s.name for s in items] for label, items in groups.items() if items and items[0].kind == "pack"}
        flow = " -> ".join(config.STLC_PHASES)
        return {"flow": flow, "phases": phases, "packs": packs}

    @mcp.tool(annotations=READ_ONLY, tags={"workflow"})
    def export_skill(
        name: Annotated[str, Field(description="Skill to export.")],
        format: Annotated[ExportFormat, Field(description="claude_skill (SKILL.md + supporting files for ~/.claude/skills), copilot_prompt (.github/prompts/*.prompt.md), cursor_rule (.cursor/rules/*.mdc), markdown.")] = "claude_skill",
    ) -> dict[str, Any]:
        """Export a skill so another agent can use it: Claude Code skill folder, GitHub Copilot prompt
        file, Cursor rule, or plain Markdown. Returns file contents and where to put them; writes nothing."""
        st = state()
        skill = st.resolve(name)
        return {"skill": skill.name, "format": format, **export_files(skill, format, st.catalog.root)}
