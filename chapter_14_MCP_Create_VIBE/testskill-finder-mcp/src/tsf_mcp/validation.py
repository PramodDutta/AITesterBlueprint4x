"""Check that a skill follows the catalog's SKILL.md format."""

from __future__ import annotations

import re
from typing import Any

import yaml

from tsf_mcp import config
from tsf_mcp.catalog import FRONTMATTER_RE, REVIEW_GATE_RE, find_section, list_items, split_sections

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
REQUIRED_SECTIONS = ("when to use", "workflow", "output shape", "guardrails")


def validate_text(raw: str, folder_name: str | None = None, rel_dir: str | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    match = FRONTMATTER_RE.match(raw)
    if not match:
        return {"valid": False, "errors": ["Missing YAML frontmatter between '---' lines at the top of the file."], "warnings": []}
    try:
        front = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        return {"valid": False, "errors": [f"Frontmatter is not valid YAML: {exc}"], "warnings": []}
    if not isinstance(front, dict):
        return {"valid": False, "errors": ["Frontmatter must be a YAML mapping."], "warnings": []}

    name = str(front.get("name") or "")
    if not name:
        errors.append("Frontmatter needs 'name'.")
    elif not NAME_RE.match(name) or len(name) > 64:
        errors.append(f"name '{name}' must be kebab-case (a-z, 0-9, hyphens), at most 64 characters.")
    if folder_name and name and name != folder_name:
        errors.append(f"name '{name}' must match its folder name '{folder_name}'.")

    description = " ".join(str(front.get("description") or "").split())
    if not description:
        errors.append("Frontmatter needs 'description'.")
    else:
        if "use when" not in description.lower():
            errors.append("description must say when to use the skill ('Use when ...') so agents know when to load it.")
        if len(description) > 1024:
            errors.append(f"description is {len(description)} characters; keep it under 1024.")
        if len(description) < 80:
            warnings.append("description is very short; add trigger phrases and what the skill produces.")
        if not re.search(r'"[^"]{3,}"', description):
            warnings.append('description has no quoted trigger phrases like "write a test plan for JIRA-1".')

    if not front.get("license"):
        warnings.append("Frontmatter has no 'license'.")
    metadata = front.get("metadata") or {}
    if not isinstance(metadata, dict):
        errors.append("'metadata' must be a mapping.")
        metadata = {}
    if not metadata.get("author"):
        warnings.append("metadata.author is missing.")
    if not SEMVER_RE.match(str(metadata.get("version", ""))):
        warnings.append("metadata.version should be semantic, e.g. 1.0.0.")
    phase, pack = metadata.get("stlc-phase"), metadata.get("pack")
    if bool(phase) == bool(pack):
        errors.append("metadata needs exactly one of 'stlc-phase' or 'pack'.")
    if phase and phase not in config.STLC_PHASES:
        errors.append(f"stlc-phase '{phase}' is not one of: {', '.join(config.STLC_PHASES)}.")
    if pack and str(pack) not in config.PACK_LABELS:
        warnings.append(f"pack '{pack}' is new; known packs: {', '.join(config.PACK_LABELS)}.")
    if rel_dir and phase in config.PHASE_FOLDERS and not rel_dir.startswith(config.PHASE_FOLDERS[phase] + "/"):
        warnings.append(f"An '{phase}' skill normally lives under {config.PHASE_FOLDERS[phase]}/.")
    if rel_dir and pack and not rel_dir.startswith(f"framework-packs/{config.pack_folder(str(pack))}/"):
        warnings.append(f"A '{pack}' pack skill normally lives under framework-packs/{config.pack_folder(str(pack))}/.")

    title, _, sections = split_sections(match.group(2))
    if not title:
        errors.append("Body needs a '# Title' heading.")
    present = {required for required in REQUIRED_SECTIONS if any(h.lower().startswith(required) for h in sections)}
    for required in REQUIRED_SECTIONS:
        if required not in present:
            errors.append(f"Body needs a '## {required.title()}' section.")
    workflow = list_items(find_section(sections, "workflow"), numbered=True)
    if "workflow" in present and len(workflow) < 3:
        warnings.append("Workflow should have at least 3 numbered steps.")
    if phase and not any(REVIEW_GATE_RE.search(step) for step in workflow):
        warnings.append("Lifecycle skills end their workflow with a 'HUMAN REVIEW GATE (mandatory)' step.")
    if "output shape" in present and "```" not in find_section(sections, "output shape"):
        warnings.append("Output shape should contain a fenced example.")
    if "guardrails" in present and not any("never" in g.lower() for g in list_items(find_section(sections, "guardrails"), numbered=False)):
        warnings.append("Guardrails usually include a 'never fabricate ...' rule.")

    return {"valid": not errors, "errors": errors, "warnings": warnings, "name": name or None}
