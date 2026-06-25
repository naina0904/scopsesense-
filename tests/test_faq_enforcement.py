import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.analysis.semantic_delay_analyzer import DelayAnalysisResult, DelayEvidence, DelayCategory
from backend.analysis.faq_generator import FAQGenerator

def test_faq_generator_enforces_exactly_5():
    # Setup dummy analysis result
    evidence = [
        DelayEvidence(
            category=DelayCategory.BLOCKED_FEATURES,
            severity=0.8,
            description="Feature is blocked",
            affected_features=["Feature A"],
            affected_contributors=[],
            timeline_markers=[],
            metadata={}
        )
    ]
    
    result = DelayAnalysisResult(
        project_key="TEST-1",
        platform="github",
        analysis_timestamp=datetime.utcnow(),
        total_features=10,
        completed_features=5,
        in_progress_features=3,
        blocked_features=2,
        unassigned_features=1,
        severity_score=0.5,
        primary_causes=["blocked_features"],
        evidence=evidence,
        working_hours_breakdown={}
    )
    
    generator = FAQGenerator(result)
    faqs = generator.generate()
    
    assert len(faqs) == 5, f"Expected exactly 5 FAQs, but got {len(faqs)}"
    print("SUCCESS: FAQGenerator enforces exactly 5 FAQs.")

if __name__ == "__main__":
    test_faq_generator_enforces_exactly_5()
