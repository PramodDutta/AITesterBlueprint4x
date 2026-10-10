"""Prompts: three workflow prompts plus one prompt per skill (named after the skill).

A per-skill prompt loads that skill's instructions and your task into the conversation, so in
Claude Code each skill shows up as a slash command, e.g. /mcp__testskill-finder__test-plan-generator.
"""

from collections.abc import Callable
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.prompts import Prompt
from pydantic import Field

from tsf_mcp.catalog import first_sentence
from tsf_mcp.state import StateProvider

TaskArg = Annotated[str, Field(description="Your input for the skill: a ticket, story, code, endpoint, results, or a short description.")]


def skill_prompt_text(body: str, name: str, task: str) -> str:
    task_line = task.strip() or "(no task given yet: ask me for the input this skill needs before starting)"
    return (
        f"Use the '{name}' skill below to complete my task. Follow its workflow in order, respect its "
        f"guardrails, and stop at its review gate.\n\nTask: {task_line}\n\n<skill name=\"{name}\">\n{body}\n</skill>"
    )


def register(mcp: FastMCP, state: StateProvider) -> Callable[[], None]:
    @mcp.prompt(tags={"workflow"})
    def use_skill(skill_name: str, task: TaskArg = "") -> str:
        """Run any skill by name on your task."""
        skill = state().resolve(skill_name)
        return skill_prompt_text(skill.body, skill.name, task)

    @mcp.prompt(tags={"workflow"})
    def find_skill(need: str) -> str:
        """Find the right skill for something you need to do, then use it."""
        return (
            f"I need to: {need}\n\n"
            "1. Call find_skill_for_task with my need and show me the top 3 with one line each on why.\n"
            "2. Call get_skill on the best match and summarize its workflow in 3-5 bullets.\n"
            "3. Ask me for any input the skill needs, then follow the skill step by step."
        )

    @mcp.prompt(tags={"workflow"})
    def plan_with_skills(goal: str) -> str:
        """Chain several skills across the STLC for a bigger goal."""
        return (
            f"Goal: {goal}\n\n"
            "1. Call suggest_skill_chain with this goal and show me the ordered steps and tooling.\n"
            "2. For each step, call get_skill and run its workflow on my inputs.\n"
            "3. Stop at every review gate and wait for my approval before the next skill.\n"
            "4. Finish with a short summary of what each skill produced."
        )

    registered: set[str] = set()

    def make(name: str) -> Callable[..., str]:
        def prompt(task: TaskArg = "") -> str:
            skill = state().catalog.get(name)
            if skill is None:
                return f"The skill '{name}' is no longer in the catalog. Use search_skills to find a replacement."
            return skill_prompt_text(skill.body, skill.name, task)

        return prompt

    def refresh() -> None:
        for skill in state().catalog.skills.values():
            if skill.name in registered:
                continue
            mcp.add_prompt(
                Prompt.from_function(
                    make(skill.name),
                    name=skill.name,
                    title=skill.title,
                    description=f"[{skill.category}] {first_sentence(skill.description)}",
                    tags={"skill", skill.kind},
                )
            )
            registered.add(skill.name)

    refresh()
    return refresh
