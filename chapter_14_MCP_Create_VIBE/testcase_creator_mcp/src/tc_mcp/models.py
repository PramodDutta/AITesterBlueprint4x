"""Data models: the in-memory TestCase record and the Pydantic inputs tools accept."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

Priority = Literal["Highest", "High", "Medium", "Low"]
Status = Literal["Ready", "Automated", "Draft", "Deprecated"]
TestType = Literal[
    "Functional",
    "Negative",
    "UI/UX",
    "API",
    "Boundary",
    "Regression",
    "Security",
    "Accessibility",
    "Performance",
]

PRIORITY_ORDER: tuple[str, ...] = ("Highest", "High", "Medium", "Low")
PRIORITY_RANK = {"Low": 1, "Medium": 2, "High": 3, "Highest": 4}
STATUS_ORDER: tuple[str, ...] = ("Ready", "Automated", "Draft", "Deprecated")
TEST_TYPE_ORDER: tuple[str, ...] = (
    "Functional",
    "Negative",
    "UI/UX",
    "API",
    "Boundary",
    "Regression",
    "Security",
    "Accessibility",
    "Performance",
)

CSV_COLUMNS: tuple[str, ...] = (
    "Issue Type",
    "Issue Key",
    "Summary",
    "Description",
    "Priority",
    "Component",
    "Labels",
    "Test Type",
    "Preconditions",
    "Steps",
    "Expected Result",
    "Browser",
    "Device",
    "Status",
)
OVERLAY_COLUMNS: tuple[str, ...] = (*CSV_COLUMNS, "Feature")

COMPACT_FIELDS = (
    "key",
    "summary",
    "module",
    "feature",
    "priority",
    "test_type",
    "status",
    "browser",
    "device",
)


@dataclass(slots=True)
class TestCase:
    __test__ = False  # not a pytest test class

    key: str
    summary: str
    description: str
    priority: str
    module: str
    labels: list[str]
    test_type: str
    preconditions: str
    steps: list[str]
    expected_result: str
    browser: str
    device: str
    status: str
    feature: str
    issue_type: str = "Test"
    source: str = "base"  # "base" (source CSV) or "overlay" (added or edited through TC MCP)
    duplicate_of: str | None = None

    @property
    def key_number(self) -> int:
        digits = "".join(ch for ch in self.key.rsplit("-", 1)[-1] if ch.isdigit())
        return int(digits) if digits else 0

    @property
    def priority_rank(self) -> int:
        return PRIORITY_RANK.get(self.priority, 0)

    @property
    def scenario(self) -> str:
        return self.summary.strip().casefold()

    @property
    def is_live(self) -> bool:
        return self.status != "Deprecated"

    def compact(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in COMPACT_FIELDS}

    def full(self) -> dict[str, Any]:
        row = self.compact()
        row.update(
            description=self.description,
            preconditions=self.preconditions,
            steps=list(self.steps),
            expected_result=self.expected_result,
            labels=list(self.labels),
            source=self.source,
            duplicate_of=self.duplicate_of,
        )
        return row

    def view(self, detail: str) -> dict[str, Any]:
        return self.full() if detail == "full" else self.compact()

    def steps_text(self) -> str:
        return " | ".join(f"{i}. {step}" for i, step in enumerate(self.steps, start=1))

    def to_csv_row(self, include_feature: bool = False) -> dict[str, str]:
        row = {
            "Issue Type": self.issue_type,
            "Issue Key": self.key,
            "Summary": self.summary,
            "Description": self.description,
            "Priority": self.priority,
            "Component": self.module,
            "Labels": " ".join(self.labels),
            "Test Type": self.test_type,
            "Preconditions": self.preconditions,
            "Steps": self.steps_text(),
            "Expected Result": self.expected_result,
            "Browser": self.browser,
            "Device": self.device,
            "Status": self.status,
        }
        if include_feature:
            row["Feature"] = self.feature
        return row


StrOrList = str | list[str]


class TestFilter(BaseModel):
    """Shared filter used by search, stats, effort and export tools. Every field is optional."""

    __test__ = False

    module: StrOrList | None = Field(
        None, description="Module name(s), e.g. 'Reports' or ['A/B Testing', 'Heatmaps']. Case-insensitive, aliases like 'ab', 'sdk', 'billing' work."
    )
    feature: StrOrList | None = Field(
        None, description="Feature name(s) inside a module, e.g. 'SSO login'. See list_modules."
    )
    priority: list[Priority] | None = Field(None, description="Exact priorities to include.")
    min_priority: Priority | None = Field(
        None, description="Lowest priority to include. Order: Low < Medium < High < Highest."
    )
    max_priority: Priority | None = Field(None, description="Highest priority to include.")
    test_type: list[TestType] | None = Field(None, description="Test types to include.")
    browser: StrOrList | None = Field(None, description="Browser(s), e.g. 'Chrome 148' or 'safari'.")
    device: StrOrList | None = Field(None, description="Device(s), e.g. 'desktop', 'ios', 'android', 'tablet'.")
    status: list[Status] | None = Field(None, description="Statuses to include. Listing 'Deprecated' here includes deprecated tests.")
    label: str | None = Field(None, description="A single label, e.g. 'security' or 'ab-testing'.")
    include_deprecated: bool = Field(False, description="Include Deprecated tests (hidden by default).")
    include_duplicates: bool = Field(True, description="Include rows flagged as exact duplicates of another test.")


StepList = Annotated[list[Annotated[str, Field(min_length=1)]], Field(min_length=1, max_length=20)]


class TestCaseDraft(BaseModel):
    """A new test case written in the VWO catalog format."""

    __test__ = False

    module: str = Field(..., description="Module name, e.g. 'Reports'.")
    feature: str = Field(..., min_length=2, description="Feature inside the module, e.g. 'scheduled email'.")
    test_type: TestType
    priority: Priority
    summary: str = Field(..., description="Format: '[Module] Test Type: action feature', e.g. '[Reports] Boundary: test limits of scheduled email'.")
    preconditions: str = Field(..., min_length=5, description="Setup needed before step 1. Separate items with '; '.")
    steps: StepList = Field(..., description="Ordered steps without numbering, e.g. ['Log in to VWO and open the Reports module.', ...].")
    expected_result: str = Field(..., min_length=5, description="One specific, checkable outcome.")
    browser: str = Field(..., description="e.g. 'Chrome 148'. See get_filter_options.")
    device: str = Field(..., description="e.g. 'desktop'. See get_filter_options.")
    description: str | None = Field(None, description="Optional. Generated in the catalog style when omitted.")
    status: Status = "Draft"


class TestCaseChanges(BaseModel):
    """Fields that update_test_case may change. Omit a field to keep its current value."""

    __test__ = False

    summary: str | None = None
    description: str | None = None
    priority: Priority | None = None
    status: Status | None = None
    test_type: TestType | None = None
    feature: str | None = None
    preconditions: str | None = None
    steps: StepList | None = None
    expected_result: str | None = None
    browser: str | None = None
    device: str | None = None
