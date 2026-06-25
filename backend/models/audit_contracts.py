from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ContributorProfile(BaseModel):

    developer: str = "Unknown"

    commits: int = 0

    assigned_features: List[str] = Field(
        default_factory=list
    )

    workload_hours: float = 0

    ownership_confidence: float = 0

    status: str = "unknown"

    evidence: List[Dict[str, Any]] = Field(
        default_factory=list
    )


class TimelineResult(BaseModel):

    feature: Optional[str] = None

    status: str = "unknown"

    timeline_analysis: Dict[str, Any] = Field(
        default_factory=dict
    )

    reasoning: List[str] = Field(
        default_factory=list
    )

    evidence: List[Dict[str, Any]] = Field(
        default_factory=list
    )


class RiskFinding(BaseModel):

    type: str = "Risk"

    severity: str = "LOW"

    message: str = ""

    probability: Optional[float] = None

    reasoning: List[str] = Field(
        default_factory=list
    )

    evidence: List[Dict[str, Any]] = Field(
        default_factory=list
    )


class AgentFinding(BaseModel):

    agent: str

    category: str = "general"

    severity: str = "INFO"

    message: str

    evidence: List[Dict[str, Any]] = Field(
        default_factory=list
    )


class FeatureResult(BaseModel):

    feature_id: Optional[str] = None

    feature_name: str

    expected_hours: float = 0

    assigned_developers: List[str] = Field(
        default_factory=list
    )

    priority: str = "Medium"

    reasoning: List[str] = Field(
        default_factory=list
    )

    evidence: List[Dict[str, Any]] = Field(
        default_factory=list
    )


class AuditContext(BaseModel):

    audit_run_id: Optional[str] = None

    owner: Optional[str] = None

    repository: Optional[str] = None

    provider: str = "gemini"

    repository_context: Dict[str, Any] = Field(
        default_factory=dict
    )

    srs_path: Optional[str] = None


class AuditResult(BaseModel):

    audit_run_id: Optional[str] = None

    provider: str = "gemini"

    semantic_features: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    timeline_analysis: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    contributors: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    feature_ownership: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    hotspots: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    causality: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    insights: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    optional_intelligence: Dict[str, Any] = Field(
        default_factory=dict
    )

    agent_findings: Dict[str, Any] = Field(
        default_factory=dict
    )

    health_score: float = 0

    semantic_confidence: float = 0

    ai_summary: str = ""
