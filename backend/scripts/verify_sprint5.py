import sys
from backend.integrations.core.unified_schema import AuditFinding, FindingCategory, FindingSeverity
from backend.intelligence.audit_report_engine import AuditReportEngine

def verify():
    print("--- Sprint 5 Verification: AuditReportEngine ---")
    
    # 1. Mock findings
    f1 = AuditFinding(
        id="f1", feature_id="feat1", category=FindingCategory.TRACEABILITY,
        severity=FindingSeverity.HIGH, message="Trace gap", evidence={}, confidence=1.0,
        recommended_action="Fix traces"
    )
    f2 = AuditFinding(
        id="f2", feature_id="feat2", category=FindingCategory.SCHEDULE_DELAY,
        severity=FindingSeverity.HIGH, message="Delayed", evidence={}, confidence=1.0,
        recommended_action="Unblock dev"
    )
    f3 = AuditFinding(
        id="f3", feature_id="feat3", category=FindingCategory.VARIANCE,
        severity=FindingSeverity.MEDIUM, message="Effort overrun", evidence={}, confidence=1.0,
        recommended_action="Fix estimate"
    )
    
    findings = [f1, f2, f3]
    
    report = AuditReportEngine.generate(findings)
    
    passed = True
    
    # Assert counts
    if report.risk_summary[FindingSeverity.HIGH.value] == 2:
        print("HIGH risk count == 2: PASS")
    else:
        print(f"HIGH risk count == {report.risk_summary[FindingSeverity.HIGH.value]}: FAIL")
        passed = False
        
    if report.risk_summary[FindingSeverity.MEDIUM.value] == 1:
        print("MEDIUM risk count == 1: PASS")
    else:
        print(f"MEDIUM risk count == {report.risk_summary[FindingSeverity.MEDIUM.value]}: FAIL")
        passed = False
        
    if report.risk_summary[FindingSeverity.CRITICAL.value] == 0:
        print("CRITICAL risk count == 0: PASS")
    else:
        print("CRITICAL risk count == 0: FAIL")
        passed = False
        
    # Assert narrative
    if "2 high-severity risk(s) were identified" in report.executive_summary:
        print("Executive summary generated: PASS")
    else:
        print("Executive summary generated: FAIL")
        passed = False
        
    # Assert recommendations
    if len(report.recommendations) == 3:
        print("Recommendations captured: PASS")
    else:
        print("Recommendations captured: FAIL")
        passed = False
        
    print(f"\nResult: {'PASS' if passed else 'FAIL'}")
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    verify()
