"""Runtime settings, ranking weights and suite rules for TC MCP.

Everything tunable lives here so the tools stay free of magic numbers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent.parent  # testcase_creator_mcp/
CSV_NAME = "vwo_5000_test_cases.csv"
BUNDLED_CSV = PACKAGE_DIR / "data" / CSV_NAME  # present only in a built wheel
REPO_CSV = PROJECT_DIR.parent / "data" / CSV_NAME  # chapter_14_MCP_Create_VIBE/data/
USER_HOME_DIR = Path.home() / ".tc_mcp"

# Response size limits (an average full row is ~190 tokens, a compact row ~45).
MAX_COMPACT_ROWS = 100
MAX_FULL_ROWS = 25
DEFAULT_LIMIT = 20
INLINE_EXPORT_ROWS = 50
MAX_SUITE_TESTS = 300

# Ranking: score = priority + status + test type, minus a per-feature diversity penalty.
PRIORITY_WEIGHT = {"Highest": 40, "High": 30, "Medium": 20, "Low": 10}
STATUS_WEIGHT = {"Ready": 10, "Automated": 8, "Draft": 2, "Deprecated": 0}
TYPE_WEIGHT = {
    "Security": 6,
    "Functional": 6,
    "Negative": 5,
    "API": 5,
    "Regression": 4,
    "Boundary": 4,
    "Performance": 3,
    "UI/UX": 2,
    "Accessibility": 2,
}
FEATURE_DIVERSITY_PENALTY = 8  # subtracted per test already picked from the same feature

# How suitable each test type is for automation (used by get_automation_candidates).
AUTOMATION_TYPE_WEIGHT = {
    "API": 8,
    "Regression": 7,
    "Functional": 6,
    "Boundary": 6,
    "Negative": 5,
    "Security": 4,
    "Performance": 3,
    "UI/UX": 2,
    "Accessibility": 1,
}

DEFAULT_MINUTES_MANUAL = 10.0
DEFAULT_MINUTES_AUTOMATED = 1.0


@dataclass(frozen=True)
class SuiteRule:
    priorities: tuple[str, ...]
    test_types: tuple[str, ...] | None  # None means every type
    per_feature: int | None  # None means no cap
    unique_scenarios: bool
    preferred_browser: str | None = None
    preferred_device: str | None = None
    relax_priorities: tuple[str, ...] = field(default_factory=tuple)


SUITE_RULES: dict[str, SuiteRule] = {
    "smoke": SuiteRule(
        priorities=("Highest",),
        test_types=("Functional", "API", "Security"),
        per_feature=1,
        unique_scenarios=True,
        preferred_browser="Chrome 148",
        preferred_device="desktop",
        relax_priorities=("High",),
    ),
    "sanity": SuiteRule(
        priorities=("Highest", "High"),
        test_types=("Functional", "Negative", "API"),
        per_feature=2,
        unique_scenarios=True,
        relax_priorities=("Medium",),
    ),
    "regression": SuiteRule(
        priorities=("Highest", "High", "Medium", "Low"),
        test_types=None,
        per_feature=None,
        unique_scenarios=False,
    ),
}


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _running_from_source() -> bool:
    return (PROJECT_DIR / "pyproject.toml").exists()


def data_path() -> Path:
    env = os.getenv("TC_MCP_DATA_PATH")
    if env:
        return Path(env).expanduser().resolve()
    if REPO_CSV.exists():
        return REPO_CSV
    return BUNDLED_CSV


def overlay_path() -> Path:
    env = os.getenv("TC_MCP_OVERLAY_PATH")
    if env:
        return Path(env).expanduser().resolve()
    source = data_path()
    if source == BUNDLED_CSV:
        return USER_HOME_DIR / "tc_additions.csv"
    return source.parent / "tc_additions.csv"


def export_dir() -> Path:
    env = os.getenv("TC_MCP_EXPORT_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return PROJECT_DIR / "exports" if _running_from_source() else USER_HOME_DIR / "exports"


def allow_write() -> bool:
    return _env_bool("TC_MCP_ALLOW_WRITE", default=False)


def transport() -> str:
    return os.getenv("TC_MCP_TRANSPORT", "stdio").strip().lower()


def host() -> str:
    return os.getenv("TC_MCP_HOST", "127.0.0.1")


def port() -> int:
    return int(os.getenv("TC_MCP_PORT", "8000"))


def auth_token() -> str | None:
    return os.getenv("TC_MCP_AUTH_TOKEN") or None
