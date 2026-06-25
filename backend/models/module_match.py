from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ModuleMatch(BaseModel):
    """Persistence model for a semantic match between an SRS node and a platform feature.

    Attributes
    ----------
    id: str
        Unique identifier for the match record.
    srs_node_id: str
        Identifier of the SRSNode that was matched.
    feature_id: str
        Identifier of the matched Feature.
    matched_type: str
        Type of the matched platform entity (e.g., "epic", "story", "task", "subtask").
    confidence_score: float
        Confidence returned by the SemanticMatcher (0.0 – 1.0).

        Optional additional information (raw documents, vectors, etc.).
    """

    id: str
    srs_node_id: str
    feature_id: str
    matched_type: str
    confidence_score: float
    approval_status: str = "PENDING_REVIEW"
    approval_timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
