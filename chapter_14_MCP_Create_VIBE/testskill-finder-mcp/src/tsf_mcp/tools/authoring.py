"""Authoring tools: validate skills, create a new skill in the house format, sync from GitHub."""

from __future__ import annotations

import textwrap
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from tsf_mcp import config
from tsf_mcp.state import StateProvider
from tsf_mcp.sync import sync_from_github
from tsf_mcp.tools.finder import READ_ONLY
from tsf_mcp.validation import NAME_RE, validate_text

WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
SYNC = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True}
Phase = Literal[
    "Requirement Analysis",
    "Test Planning",
    "Test Design",
    "Test Case Development",
    "Test Execution",
    "Defect Management",
    "Test Closure",
]


def render_skill(
    *,
    name: str,
    title: str,
    phase: str | None,
    pack: str | None,
    summary: str,
    triggers: list[str],
    produces: str,
    role: str,
    when_to_use: list[str],
    workflow: list[str],
    output_shape: str,
    output_language: str,
    guardrails: list[str],
) -> str:
    quoted = ", ".join(f'"{t.strip()}"' for t in triggers)
    description = f"{summary.strip()} Use when a tester says {quoted}. {produces.strip()}"
    folded = textwrap.fill(description, width=88, initial_indent="  ", subsequent_indent="  ")
    meta_line = f"  stlc-phase: {phase}" if phase else f"  pack: {pack}"

    steps = []
    for step in workflow:
        step = step.strip()
        head, sep, rest = step.partition(":")
        steps.append(f"**{head.strip().rstrip('.')}.** {rest.strip()}" if sep and len(head) <= 40 else step)
    if phase and not any("human review" in s.lower() for s in steps):
        steps.append("**HUMAN REVIEW GATE (mandatory).** Present the output as a draft, list every assumption and open question, and ask for confirmation before it is treated as final.")

    lines = [
        "---",
        f"name: {name}",
        "description: >-",
        folded,
        "license: MIT",
        "metadata:",
        "  author: TheTestingAcademy",
        meta_line,
        "  version: 1.0.0",
        "---",
        "",
        f"# {title}",
        "",
        role.strip(),
        "",
        "## When to use",
        *[f"- {item.strip()}" for item in when_to_use],
        "",
        "## Workflow",
        *[f"{i}. {s}" for i, s in enumerate(steps, start=1)],
        "",
        "## Output shape",
        f"```{output_language}",
        output_shape.rstrip(),
        "```",
        "",
        "## Guardrails",
        *[f"- {g.strip()}" for g in guardrails],
        "",
    ]
    return "\n".join(lines)


def register(mcp: FastMCP, state: StateProvider, refresh_prompts) -> None:
    @mcp.tool(annotations=READ_ONLY, tags={"quality"})
    def validate_skills(
        name: Annotated[str | None, Field(description="One skill to check; omit to check the whole catalog.")] = None,
        only_problems: Annotated[bool, Field(description="Only list skills with errors or warnings.")] = True,
    ) -> dict[str, Any]:
        """Check skills against the catalog format: frontmatter (name = folder, description with 'Use when'
        and trigger phrases, license, metadata with exactly one of stlc-phase/pack, semantic version),
        the four body sections, workflow steps, a review gate for lifecycle skills, and an output example."""
        st = state()
        skills = [st.resolve(name)] if name else list(st.catalog.skills.values())
        results = []
        for skill in skills:
            report = validate_text(skill.raw, skill.rel_dir.rsplit("/", 1)[-1], skill.rel_dir)
            if not only_problems or report["errors"] or report["warnings"]:
                results.append({"skill": skill.name, "path": f"{skill.rel_dir}/SKILL.md", **{k: report[k] for k in ("valid", "errors", "warnings")}})
        return {
            "checked": len(skills),
            "valid": sum(1 for s in skills if validate_text(s.raw, s.rel_dir.rsplit("/", 1)[-1], s.rel_dir)["valid"]),
            "load_problems": st.catalog.load_problems,
            "results": results,
        }

    @mcp.tool(annotations=WRITE, tags={"authoring", "write"})
    def create_skill(
        name: Annotated[str, Field(description="kebab-case folder/skill name, e.g. 'contract-test-reviewer'.")],
        summary: Annotated[str, Field(min_length=20, description="One sentence: what the skill does.")],
        triggers: Annotated[list[str], Field(min_length=2, max_length=5, description="Phrases a user would type, e.g. 'review my contract tests'.")],
        produces: Annotated[str, Field(min_length=20, description="One or two sentences: what it outputs and that it is a draft for review.")],
        when_to_use: Annotated[list[str], Field(min_length=2, max_length=6)],
        workflow: Annotated[list[str], Field(min_length=3, max_length=9, description="Steps as 'Step name: what to do'. Lifecycle skills get a HUMAN REVIEW GATE step added automatically.")],
        output_shape: Annotated[str, Field(min_length=10, description="Example of the output (template, table or code).")],
        guardrails: Annotated[list[str], Field(min_length=2, max_length=7, description="Include a 'Never fabricate ...' rule.")],
        phase: Annotated[Phase | None, Field(description="STLC phase for a lifecycle skill. Give phase OR pack.")] = None,
        pack: Annotated[str | None, Field(description="Pack id for a framework/specialty skill, e.g. 'playwright', 'cypress', 'api', 'security', 'llm-eval'.")] = None,
        title: Annotated[str | None, Field(description="Display title; defaults to the name in Title Case.")] = None,
        role: Annotated[str | None, Field(description="1-2 sentence role statement opening the body.")] = None,
        output_language: Annotated[str, Field(description="Code fence language for the output example, e.g. 'typescript', 'python', 'text'.")] = "text",
        dry_run: Annotated[bool, Field(description="true: render and validate only. false: write the SKILL.md.")] = True,
    ) -> dict[str, Any]:
        """Create a new skill in the same SKILL.md format as the rest of the catalog and save it in the right
        folder (STLC phase folder or framework-packs/<pack>-pack). Validates before writing; never overwrites."""
        if bool(phase) == bool(pack):
            raise ToolError("Give exactly one of phase (lifecycle skill) or pack (framework/specialty skill).")
        if not NAME_RE.match(name) or len(name) > 64:
            raise ToolError("name must be kebab-case (a-z, 0-9, hyphens), at most 64 characters.")
        st = state()
        if st.catalog.get(name):
            raise ToolError(f"A skill named '{name}' already exists at {st.catalog.get(name).rel_dir}.")
        pack_id = pack.strip().lower() if pack else None
        rel_dir = f"{config.PHASE_FOLDERS[phase]}/{name}" if phase else f"framework-packs/{config.pack_folder(pack_id)}/{name}"
        content = render_skill(
            name=name,
            title=title or name.replace("-", " ").title(),
            phase=phase,
            pack=pack_id,
            summary=summary,
            triggers=triggers,
            produces=produces,
            role=role or f"You help QA teams with {summary.strip().rstrip('.').lower()}. **Everything you produce is a draft for a human to review.**",
            when_to_use=when_to_use,
            workflow=workflow,
            output_shape=output_shape,
            output_language=output_language,
            guardrails=guardrails,
        )
        report = validate_text(content, name, rel_dir)
        payload: dict[str, Any] = {"path": f"{rel_dir}/SKILL.md", "valid": report["valid"], "errors": report["errors"], "warnings": report["warnings"], "content": content}
        if not report["valid"] or dry_run:
            payload["written"] = False
            if report["valid"]:
                payload["next_step"] = "Show the content to the user; call again with dry_run=false to save it."
            return payload
        target = st.catalog.root / rel_dir / "SKILL.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        st.fresh()
        refresh_prompts()
        payload.update(written=True, total_skills=len(st.catalog.skills))
        payload.pop("content")
        return payload

    @mcp.tool(annotations=SYNC, tags={"authoring", "write"})
    def sync_skills_from_github(
        ref: Annotated[str, Field(description="Branch, tag or commit of the upstream repo.")] = config.UPSTREAM_REF,
        dry_run: Annotated[bool, Field(description="true: report what would change. false: download and write.")] = True,
    ) -> dict[str, Any]:
        """Download the upstream skill catalog (PramodDutta/skillmasterclass, skillmasterclass/skills) into the
        skills folder. Adds and updates upstream files only; local skills are never modified or deleted."""
        st = state()
        report = sync_from_github(st.catalog.root, ref=ref, dry_run=dry_run).as_dict()
        if not dry_run:
            st.fresh()
            refresh_prompts()
            report["total_skills"] = len(st.catalog.skills)
        return report
