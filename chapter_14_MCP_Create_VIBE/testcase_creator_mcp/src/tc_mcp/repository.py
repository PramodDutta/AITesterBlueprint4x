"""Load the test case CSV, clean it, index it, and manage the write overlay.

The source CSV is never modified. New and edited tests are appended to an overlay CSV
(same columns plus 'Feature'); when a key appears in both, the last overlay row wins.
"""

from __future__ import annotations

import contextlib
import csv
import re
from collections import Counter, defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from fastmcp.exceptions import ToolError

from tc_mcp import config
from tc_mcp.models import (
    CSV_COLUMNS,
    OVERLAY_COLUMNS,
    PRIORITY_RANK,
    STATUS_ORDER,
    TEST_TYPE_ORDER,
    TestCase,
    TestFilter,
)
from tc_mcp.resolver import resolve_many, resolve_modules

try:  # POSIX file locking; Windows falls back to no lock.
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

FEATURE_RE = re.compile(r"\bthe (.+?) in the .+? module\b")
SUMMARY_RE = re.compile(r"^\[(?P<module>.+?)\] (?P<type>.+?): (?P<action>.+)$")
STEP_SPLIT_RE = re.compile(r"\s+\|\s+(?=\d+\.\s)")
STEP_NUMBER_RE = re.compile(r"^\s*\d+\.\s*")
KEY_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")
KEEPER_STATUS_PREFERENCE = {"Automated": 0, "Ready": 1, "Draft": 2, "Deprecated": 3}


def module_slug(module: str) -> str:
    name = module.split(" / ")[0].replace("/", "")
    return re.sub(r"\s+", "-", name.strip().lower())


def type_slug(test_type: str) -> str:
    return re.sub(r"[\s/]+", "-", test_type.strip().lower())


def generate_labels(module: str, test_type: str) -> list[str]:
    return list(dict.fromkeys([module_slug(module), type_slug(test_type), "regression"]))


def normalize_labels(raw: str, module: str) -> list[str]:
    """Rebuild labels: the first raw token is a module slug that the export mangled
    (A/B Testing became 'a'), so replace it, keep the rest, and drop repeats."""
    tokens = raw.split()
    return list(dict.fromkeys([module_slug(module), *tokens[1:]]))


def parse_steps(raw: str) -> list[str]:
    parts = STEP_SPLIT_RE.split(raw.strip())
    if len(parts) == 1 and " | " in raw:
        parts = raw.split(" | ")
    return [STEP_NUMBER_RE.sub("", part).strip() for part in parts if part.strip()]


def extract_feature(description: str, summary: str) -> str:
    match = FEATURE_RE.search(description)
    if match:
        return match.group(1).strip()
    summary_match = SUMMARY_RE.match(summary)
    return summary_match.group("action").strip() if summary_match else "unknown"


def keeper_sort_key(tc: TestCase) -> tuple[int, int]:
    return (KEEPER_STATUS_PREFERENCE.get(tc.status, 9), tc.key_number)


def _file_signature(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    return (stat.st_mtime_ns, stat.st_size)


@contextlib.contextmanager
def _locked(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with open(lock_path, "w") as handle:
        if fcntl is not None:
            fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle, fcntl.LOCK_UN)


class Repository:
    def __init__(self, data_path: Path | None = None, overlay_path: Path | None = None) -> None:
        self.data_path = data_path or config.data_path()
        self.overlay_path = overlay_path or config.overlay_path()
        self._signature: tuple[Any, Any] | None = None
        self.load()

    # ------------------------------------------------------------------ loading

    def load(self) -> None:
        if not self.data_path.exists():
            raise RuntimeError(
                f"Test case CSV not found at {self.data_path}. Set TC_MCP_DATA_PATH to the CSV location."
            )
        self.load_warnings: list[str] = []
        base = self._read_csv(self.data_path, source="base")
        overlay = self._read_csv(self.overlay_path, source="overlay") if self.overlay_path.exists() else []

        by_key: dict[str, TestCase] = {tc.key: tc for tc in base}
        for tc in overlay:  # later rows win, so an edit replaces the original
            by_key[tc.key] = tc
        self.rows: list[TestCase] = sorted(by_key.values(), key=lambda tc: tc.key_number)
        self.by_key = {tc.key: tc for tc in self.rows}
        self.overlay_count = len({tc.key for tc in overlay})
        self.base_count = len(base)
        self._flag_duplicates()
        self._build_indexes()
        self._signature = (_file_signature(self.data_path), _file_signature(self.overlay_path))

    def ensure_fresh(self) -> None:
        """Reload when the source CSV or the overlay changed on disk (e.g. another client wrote)."""
        current = (_file_signature(self.data_path), _file_signature(self.overlay_path))
        if current != self._signature:
            self.load()

    def _read_csv(self, path: Path, source: str) -> list[TestCase]:
        with open(path, newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            missing = [c for c in CSV_COLUMNS if c not in (reader.fieldnames or [])]
            if missing:
                raise RuntimeError(f"{path.name} is missing columns: {', '.join(missing)}")
            rows: list[TestCase] = []
            for line_no, raw in enumerate(reader, start=2):
                tc = self._parse_row(raw, source, path.name, line_no)
                if tc is not None:
                    rows.append(tc)
        return rows

    def _parse_row(self, raw: dict[str, str], source: str, file_name: str, line_no: int) -> TestCase | None:
        get = lambda col: (raw.get(col) or "").strip()  # noqa: E731
        key, priority, status = get("Issue Key"), get("Priority"), get("Status")
        problems = []
        if not KEY_RE.match(key):
            problems.append(f"bad Issue Key {key!r}")
        if priority not in PRIORITY_RANK:
            problems.append(f"unknown Priority {priority!r}")
        if status not in STATUS_ORDER:
            problems.append(f"unknown Status {status!r}")
        steps = parse_steps(get("Steps"))
        if not steps:
            problems.append("no Steps")
        if problems:
            self.load_warnings.append(f"{file_name} line {line_no} skipped: {'; '.join(problems)}")
            return None
        module = get("Component")
        description = get("Description")
        summary = get("Summary")
        return TestCase(
            key=key,
            summary=summary,
            description=description,
            priority=priority,
            module=module,
            labels=normalize_labels(get("Labels"), module),
            test_type=get("Test Type"),
            preconditions=get("Preconditions"),
            steps=steps,
            expected_result=get("Expected Result"),
            browser=get("Browser"),
            device=get("Device"),
            status=status,
            feature=get("Feature") or extract_feature(description, summary),
            issue_type=get("Issue Type") or "Test",
            source=source,
        )

    def _flag_duplicates(self) -> None:
        groups: dict[tuple[str, str, str], list[TestCase]] = defaultdict(list)
        for tc in self.rows:
            tc.duplicate_of = None
            groups[(tc.scenario, tc.browser.casefold(), tc.device.casefold())].append(tc)
        self.exact_duplicate_groups = [g for g in groups.values() if len(g) > 1]
        for group in self.exact_duplicate_groups:
            keeper = min(group, key=keeper_sort_key)
            for tc in group:
                if tc is not keeper:
                    tc.duplicate_of = keeper.key

    def _build_indexes(self) -> None:
        self.modules = sorted({tc.module for tc in self.rows})
        features: dict[str, Counter[str]] = defaultdict(Counter)
        for tc in self.rows:
            features[tc.module][tc.feature] += 1
        self.features_by_module = {m: sorted(features[m]) for m in self.modules}
        self.feature_counts = {m: dict(features[m]) for m in self.modules}
        self.all_features = sorted({f for fs in self.features_by_module.values() for f in fs})
        self.browsers = sorted({tc.browser for tc in self.rows})
        self.devices = sorted({tc.device for tc in self.rows})
        present_types = {tc.test_type for tc in self.rows}
        self.test_types = [t for t in TEST_TYPE_ORDER if t in present_types] + sorted(present_types - set(TEST_TYPE_ORDER))
        self.labels = sorted({label for tc in self.rows for label in tc.labels})
        self.expected_result_counts = Counter(tc.expected_result.casefold() for tc in self.rows)
        self.scenario_count = len({tc.scenario for tc in self.rows})
        self.key_prefix = self.rows[0].key.rsplit("-", 1)[0] if self.rows else "TC"

    # ------------------------------------------------------------------ queries

    def get(self, key: str) -> TestCase | None:
        return self.by_key.get(self.normalize_key(key))

    def normalize_key(self, key: str) -> str:
        key = key.strip().upper()
        if key.isdigit():
            key = f"{self.key_prefix}-{key}"
        return key

    def live_rows(self) -> list[TestCase]:
        return [tc for tc in self.rows if tc.is_live]

    def filter(self, flt: TestFilter | None) -> tuple[list[TestCase], dict[str, Any]]:
        """Apply a TestFilter. Returns matching rows (key order) and the resolved filters."""
        flt = flt or TestFilter()
        applied: dict[str, Any] = {}

        modules = resolve_modules(flt.module, self.modules)
        if modules:
            applied["module"] = modules
        features = None
        if flt.feature is not None:
            pool = sorted({f for m in (modules or self.modules) for f in self.features_by_module[m]})
            features = resolve_many(flt.feature, pool, "feature")
            if features:
                applied["feature"] = features
        browsers = resolve_many(flt.browser, self.browsers, "browser")
        if browsers:
            applied["browser"] = browsers
        devices = resolve_many(flt.device, self.devices, "device")
        if devices:
            applied["device"] = devices

        priorities = set(flt.priority) if flt.priority else set(PRIORITY_RANK)
        if flt.min_priority and flt.max_priority and PRIORITY_RANK[flt.min_priority] > PRIORITY_RANK[flt.max_priority]:
            raise ToolError(
                f"min_priority {flt.min_priority!r} is above max_priority {flt.max_priority!r}. Order: Low < Medium < High < Highest."
            )
        if flt.min_priority:
            priorities = {p for p in priorities if PRIORITY_RANK[p] >= PRIORITY_RANK[flt.min_priority]}
        if flt.max_priority:
            priorities = {p for p in priorities if PRIORITY_RANK[p] <= PRIORITY_RANK[flt.max_priority]}
        if priorities != set(PRIORITY_RANK):
            applied["priority"] = sorted(priorities, key=lambda p: -PRIORITY_RANK[p])

        if flt.status:
            statuses = set(flt.status)
        elif flt.include_deprecated:
            statuses = set(STATUS_ORDER)
        else:
            statuses = set(STATUS_ORDER) - {"Deprecated"}
        applied["status"] = [s for s in STATUS_ORDER if s in statuses]

        test_types = set(flt.test_type) if flt.test_type else None
        if test_types:
            applied["test_type"] = [t for t in TEST_TYPE_ORDER if t in test_types]
        label = flt.label.strip().casefold() if flt.label else None
        if label:
            applied["label"] = label
        if not flt.include_duplicates:
            applied["include_duplicates"] = False

        module_set = set(modules) if modules else None
        feature_set = set(features) if features else None
        browser_set = set(browsers) if browsers else None
        device_set = set(devices) if devices else None
        result = [
            tc
            for tc in self.rows
            if (module_set is None or tc.module in module_set)
            and (feature_set is None or tc.feature in feature_set)
            and tc.priority in priorities
            and tc.status in statuses
            and (test_types is None or tc.test_type in test_types)
            and (browser_set is None or tc.browser in browser_set)
            and (device_set is None or tc.device in device_set)
            and (label is None or label in tc.labels)
            and (flt.include_duplicates or tc.duplicate_of is None)
        ]
        return result, applied

    # ------------------------------------------------------------------ writes

    def write_new(self, cases: list[TestCase]) -> list[str]:
        """Assign fresh keys and append to the overlay. Allocation happens under a file lock."""
        with _locked(self.overlay_path):
            self.ensure_fresh()
            next_number = max((tc.key_number for tc in self.rows), default=0) + 1
            for offset, tc in enumerate(cases):
                tc.key = f"{self.key_prefix}-{next_number + offset}"
                tc.source = "overlay"
            self._append(cases)
        self.load()
        return [tc.key for tc in cases]

    def write_update(self, tc: TestCase) -> None:
        with _locked(self.overlay_path):
            tc.source = "overlay"
            self._append([tc])
        self.load()

    def _append(self, cases: list[TestCase]) -> None:
        new_file = not self.overlay_path.exists() or self.overlay_path.stat().st_size == 0
        with open(self.overlay_path, "a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(OVERLAY_COLUMNS))
            if new_file:
                writer.writeheader()
            for tc in cases:
                writer.writerow(tc.to_csv_row(include_feature=True))

