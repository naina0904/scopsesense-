import sys
from backend.integrations.core.unified_schema import Feature, FindingCategory, FindingSeverity
from backend.intelligence.audit_findings_engine import AuditFindingsEngine

def verify():
    print("--- Sprint 4 Verification: AuditFindingsEngine ---")
    
    # 1. Feature with low traceability
    f1 = Feature(id="F1", name="Low Traceability", evidence_score=0.2)
    
    # 2. Feature with variance (ghost authorship)
    f2 = Feature(id="F2", name="Variance", variance_detected=True, variance_reason="Ghost authoring")
    
    # 3. Feature with effort overrun (high severity variance)
    f3 = Feature(id="F3", name="Overrun", variance_detected=True, estimated_hours=10.0, actual_hours=18.0, variance_reason="Took longer")
    
    # 4. Feature with schedule delay
    f4 = Feature(id="F4", name="Delay", delay_days=10.5)
    
    # 5. Perfect feature (no findings)
    f5 = Feature(id="F5", name="Perfect", evidence_score=1.0, delay_days=2.0)
    
    features = [f1, f2, f3, f4, f5]
    
    findings = AuditFindingsEngine.run(features)
    
    f1_finding = next((f for f in findings if f.feature_id == "F1"), None)
    f2_finding = next((f for f in findings if f.feature_id == "F2"), None)
    f3_finding = next((f for f in findings if f.feature_id == "F3"), None)
    f4_finding = next((f for f in findings if f.feature_id == "F4"), None)
    f5_finding = next((f for f in findings if f.feature_id == "F5"), None)
    
    passed = True
    
    if f1_finding and f1_finding.category == FindingCategory.TRACEABILITY and f1_finding.severity == FindingSeverity.HIGH:
        print("F1 (Traceability): PASS")
    else:
        print("F1 (Traceability): FAIL")
        passed = False
        
    if f2_finding and f2_finding.category == FindingCategory.VARIANCE and f2_finding.severity == FindingSeverity.MEDIUM:
        print("F2 (Variance - Medium): PASS")
    else:
        print("F2 (Variance - Medium): FAIL")
        passed = False
        
    if f3_finding and f3_finding.category == FindingCategory.VARIANCE and f3_finding.severity == FindingSeverity.HIGH:
        print("F3 (Variance - High): PASS")
    else:
        print("F3 (Variance - High): FAIL")
        passed = False
        
    if f4_finding and f4_finding.category == FindingCategory.SCHEDULE_DELAY and f4_finding.severity == FindingSeverity.HIGH:
        print("F4 (Delay): PASS")
    else:
        print("F4 (Delay): FAIL")
        passed = False
        
    if not f5_finding:
        print("F5 (Perfect): PASS")
    else:
        print("F5 (Perfect): FAIL")
        passed = False
        
    print(f"\nResult: {'PASS' if passed else 'FAIL'}")
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    verify()
