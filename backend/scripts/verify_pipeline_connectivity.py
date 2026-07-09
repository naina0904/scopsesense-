import sys
import os
from datetime import datetime
from backend.integrations.core.unified_schema import PlatformData, PlatformType, Feature
from backend.analysis.semantic_delay_analyzer import DelayAnalysisResult, DelayEvidence, DelayCategory
from backend.analysis.project_chatbot import ProjectChatbot, AnalysisContextualizer

def verify():
    print("--- Verifying End-to-End Pipeline Connectivity & Chatbot Hydration ---")
    
    # 1. Mock session dict as returned by get_session() (where platform_data and analysis_result are dicts)
    mock_platform_data_dict = {
        "platform": "jira",
        "platform_key": "PROJ",
        "features": [
            {
                "id": "PROJ-1",
                "title": "User Authentication API",
                "status": "Done",
                "assigned_developer": "Dev A",
                "planned_hours": 20.0,
                "actual_hours": 25.0
            },
            {
                "id": "PROJ-2",
                "title": "Payment Gateway Integration",
                "status": "Blocked",
                "assigned_developer": "Dev B",
                "planned_hours": 40.0,
                "actual_hours": 10.0
            }
        ],
        "contributors": [
            {"name": "Dev A", "email": "deva@example.com", "total_commits": 50},
            {"name": "Dev B", "email": "devb@example.com", "total_commits": 30}
        ]
    }
    
    mock_analysis_result_dict = {
        "project_key": "PROJ",
        "platform": "jira",
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "total_features": 2,
        "completed_features": 1,
        "in_progress_features": 0,
        "blocked_features": 1,
        "unassigned_features": 0,
        "severity_score": 0.75,
        "primary_causes": ["blocked_features", "variance_overrun"],
        "evidence": [
            {
                "category": "blocked_features",
                "severity": 0.95,
                "description": "1 features are blocked."
            }
        ]
    }
    
    mock_srs_features = [
        {"id": "REQ-1", "title": "User login and signup", "priority": "High"},
        {"id": "REQ-2", "title": "Stripe checkout integration", "priority": "High"}
    ]
    
    # 2. Test AnalysisContextualizer Hydration
    print("\n[Test 1] Testing AnalysisContextualizer hydration from dicts...")
    try:
        contextualizer = AnalysisContextualizer(
            platform_data=mock_platform_data_dict,
            analysis_result=mock_analysis_result_dict,
            srs_features=mock_srs_features
        )
        
        # Verify platform_data is hydrated to PlatformData object
        if isinstance(contextualizer.platform_data, PlatformData):
            print("  -> platform_data hydrated to PlatformData: PASS")
        else:
            print(f"  -> platform_data hydration failed ({type(contextualizer.platform_data)}): FAIL")
            sys.exit(1)
            
        # Verify features inside PlatformData are hydrated to Feature objects
        if len(contextualizer.platform_data.features) == 2 and hasattr(contextualizer.platform_data.features[0], "name") and contextualizer.platform_data.features[0].name == "User Authentication API":
            print("  -> features inside PlatformData hydrated to Feature objects: PASS")
        else:
            print("  -> features inside PlatformData hydration failed: FAIL")
            sys.exit(1)
            
        # Verify analysis_result is hydrated to DelayAnalysisResult object
        if isinstance(contextualizer.analysis_result, DelayAnalysisResult):
            print("  -> analysis_result hydrated to DelayAnalysisResult: PASS")
        else:
            print(f"  -> analysis_result hydration failed ({type(contextualizer.analysis_result)}): FAIL")
            sys.exit(1)
            
        # Verify evidence inside DelayAnalysisResult is hydrated to DelayEvidence objects
        if len(contextualizer.analysis_result.evidence) == 1 and isinstance(contextualizer.analysis_result.evidence[0], DelayEvidence):
            print("  -> evidence inside DelayAnalysisResult hydrated to DelayEvidence objects: PASS")
        else:
            print("  -> evidence inside DelayAnalysisResult hydration failed: FAIL")
            sys.exit(1)
            
    except Exception as e:
        print(f"  -> Exception during AnalysisContextualizer initialization: {e}: FAIL")
        sys.exit(1)
        
    # 3. Test ProjectChatbot Initialization and Context Building
    print("\n[Test 2] Testing ProjectChatbot initialization and context summary generation...")
    try:
        chatbot = ProjectChatbot(
            platform_data=mock_platform_data_dict,
            analysis_result=mock_analysis_result_dict,
            srs_features=mock_srs_features
        )
        summary = chatbot.contextualizer.build_context_summary()
        if "PROJ" in summary and "User Authentication API" in summary and "Stripe checkout integration" in summary:
            print("  -> Context summary contains Jira features, SRS requirements, and metrics: PASS")
        else:
            print("  -> Context summary missing key elements: FAIL")
            print(f"Summary generated:\n{summary}")
            sys.exit(1)
    except Exception as e:
        print(f"  -> Exception during ProjectChatbot initialization/summary: {e}: FAIL")
        sys.exit(1)
        
    print("\nAll Pipeline Connectivity & Hydration Tests PASSED successfully!")

if __name__ == "__main__":
    verify()
