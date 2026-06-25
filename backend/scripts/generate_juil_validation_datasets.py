import json
from backend.integrations.core.unified_schema import PlatformData, Feature, PlatformType
from backend.jira_usage.jira_usage_intelligence import JiraUsageIntelligenceEngine

def create_mock_feature(fid, issue_type, assigned=False, sp=None, est=None):
    return Feature(
        id=fid,
        name=f"Feature {fid}",
        status="todo",
        assigned_to="dev1" if assigned else None,
        platform_specific={"issue_type": issue_type, "story_points": sp},
        estimated_hours=est
    )

def generate_epic_driven_org():
    features = [
        create_mock_feature("E1", "Epic", assigned=True, sp=13, est=100),
        create_mock_feature("E2", "Epic", assigned=True, sp=8, est=60),
        create_mock_feature("S1", "Story", assigned=False, sp=None, est=0),
        create_mock_feature("S2", "Story", assigned=False, sp=None, est=0),
        create_mock_feature("S3", "Story", assigned=False, sp=None, est=0)
    ]
    return PlatformData(platform=PlatformType.JIRA, platform_key="EPIC", features=features, timeline_events=[], contributors=[])

def generate_task_driven_org():
    features = [
        create_mock_feature("E1", "Epic", assigned=False, sp=None, est=None),
        create_mock_feature("S1", "Story", assigned=False, sp=None, est=None),
        create_mock_feature("T1", "Task", assigned=True, sp=3, est=20),
        create_mock_feature("T2", "Task", assigned=True, sp=5, est=40),
        create_mock_feature("T3", "Task", assigned=True, sp=2, est=10),
        create_mock_feature("T4", "Task", assigned=True, sp=1, est=8),
    ]
    return PlatformData(platform=PlatformType.JIRA, platform_key="TASK", features=features, timeline_events=[], contributors=[])

def generate_mixed_org():
    features = [
        create_mock_feature("E1", "Epic", assigned=False, sp=None, est=None),
        create_mock_feature("S1", "Story", assigned=True, sp=8, est=40),
        create_mock_feature("S2", "Story", assigned=True, sp=5, est=30),
        create_mock_feature("T1", "Task", assigned=True, sp=None, est=10), # Tasks have time but no points
        create_mock_feature("T2", "Task", assigned=True, sp=None, est=10),
        create_mock_feature("T3", "Task", assigned=True, sp=None, est=10),
    ]
    return PlatformData(platform=PlatformType.JIRA, platform_key="MIXED", features=features, timeline_events=[], contributors=[])

if __name__ == "__main__":
    engine = JiraUsageIntelligenceEngine()
    
    datasets = {
        "Epic_Driven": generate_epic_driven_org(),
        "Task_Driven": generate_task_driven_org(),
        "Mixed_Driven": generate_mixed_org()
    }
    
    results = {}
    for name, pd in datasets.items():
        profile = engine.discover(pd)
        results[name] = profile
        
    with open("juil_validation_datasets.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("Generated juil_validation_datasets.json successfully!")
