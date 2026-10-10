"""Score test cases and pick a ranked, feature-diverse shortlist."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from tc_mcp import config
from tc_mcp.models import TestCase

ORDINALS = {1: "1st", 2: "2nd", 3: "3rd"}


@dataclass
class Ranked:
    tc: TestCase
    score: int
    rank: int
    reason: str

    def as_dict(self, detail: str = "compact") -> dict:
        row = self.tc.view(detail)
        row.update(rank=self.rank, score=self.score, rank_reason=self.reason)
        return row


def base_score(tc: TestCase, prefer_browser: str | None = None, prefer_device: str | None = None) -> int:
    score = (
        config.PRIORITY_WEIGHT.get(tc.priority, 0)
        + config.STATUS_WEIGHT.get(tc.status, 0)
        + config.TYPE_WEIGHT.get(tc.test_type, 0)
    )
    if prefer_browser and tc.browser == prefer_browser:
        score += 1
    if prefer_device and tc.device == prefer_device:
        score += 1
    return score


def best_per_scenario(rows: list[TestCase], **prefs: str | None) -> list[TestCase]:
    """Keep the highest-scoring variant of each scenario (same Summary)."""
    best: dict[str, TestCase] = {}
    for tc in rows:
        current = best.get(tc.scenario)
        if current is None or (base_score(tc, **prefs), -tc.key_number) > (base_score(current, **prefs), -current.key_number):
            best[tc.scenario] = tc
    return list(best.values())


def rank(
    rows: list[TestCase],
    count: int,
    *,
    unique_scenarios: bool = True,
    per_feature: int | None = None,
    prefer_browser: str | None = None,
    prefer_device: str | None = None,
) -> list[Ranked]:
    """Greedy pick: at each step take the best candidate after subtracting a penalty for
    every test already picked from the same feature. This spreads the shortlist across
    features without letting a Low test jump ahead of a Highest one."""
    prefs = {"prefer_browser": prefer_browser, "prefer_device": prefer_device}
    pool = best_per_scenario(rows, **prefs) if unique_scenarios else list(rows)

    queues: dict[tuple[str, str], list[tuple[int, TestCase]]] = defaultdict(list)
    for tc in pool:
        queues[(tc.module, tc.feature)].append((base_score(tc, **prefs), tc))
    for queue in queues.values():
        queue.sort(key=lambda item: (-item[0], item[1].key_number))

    picked_per_feature: dict[tuple[str, str], int] = defaultdict(int)
    heads = {feature: 0 for feature in queues}
    result: list[Ranked] = []
    while len(result) < count:
        best_feature, best_effective, best_item = None, None, None
        for feature, position in heads.items():
            queue = queues[feature]
            if position >= len(queue):
                continue
            if per_feature is not None and picked_per_feature[feature] >= per_feature:
                continue
            score, tc = queue[position]
            effective = score - config.FEATURE_DIVERSITY_PENALTY * picked_per_feature[feature]
            candidate = (effective, -tc.key_number)
            if best_effective is None or candidate > best_effective:
                best_feature, best_effective, best_item = feature, candidate, (score, tc)
        if best_item is None:
            break
        score, tc = best_item
        heads[best_feature] += 1
        picked_per_feature[best_feature] += 1
        nth = picked_per_feature[best_feature]
        reason = (
            f"{tc.priority} · {tc.status} · {tc.test_type} (score {score}); "
            f"{ORDINALS.get(nth, f'{nth}th')} pick for feature '{tc.feature}'"
        )
        result.append(Ranked(tc=tc, score=score, rank=len(result) + 1, reason=reason))
    return result
