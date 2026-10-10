"""Load every SKILL.md under the skills folder into structured, searchable records.

The folder is the source of truth: the catalog reloads itself whenever a file under it
is added, removed or changed.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from tsf_mcp import config
from tsf_mcp.sync import read_manifest
from tsf_mcp.text import tokenize

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)
TRIGGER_RE = re.compile(r'"([^"]{3,120})"')
NUMBERED_RE = re.compile(r"^\s*(?:#{3,4}\s*)?(\d+)\.\s+(.*)$")  # "1. step" or "### 1. Step"
REVIEW_GATE_RE = re.compile(r"human review", re.IGNORECASE)
BULLET_RE = re.compile(r"^\s*[-*]\s+(.*)$")
BOLD_LEAD_RE = re.compile(r"^\*\*(.+?)\*\*\s*")


@dataclass
class Skill:
    name: str
    title: str
    description: str
    license: str
    metadata: dict[str, Any]
    kind: str  # "stlc" or "pack"
    phase: str | None
    phase_number: int | None
    pack: str | None
    category: str  # display label: STLC phase name or pack label
    rel_dir: str  # folder relative to the skills root
    body: str
    raw: str
    intro: str
    sections: dict[str, str]
    when_to_use: list[str]
    workflow: list[str]
    guardrails: list[str]
    output_shape: str
    triggers: list[str]
    files: list[str]
    source: str = "local"  # "upstream" (synced from GitHub) or "local"
    tokens: dict[str, list[str]] = field(default_factory=dict)

    @property
    def has_review_gate(self) -> bool:
        return any(REVIEW_GATE_RE.search(step) for step in self.workflow)

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "category": self.category,
            "kind": self.kind,
            "phase": self.phase,
            "pack": self.pack,
            "summary": first_sentence(self.description),
            "path": f"{self.rel_dir}/SKILL.md",
            "source": self.source,
        }

    def detail(self) -> dict[str, Any]:
        row = self.summary()
        row.update(
            description=self.description,
            license=self.license,
            metadata=self.metadata,
            triggers=self.triggers,
            when_to_use=self.when_to_use,
            workflow=self.workflow,
            output_shape=self.output_shape,
            guardrails=self.guardrails,
            supporting_files=self.files,
            human_review_gate=self.has_review_gate,
        )
        return row


def first_sentence(text: str) -> str:
    match = re.match(r"(.+?[.!?])(\s|$)", text.strip())
    return (match.group(1) if match else text).strip()


def split_sections(body: str) -> tuple[str, str, dict[str, str]]:
    """Return (title, intro, {section heading: content}) for a markdown body. Code fences are respected."""
    title, intro_lines, sections, current = "", [], {}, None
    in_fence = False
    for line in body.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
        if not in_fence and line.startswith("# ") and not title:
            title = line[2:].strip()
            continue
        if not in_fence and line.startswith("## "):
            current = line[3:].strip()
            sections[current] = ""
            continue
        if current is None:
            intro_lines.append(line)
        else:
            sections[current] += line + "\n"
    return title, "\n".join(intro_lines).strip(), {k: v.strip() for k, v in sections.items()}


def list_items(text: str, numbered: bool) -> list[str]:
    """Collect list items (with wrapped continuation lines) from a section."""
    items: list[str] = []
    pattern = NUMBERED_RE if numbered else BULLET_RE
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = pattern.match(line)
        if match:
            items.append(match.group(match.lastindex).strip())
        elif items and line.startswith((" ", "\t")) and line.strip() and not (BULLET_RE.match(line) and numbered):
            items[-1] += " " + line.strip()
        elif numbered and items and BULLET_RE.match(line):
            items[-1] += " " + BULLET_RE.match(line).group(1).strip()
    return items


def find_section(sections: dict[str, str], *names: str) -> str:
    """Match headings by prefix so 'Workflow (follow in order)' counts as 'workflow'."""
    for heading, content in sections.items():
        if heading.lower().startswith(names):
            return content
    return ""


def fenced_block(text: str) -> str:
    match = re.search(r"```[^\n]*\n(.*?)```", text, re.DOTALL)
    return match.group(1).rstrip() if match else text.strip()


def parse_skill(skill_file: Path, root: Path, upstream_files: set[str]) -> tuple[Skill | None, list[str]]:
    rel_dir = skill_file.parent.relative_to(root).as_posix()
    problems: list[str] = []
    raw = skill_file.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(raw)
    if not match:
        return None, [f"{rel_dir}: missing YAML frontmatter"]
    try:
        front = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        return None, [f"{rel_dir}: invalid YAML frontmatter ({exc.__class__.__name__})"]
    if not isinstance(front, dict) or not front.get("name"):
        return None, [f"{rel_dir}: frontmatter has no name"]

    body = match.group(2)
    metadata = front.get("metadata") or {}
    phase = metadata.get("stlc-phase")
    pack = metadata.get("pack")
    phase_number = config.STLC_PHASES.index(phase) + 1 if phase in config.STLC_PHASES else None
    kind = "stlc" if phase else "pack"
    category = phase or config.PACK_LABELS.get(str(pack), str(pack or "Uncategorized").title())
    title, intro, sections = split_sections(body)
    description = " ".join(str(front.get("description", "")).split())

    files = sorted(
        p.relative_to(skill_file.parent).as_posix()
        for p in skill_file.parent.rglob("*")
        if p.is_file() and p.name != "SKILL.md" and not p.name.startswith(".")
    )
    skill = Skill(
        name=str(front["name"]).strip(),
        title=title or str(front["name"]),
        description=description,
        license=str(front.get("license", "")),
        metadata=metadata,
        kind=kind,
        phase=phase,
        phase_number=phase_number,
        pack=str(pack) if pack else None,
        category=category,
        rel_dir=rel_dir,
        body=body.strip(),
        raw=raw,
        intro=intro,
        sections=sections,
        when_to_use=list_items(find_section(sections, "when to use"), numbered=False),
        workflow=list_items(find_section(sections, "workflow"), numbered=True),
        guardrails=list_items(find_section(sections, "guardrails"), numbered=False),
        output_shape=fenced_block(find_section(sections, "output shape", "output")),
        triggers=TRIGGER_RE.findall(description),
        files=files,
        source="upstream" if f"{rel_dir}/SKILL.md" in upstream_files else "local",
    )
    skill.tokens = {
        "name": tokenize(skill.name.replace("-", " ")),
        "title": tokenize(skill.title),
        "category": tokenize(f"{skill.category} {skill.pack or ''} {rel_dir.replace('/', ' ').replace('-', ' ')}"),
        "description": tokenize(description),
        "triggers": tokenize(" ".join(skill.triggers)),
        "headings": tokenize(" ".join(skill.when_to_use)),
        "body": tokenize(body),
    }
    return skill, problems


class Catalog:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or config.skills_dir()).resolve()
        self._signature: tuple | None = None
        self.load()

    def _compute_signature(self) -> tuple:
        entries = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for name in filenames:
                try:
                    stat = os.stat(os.path.join(dirpath, name))
                except FileNotFoundError:
                    continue
                entries.append((dirpath, name, stat.st_mtime_ns, stat.st_size))
        return tuple(sorted(entries))

    def load(self) -> None:
        if not self.root.exists():
            raise RuntimeError(f"Skills folder not found at {self.root}. Set TSF_SKILLS_DIR or run `tsf-mcp sync`.")
        manifest = read_manifest(self.root) or {}
        self.manifest = manifest
        upstream_files = set(manifest.get("files", []))
        self.load_problems: list[str] = []
        skills: dict[str, Skill] = {}
        for skill_file in sorted(self.root.rglob("SKILL.md")):
            if any(part.startswith(".") for part in skill_file.relative_to(self.root).parts):
                continue
            skill, problems = parse_skill(skill_file, self.root, upstream_files)
            self.load_problems.extend(problems)
            if skill is None:
                continue
            if skill.name in skills:
                self.load_problems.append(f"{skill.rel_dir}: duplicate skill name '{skill.name}' (also at {skills[skill.name].rel_dir})")
                continue
            skills[skill.name] = skill
        self.skills = dict(sorted(skills.items(), key=lambda item: sort_key(item[1])))
        self._signature = self._compute_signature()
        self._derived: dict[str, Any] = {}

    def ensure_fresh(self) -> None:
        if self._compute_signature() != self._signature:
            self.load()

    def get(self, name: str) -> Skill | None:
        return self.skills.get(name.strip().lower())

    def categories(self) -> dict[str, list[Skill]]:
        groups: dict[str, list[Skill]] = {}
        for skill in self.skills.values():
            groups.setdefault(skill.category, []).append(skill)
        return groups


def sort_key(skill: Skill) -> tuple:
    if skill.kind == "stlc":
        return (0, skill.phase_number or 99, skill.name)
    order = list(config.PACK_LABELS)
    return (1, order.index(skill.pack) if skill.pack in order else 99, skill.name)
