import uuid
from typing import List
from backend.integrations.core.unified_schema import (
    Feature, 
    AuditFinding, 
    FindingCategory, 
    FindingSeverity
)

class AuditFindingsEngine:
    """
    Deterministically generates structured findings from the canonical Feature schema.
    Operates independently of whether features were derived from Jira or GitHub.
    """
    
    @staticmethod
    def run(features: List[Feature]) -> List[AuditFinding]:
        findings = []
        
        for feature in features:
            # 1. Traceability Gap
            if feature.evidence_score is not None and feature.evidence_score < 0.5:
                findings.append(AuditFinding(
                    id=str(uuid.uuid4()),
                    feature_id=feature.id,
                    category=FindingCategory.TRACEABILITY,
                    severity=FindingSeverity.HIGH,
                    message=f"Low traceability evidence score ({feature.evidence_score})",
                    evidence={"evidence_score": feature.evidence_score},
                    confidence=1.0,
                    recommended_action="Ensure development work is explicitly linked to this issue via PRs and Commits."
                ))
                
            # 2. Effort Overrun / Variance
            if feature.variance_detected:
                severity = FindingSeverity.MEDIUM
                if feature.actual_hours and feature.estimated_hours and (feature.actual_hours > feature.estimated_hours * 1.5):
                    severity = FindingSeverity.HIGH
                    
                findings.append(AuditFinding(
                    id=str(uuid.uuid4()),
                    feature_id=feature.id,
                    category=FindingCategory.VARIANCE,
                    severity=severity,
                    message=f"Variance detected: {feature.variance_reason or 'Unknown'}",
                    evidence={
                        "actual_hours": feature.actual_hours,
                        "estimated_hours": feature.estimated_hours,
                        "reason": feature.variance_reason
                    },
                    confidence=1.0,
                    recommended_action="Review capacity planning and assignment practices."
                ))
                
            # 3. Schedule Delay
            if feature.delay_days is not None and feature.delay_days > 7.0:
                findings.append(AuditFinding(
                    id=str(uuid.uuid4()),
                    feature_id=feature.id,
                    category=FindingCategory.SCHEDULE_DELAY,
                    severity=FindingSeverity.HIGH,
                    message=f"Delivery delayed by {feature.delay_days:.1f} days.",
                    evidence={"delay_days": feature.delay_days},
                    confidence=1.0,
                    recommended_action="Investigate blockers causing extended cycle time."
                ))
                
        return findings
