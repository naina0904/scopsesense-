import uuid
from datetime import datetime
from typing import List
from backend.integrations.core.unified_schema import AuditFinding, AuditReport, FindingSeverity

class AuditReportEngine:
    """
    Converts a raw list of deterministic AuditFindings into a manager-readable Audit Report.
    """
    
    @staticmethod
    def generate(findings: List[AuditFinding]) -> AuditReport:
        # 1. Initialize Risk Summary
        risk_summary = {
            FindingSeverity.CRITICAL.value: 0,
            FindingSeverity.HIGH.value: 0,
            FindingSeverity.MEDIUM.value: 0,
            FindingSeverity.LOW.value: 0,
        }
        
        # 2. Extract unique recommendations
        recommendations_set = set()
        
        for finding in findings:
            risk_summary[finding.severity.value] += 1
            if finding.recommended_action:
                recommendations_set.add(finding.recommended_action)
                
        # 3. Construct Executive Summary Narrative
        total_findings = len(findings)
        high_critical = risk_summary[FindingSeverity.CRITICAL.value] + risk_summary[FindingSeverity.HIGH.value]
        
        if total_findings == 0:
            executive_summary = "Audit completed successfully. No significant schedule, variance, or traceability risks were detected. The project is tracking cleanly according to the semantic requirements."
        elif high_critical > 0:
            executive_summary = f"Audit completed with concerns. {high_critical} high-severity risk(s) were identified across {total_findings} total findings. Immediate management intervention is recommended to address schedule delays or traceability gaps."
        else:
            executive_summary = f"Audit completed with minor observations. {total_findings} medium/low severity variance(s) were identified. Proceed with standard operational adjustments."
            
        return AuditReport(
            report_id=str(uuid.uuid4()),
            generated_at=datetime.utcnow().isoformat() + "Z",
            executive_summary=executive_summary,
            risk_summary=risk_summary,
            findings=findings,
            recommendations=list(recommendations_set)
        )
