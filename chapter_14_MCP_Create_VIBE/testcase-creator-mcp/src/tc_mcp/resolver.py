"""Turn loose user input ('ab testing', 'safari', 'ios') into exact catalog values."""

from __future__ import annotations

import difflib
import re
from collections.abc import Iterable

from fastmcp.exceptions import ToolError

# Normalized alias -> canonical module name. Keys go through _norm() before lookup.
MODULE_ALIASES: dict[str, str] = {
    "ab": "A/B Testing",
    "abtest": "A/B Testing",
    "abtests": "A/B Testing",
    "abtesting": "A/B Testing",
    "split": "Split URL Testing",
    "spliturl": "Split URL Testing",
    "mvt": "Multivariate Testing",
    "multivariate": "Multivariate Testing",
    "sdk": "SDK / Server-Side API",
    "serverside": "SDK / Server-Side API",
    "serversideapi": "SDK / Server-Side API",
    "api": "SDK / Server-Side API",
    "billing": "Account & Billing",
    "account": "Account & Billing",
    "accountbilling": "Account & Billing",
    "accountandbilling": "Account & Billing",
    "users": "User Management",
    "user": "User Management",
    "usermgmt": "User Management",
    "goals": "Goals & Metrics",
    "metrics": "Goals & Metrics",
    "goalsandmetrics": "Goals & Metrics",
    "recordings": "Session Recordings",
    "sessionrecording": "Session Recordings",
    "sessionreplay": "Session Recordings",
    "replay": "Session Recordings",
    "forms": "Form Analytics",
    "form": "Form Analytics",
    "rollout": "Feature Rollout",
    "featureflags": "Feature Rollout",
    "flags": "Feature Rollout",
    "personalisation": "Personalization",
    "integration": "Integrations",
    "heatmap": "Heatmaps",
    "funnel": "Funnels",
    "report": "Reports",
    "survey": "Surveys",
    "snippet": "SmartCode",
}


def _norm(value: str) -> str:
    value = value.casefold().replace("&", "and")
    return re.sub(r"[^a-z0-9]", "", value)


def resolve_value(raw: str, allowed: Iterable[str], field: str, aliases: dict[str, str] | None = None) -> str:
    """Resolve one value against the allowed list, or raise a ToolError with suggestions."""
    allowed = list(allowed)
    text = raw.strip()
    if not text:
        raise ToolError(f"Empty {field}. Valid values: {', '.join(allowed)}")

    lowered = {a.casefold(): a for a in allowed}
    if text.casefold() in lowered:
        return lowered[text.casefold()]

    normalized = {_norm(a): a for a in allowed}
    key = _norm(text)
    if key in normalized:
        return normalized[key]
    if aliases and key in aliases and aliases[key] in allowed:
        return aliases[key]

    # Unique partial match: 'safari' -> 'Safari 19', 'ios' -> 'mobile (iOS)'.
    if key:
        partial = [a for a in allowed if key in _norm(a)]
        if len(partial) == 1:
            return partial[0]

    suggestions = difflib.get_close_matches(text, allowed, n=3, cutoff=0.5)
    hint = f" Did you mean {' or '.join(repr(s) for s in suggestions)}?" if suggestions else ""
    raise ToolError(f"Unknown {field} {text!r}.{hint} Valid values: {', '.join(allowed)}")


def resolve_many(raw: str | list[str] | None, allowed: Iterable[str], field: str, aliases: dict[str, str] | None = None) -> list[str] | None:
    if raw is None:
        return None
    values = [raw] if isinstance(raw, str) else raw
    allowed = list(allowed)
    resolved: list[str] = []
    for value in values:
        if isinstance(value, str) and value.strip().casefold() == "all":
            return None
        item = resolve_value(value, allowed, field, aliases)
        if item not in resolved:
            resolved.append(item)
    return resolved or None


def resolve_module(raw: str, modules: Iterable[str]) -> str:
    return resolve_value(raw, modules, "module", MODULE_ALIASES)


def resolve_modules(raw: str | list[str] | None, modules: Iterable[str]) -> list[str] | None:
    return resolve_many(raw, modules, "module", MODULE_ALIASES)
