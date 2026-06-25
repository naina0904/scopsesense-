"""
Unified schema for multi-platform project data integration.

Defines canonical data models used by all platform adapters (GitHub, Jira)
and all downstream analysis engines (SemanticDelayAnalyzer, ProjectChatbot, etc.).

All symbols here are derived exclusively from imports and field access found
in consuming modules. No fields are invented.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

# Re-export HierarchyNode from the canonical hierarchy module so that
# `from backend.integrations.core.unified_schema import HierarchyNode`
# continues to work for all consumers (hierarchy_builder.py, etc.)
from backend.hierarchy.models import HierarchyNode  # noqa: F401


# ============================================================
# ENUMS
# ============================================================

class PlatformType(Enum):
    """Supported integration platforms."""
    GITHUB = "github"
    JIRA = "jira"


class FeatureStatus(Enum):
    """Canonical feature lifecycle statuses.

    Values are derived from status_map dicts in both adapters and
    from FeatureStatus(status_str) calls in audit_tasks.py.
    """
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"


# ============================================================
# FEATURE
# ============================================================

@dataclass
class Feature:
    """Canonical representation of a single unit of work.

    Fields derived from:
    - github_adapter.py  _convert_pr_to_feature()
    - jira_adapter.py    _convert_issue_to_feature()
    - audit_tasks.py     Feature(...) constructor calls
    - semantic_delay_analyzer.py  field accesses
    - project_chatbot.py          field accesses
    """

    # --- Required ---
    id: str
    name: str

    # --- Optional with defaults ---
    description: str = ""
    status: FeatureStatus = FeatureStatus.TODO
    assigned_to: Optional[str] = None          # contributor.id
    created_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None    # jira_adapter, audit_tasks
    actual_hours: Optional[float] = None       # jira_adapter, audit_tasks
    aggregated_actual_hours: Optional[float] = None  # audit_tasks.py line 101, 312
    parent_id: Optional[str] = None            # jira_adapter (subtask parent), audit_tasks (module)
    priority: Optional[str] = None             # jira_adapter, audit_tasks
    platform_specific: Dict[str, Any] = field(default_factory=dict)
    ownership_history: List[Dict[str, Any]] = field(default_factory=list)
    # Sprint 2C Traceability Intelligence
    evidence_score: Optional[float] = None     # 0.0 to 1.0 based on traceability depth
    active_contributors: List[str] = field(default_factory=list) # Commit authors
    variance_detected: bool = False            # True if assigned != active or estimated < actual
    variance_reason: Optional[str] = None      # Text explanation of variance
    delay_days: Optional[float] = None         # Delta between creation and completion
    inherited_attributes: Dict[str, Dict[str, Any]] = field(default_factory=dict)


# ============================================================
# CONTRIBUTOR
# ============================================================

@dataclass
class Contributor:
    """A person who has contributed to the project.

    Fields derived from:
    - github_adapter.py  Contributor(...) constructor
    - jira_adapter.py    Contributor(...) constructor
    - audit_tasks.py     Contributor(id=dev, name=dev)
    - semantic_delay_analyzer.py  contributor.name, contributor.id, contributor.commits_count
    - project_chatbot.py          contrib.name, contrib.commits_count
    """

    # --- Required ---
    id: str
    name: str

    # --- Optional with defaults ---
    email: Optional[str] = None
    commits_count: int = 0                     # github_adapter increments this
    platform_specific: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# TIMELINE EVENT
# ============================================================

@dataclass
class TimelineEvent:
    """A single timestamped event in the project timeline.

    Fields derived from:
    - github_adapter.py  _convert_commit_to_event()
    - jira_adapter.py    _extract_timeline_from_history()
    - semantic_delay_analyzer.py  e.timestamp, e.event_type, e.contributor_id, e.description
    """

    # --- Required ---
    timestamp: datetime
    event_type: str    # "commit", "status_changed", "ownership_transfer", "issue_updated"
    description: str

    # --- Optional with defaults ---
    contributor_id: Optional[str] = None
    feature_id: Optional[str] = None          # jira_adapter sets this
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# SPRINT
# ============================================================

@dataclass
class Sprint:
    """A time-boxed sprint (JIRA-only concept for now).

    Fields derived from:
    - jira_adapter.py  _convert_sprint()
    - semantic_delay_analyzer.py  sprint.end_date, sprint.name, sprint.features
    """

    # --- Required ---
    id: str
    name: str

    # --- Optional with defaults ---
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    goal: Optional[str] = None
    status: str = "active"
    features: List[str] = field(default_factory=list)  # feature IDs in this sprint


# ============================================================
# AUDIT FINDING (Sprint 4)
# ============================================================

class FindingCategory(str, Enum):
    TRACEABILITY = "TRACEABILITY"
    VARIANCE = "VARIANCE"
    SCHEDULE_DELAY = "SCHEDULE_DELAY"
    CAPACITY = "CAPACITY"

class FindingSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass
class AuditFinding:
    id: str
    feature_id: str
    category: FindingCategory
    severity: FindingSeverity
    message: str
    evidence: Dict[str, Any]
    confidence: float
    recommended_action: str

@dataclass
class AuditReport:
    report_id: str
    generated_at: str
    executive_summary: str
    risk_summary: Dict[str, int]
    findings: List[AuditFinding]
    recommendations: List[str]


# ============================================================
# PLATFORM DATA
# ============================================================

@dataclass
class PlatformData:
    """Top-level container for all normalized data from a single platform.

    Fields derived from:
    - github_adapter.py    PlatformData(...) constructor + .features, .contributors, .timeline_events
    - jira_adapter.py      PlatformData(...) constructor + .contributors, .features, .timeline_events, .sprints
    - audit_tasks.py       PlatformData(...) constructor (line 282-289), .features, .contributors
    - semantic_delay_analyzer.py  .platform_key, .platform.value, .features, .contributors,
                                   .timeline_events, .sprints, .get_features_by_status(),
                                   .get_events_for_feature(), .get_features_by_contributor()
    - project_chatbot.py   .platform.value, .platform_key, .contributors, .features,
                            .timeline_events, .get_features_by_contributor(),
                            .get_events_by_contributor(), .get_contributor_by_id(),
                            .get_events_for_feature()
    - hierarchy_builder.py .features, .hierarchy_nodes
    """

    # --- Required ---
    platform: PlatformType
    platform_key: str          # e.g. "owner/repo" for GitHub, project key for Jira

    # --- Optional with defaults ---
    platform_url: str = ""
    auth_type: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)

    # --- Collections ---
    features: List[Feature] = field(default_factory=list)
    contributors: List[Contributor] = field(default_factory=list)
    timeline_events: List[TimelineEvent] = field(default_factory=list)
    sprints: List[Sprint] = field(default_factory=list)
    hierarchy_nodes: List[HierarchyNode] = field(default_factory=list)

    # ----------------------------------------------------------------
    # Helper methods
    # Referenced in semantic_delay_analyzer.py and project_chatbot.py
    # ----------------------------------------------------------------

    def __post_init__(self):
        def parse_dt(val):
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val.replace("Z", "+00:00"))
                except ValueError:
                    return val
            return val

        if isinstance(self.platform, str):
            try:
                self.platform = PlatformType(self.platform)
            except ValueError:
                pass

        if self.features:
            hydrated = []
            for item in self.features:
                if isinstance(item, dict):
                    for date_field in ["created_date", "due_date", "completed_date"]:
                        if date_field in item and item[date_field]:
                            item[date_field] = parse_dt(item[date_field])
                    if "status" in item:
                        st = item["status"]
                        if isinstance(st, dict):
                            st = st.get("value")
                        if isinstance(st, str):
                            try:
                                item["status"] = FeatureStatus(st)
                            except ValueError:
                                item["status"] = FeatureStatus.TODO
                    hydrated.append(Feature(**item))
                else:
                    hydrated.append(item)
            self.features = hydrated

        if self.contributors:
            hydrated = []
            for item in self.contributors:
                if isinstance(item, dict):
                    hydrated.append(Contributor(**item))
                else:
                    hydrated.append(item)
            self.contributors = hydrated

        if self.timeline_events:
            hydrated = []
            for item in self.timeline_events:
                if isinstance(item, dict):
                    if "timestamp" in item and item["timestamp"]:
                        item["timestamp"] = parse_dt(item["timestamp"])
                    hydrated.append(TimelineEvent(**item))
                else:
                    hydrated.append(item)
            self.timeline_events = hydrated

        if self.sprints:
            hydrated = []
            for item in self.sprints:
                if isinstance(item, dict):
                    if "start_date" in item and item["start_date"]:
                        item["start_date"] = parse_dt(item["start_date"])
                    if "end_date" in item and item["end_date"]:
                        item["end_date"] = parse_dt(item["end_date"])
                    hydrated.append(Sprint(**item))
                else:
                    hydrated.append(item)
            self.sprints = hydrated

        if self.hierarchy_nodes:
            hydrated = []
            for item in self.hierarchy_nodes:
                if isinstance(item, dict):
                    hydrated.append(HierarchyNode(**item))
                else:
                    hydrated.append(item)
            self.hierarchy_nodes = hydrated

    def get_features_by_status(self, status: FeatureStatus) -> List[Feature]:
        """Return all features matching the given status."""
        return [f for f in self.features if f.status == status]

    def get_features_by_contributor(self, contributor_id: str) -> List[Feature]:
        """Return all features assigned to the given contributor."""
        return [f for f in self.features if f.assigned_to == contributor_id]

    def get_events_for_feature(self, feature_id: str) -> List[TimelineEvent]:
        """Return all timeline events for a given feature."""
        return [e for e in self.timeline_events if e.feature_id == feature_id]

    def get_events_by_contributor(self, contributor_id: str) -> List[TimelineEvent]:
        """Return all timeline events produced by a given contributor."""
        return [e for e in self.timeline_events if e.contributor_id == contributor_id]

    def get_contributor_by_id(self, contributor_id: str) -> Optional[Contributor]:
        """Look up a contributor by id. Returns None if not found."""
        for contributor in self.contributors:
            if contributor.id == contributor_id:
                return contributor
        return None
