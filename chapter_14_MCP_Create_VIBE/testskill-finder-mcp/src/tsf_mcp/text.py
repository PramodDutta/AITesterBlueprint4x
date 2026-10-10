"""Tokenizing, light stemming and synonym expansion for skill search."""

from __future__ import annotations

import re

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "by", "from", "at", "as",
    "is", "are", "be", "it", "this", "that", "these", "those", "my", "me", "i", "we", "our", "you",
    "your", "can", "how", "do", "does", "want", "need", "help", "find", "show", "give", "get",
    "skill", "skills", "related", "about", "some", "any", "please", "using", "use", "which", "what",
    "when", "who", "will", "would", "should", "into", "than", "then", "not", "no", "so", "if",
}

# Whole-token rewrites applied before stemming (abbreviations and irregular forms).
LEMMAS = {
    "pw": "playwright",
    "se": "selenium",
    "cy": "cypress",
    "a11y": "accessibility",
    "perf": "performance",
    "e2e": "endtoend",
    "llms": "llm",
    "genai": "llm",
    "evals": "evaluation",
    "eval": "evaluation",
    "rtm": "traceability",
    "qa": "quality",
    "ui": "ui",
    "apis": "api",
    "webdriver": "selenium",
    "testng": "testng",
    "bugs": "bug",
}

SUFFIXES = (
    ("ies", "y"),
    ("ing", ""),
    ("ions", ""),
    ("ion", ""),
    ("ers", ""),
    ("er", ""),
    ("ors", ""),
    ("or", ""),
    ("ed", ""),
    ("s", ""),
)


def stem(token: str) -> str:
    token = LEMMAS.get(token, token)
    if len(token) <= 3 or token.isdigit():
        return token
    for suffix, replacement in SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            if suffix == "s" and token.endswith(("ss", "us", "is")):
                break
            token = token[: -len(suffix)] + replacement
            if suffix in ("ing", "er", "ers", "ed") and len(token) > 3 and token[-1] == token[-2] and token[-1] not in "lsfz":
                token = token[:-1]
            break
    if len(token) > 4 and token.endswith("e"):
        token = token[:-1]
    return token


def tokenize(text: str, keep_stopwords: bool = False) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [stem(w) for w in words if (keep_stopwords or w not in STOPWORDS) and len(w) > 1 or w in LEMMAS]


# Synonym groups, written as plain words and stemmed below. Every member expands to the others.
_GROUPS = [
    ["create", "creator", "write", "writer", "generate", "generator", "build", "builder", "draft", "scaffold", "author"],
    ["bug", "defect", "issue"],
    ["api", "rest", "endpoint", "graphql"],
    ["accessibility", "wcag", "axe"],
    ["performance", "load", "stress", "k6", "jmeter", "locust", "latency"],
    ["security", "owasp", "vulnerability", "pentest"],
    ["flaky", "flake", "intermittent", "unstable"],
    ["llm", "ai", "gpt"],
    ["evaluation", "evaluate", "metric", "judge"],
    ["agent", "agentic"],
    ["strategy", "approach"],
    ["ci", "pipeline", "jenkins", "github"],
    ["locator", "selector"],
    ["report", "summary"],
    ["rca", "root", "cause"],
    ["jira", "ticket", "story"],
    ["bdd", "gherkin", "cucumber"],
    ["mock", "stub", "intercept"],
    ["mobile", "appium", "android", "ios"],
    ["traceability", "coverage"],
    ["triage", "prioritize"],
    ["review", "audit"],
]
SYNONYMS: dict[str, set[str]] = {}
for _words in _GROUPS:
    _stems = {stem(w) for w in _words}
    for _term in _stems:
        SYNONYMS.setdefault(_term, set()).update(_stems - {_term})


def expand(terms: list[str]) -> dict[str, float]:
    """Primary terms weigh 1.0; synonyms weigh 0.6 (never overriding a primary term)."""
    weights: dict[str, float] = {}
    for term in terms:
        weights[term] = 1.0
    for term in terms:
        for synonym in SYNONYMS.get(term, ()):
            weights.setdefault(synonym, 0.6)
    return weights
