from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class HierarchyNode:
    """Canonical internal representation of hierarchical entities from Jira or GitHub."""
    id: str  # Unique internal identifier (e.g., platform:external_id)
    external_id: str  # Original platform identifier (e.g., issue key, PR number)
    title: str
    node_type: str  # EPIC, STORY, TASK, SUBTASK, PROJECT, MILESTONE, ISSUE, PULL_REQUEST, SUB_ISSUE
    parent_id: Optional[str] = None  # Internal parent node id
    root_id: Optional[str] = None  # Top‑level ancestor id
    hierarchy_level: int = 0
    platform: str = ""  # "jira" or "github"
    assigned_developer: Optional[str] = None  # contributor.id
    planned_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    remaining_hours: Optional[float] = None
    status: Optional[str] = None
    child_ids: List[str] = field(default_factory=list)
    linked_nodes: List[str] = field(default_factory=list)  # Added for cross-platform linking
    metadata: Dict[str, any] = field(default_factory=dict)
    confidence_score: Optional[float] = None
    correlation_reason: Optional[str] = None
