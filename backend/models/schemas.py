from pydantic import BaseModel
from typing import List, Optional


class Feature(BaseModel):
    feature_id: str
    feature_name: str
    expected_hours: float
    assigned_to: Optional[str] = None
    priority: Optional[str] = "Medium"


class GitHubSignal(BaseModel):
    commit_id: str
    author: str
    message: str
    files_changed: List[str]


class AuditRequest(BaseModel):
    owner: str
    repo: str
    branch: str = "main"


class FullAuditRequest(BaseModel):
    owner: str
    repo: str
    srs_file_path: str


class AuditResponse(BaseModel):
    success: bool
    session_id: str
    status: str


class AuditResult(BaseModel):
    feature_name: str
    expected_hours: float
    actual_hours: float
    completion_percentage: float
    risk_level: str


from typing import Dict, Any

class AuditFindingResponse(BaseModel):
    id: str
    feature_id: str
    category: str
    severity: str
    message: str
    evidence: Dict[str, Any]
    confidence: float
    recommended_action: str

class AuditReportResponse(BaseModel):
    report_id: str
    generated_at: str
    executive_summary: str
    risk_summary: Dict[str, int]
    findings: List[AuditFindingResponse]
    recommendations: List[str]