"""Runtime settings for TestSkill Finder MCP."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent.parent  # testskill-finder-mcp/
REPO_SKILLS_DIR = PROJECT_DIR / "skills"  # source of truth when running from a clone
BUNDLED_SKILLS_DIR = PACKAGE_DIR / "skills"  # present only in a built wheel

# Upstream catalog that `sync` downloads from.
UPSTREAM_REPO = "PramodDutta/skillmasterclass"
UPSTREAM_REF = "main"
UPSTREAM_PATH = "skillmasterclass/skills"
MANIFEST_NAME = ".upstream.json"

# Sync safety limits.
SYNC_MAX_FILES = 500
SYNC_MAX_FILE_BYTES = 1_000_000

# Response limits.
MAX_RESULTS = 50
DEFAULT_RESULTS = 10
MAX_FILE_CHARS = 60_000

# STLC phase order, used for chains and sorting.
STLC_PHASES = (
    "Requirement Analysis",
    "Test Planning",
    "Test Design",
    "Test Case Development",
    "Test Execution",
    "Defect Management",
    "Test Closure",
)
PHASE_FOLDERS = {
    "Requirement Analysis": "01-requirement-analysis",
    "Test Planning": "02-test-planning",
    "Test Design": "03-test-design",
    "Test Case Development": "04-test-case-development",
    "Test Execution": "05-test-execution",
    "Defect Management": "06-defect-management",
    "Test Closure": "07-test-closure",
}
# Folder for each pack under framework-packs/ (defaults to "<pack>-pack").
PACK_FOLDERS = {"ai-agents": "ai-agent-pack"}


def pack_folder(pack: str) -> str:
    return PACK_FOLDERS.get(pack, f"{pack}-pack")


PACK_LABELS = {
    "playwright": "Playwright",
    "selenium": "Selenium",
    "cypress": "Cypress",
    "api": "API Testing",
    "performance": "Performance",
    "security": "Security",
    "llm-eval": "LLM Evaluation",
    "ai-agents": "AI Agents",
    "mcp": "MCP",
    "automation": "Automation",
}


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def skills_dir() -> Path:
    env = os.getenv("TSF_SKILLS_DIR")
    if env:
        return Path(env).expanduser().resolve()
    if REPO_SKILLS_DIR.exists():
        return REPO_SKILLS_DIR
    return BUNDLED_SKILLS_DIR


def allow_write() -> bool:
    return _env_bool("TSF_ALLOW_WRITE", default=False)


def transport() -> str:
    return os.getenv("TSF_TRANSPORT", "stdio").strip().lower()


def host() -> str:
    return os.getenv("TSF_HOST", "127.0.0.1")


def port() -> int:
    return int(os.getenv("TSF_PORT", "8110"))


def auth_token() -> str | None:
    return os.getenv("TSF_AUTH_TOKEN") or None


def github_token() -> str | None:
    return os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or None
