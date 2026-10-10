"""Rank skills for a keyword query or a plain-English task.

score = sum over query terms of  term weight x IDF x field weight, summed over the fields
the term appears in, then scaled by how many of the user's own words matched. Synonyms count
at 0.6. Fields: name 6, title 4, triggers 3, category 3, description 2, when-to-use 1.5,
body 0.5 (log of term count).
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from tsf_mcp.catalog import Catalog, Skill
from tsf_mcp.text import expand, tokenize

FIELD_WEIGHTS = {
    "name": 6.0,
    "title": 4.0,
    "triggers": 3.0,
    "category": 3.0,
    "description": 2.0,
    "headings": 1.5,
}
BODY_WEIGHT = 0.5
MIN_RELATIVE_SCORE = 0.06  # results scoring under 6% of the best hit are noise
STRONG_FIELDS = ("name", "title", "triggers", "category", "description")


@dataclass
class Hit:
    skill: Skill
    score: float
    matched_terms: list[str] = field(default_factory=list)
    matched_fields: list[str] = field(default_factory=list)
    best_trigger: str | None = None

    def as_dict(self) -> dict:
        row = self.skill.summary()
        row.update(score=round(self.score, 2), matched_terms=self.matched_terms, matched_in=self.matched_fields)
        if self.best_trigger:
            row["closest_trigger"] = self.best_trigger
        return row


class SearchIndex:
    def __init__(self, catalog: Catalog) -> None:
        self.catalog = catalog
        self.sets = {name: {f: set(tokens) for f, tokens in s.tokens.items()} for name, s in catalog.skills.items()}
        self.body_counts = {name: Counter(s.tokens["body"]) for name, s in catalog.skills.items()}
        doc_freq: Counter[str] = Counter()
        for fields in self.sets.values():
            doc_freq.update(set().union(*fields.values()))
        n = max(len(catalog.skills), 1)
        self.idf = {term: math.log(1 + n / (df + 0.5)) for term, df in doc_freq.items()}

    def score(self, skill: Skill, weights: dict[str, float], primary: list[str]) -> Hit | None:
        fields = self.sets[skill.name]
        body = self.body_counts[skill.name]
        total = 0.0
        matched_terms: set[str] = set()
        matched_fields: set[str] = set()
        for term, weight in weights.items():
            idf = self.idf.get(term)
            if idf is None:
                continue
            term_score = sum(fw for f, fw in FIELD_WEIGHTS.items() if term in fields[f])
            if body[term]:
                term_score += BODY_WEIGHT * math.log(1 + body[term])
            if term_score:
                total += weight * idf * term_score
                matched_terms.add(term)
                matched_fields.update(f for f in FIELD_WEIGHTS if term in fields[f])
        if not total:
            return None

        def strong(term: str) -> bool:
            if any(term in fields[f] for f in STRONG_FIELDS):
                return True
            return any(syn in weights and weights[syn] < 1 and any(syn in fields[f] for f in STRONG_FIELDS) for syn in _synonyms(term))

        coverage = sum(1 for t in set(primary) if strong(t)) / max(len(set(primary)), 1)
        total *= 0.3 + 0.7 * coverage**1.5
        if primary and all(t in fields["name"] or _syn_in(t, fields["name"]) for t in set(primary)):
            total *= 1.4  # every word the user typed is in the skill's name
        return Hit(skill=skill, score=total, matched_terms=sorted(matched_terms), matched_fields=sorted(matched_fields))

    def search(self, query: str, candidates: list[Skill] | None = None, limit: int = 10) -> list[Hit]:
        primary = tokenize(query)
        if not primary:
            return []
        weights = expand(primary)
        hits = []
        for skill in candidates if candidates is not None else self.catalog.skills.values():
            hit = self.score(skill, weights, primary)
            if hit:
                hits.append(hit)
        hits.sort(key=lambda h: (-h.score, h.skill.name))
        if hits:  # drop the long tail of incidental body matches
            floor = hits[0].score * MIN_RELATIVE_SCORE
            hits = [h for h in hits if h.score >= floor]
        return hits[:limit]

    def match_task(self, task: str, candidates: list[Skill] | None = None, limit: int = 3) -> list[Hit]:
        """Like search, plus a bonus for skills whose quoted trigger phrases resemble the task."""
        task_terms = set(tokenize(task))
        hits = self.search(task, candidates, limit=max(limit * 4, 12))
        for hit in hits:
            best, best_overlap = None, 0.0
            for trigger in hit.skill.triggers:
                trigger_terms = set(tokenize(trigger))
                if not trigger_terms:
                    continue
                overlap = len(task_terms & trigger_terms) / len(trigger_terms | task_terms)
                if overlap > best_overlap:
                    best, best_overlap = trigger, overlap
            hit.score *= 1 + best_overlap
            hit.best_trigger = best
        hits.sort(key=lambda h: (-h.score, h.skill.name))
        return hits[:limit]


def _synonyms(term: str) -> set[str]:
    from tsf_mcp.text import SYNONYMS

    return SYNONYMS.get(term, set())


def _syn_in(term: str, tokens: set[str]) -> bool:
    return bool(_synonyms(term) & tokens)
