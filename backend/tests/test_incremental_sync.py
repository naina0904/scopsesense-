import pytest
from datetime import datetime, timezone
from backend.services.platform_fetch_service import PlatformFetchService
from backend.integrations.core.unified_schema import PlatformData, PlatformType, Feature, FeatureStatus

def test_upsert_merge_logic():
    service = PlatformFetchService()
    
    # 1. Create existing data (Snapshot 1)
    existing_data = PlatformData(
        platform=PlatformType.JIRA,
        platform_key="TEST_PROJ",
        platform_url="https://test.atlassian.net",
        auth_type="api_token",
        features=[
            Feature(id="TEST-1", name="Feature 1", status=FeatureStatus.TODO),
            Feature(id="TEST-2", name="Feature 2", status=FeatureStatus.IN_PROGRESS),
        ],
        timeline_events=[],
        contributors=[]
    )
    
    # 2. Create delta data (Snapshot 2 - Incremental Fetch)
    # TEST-2 is updated, TEST-3 is new. TEST-1 is unchanged so it's not in the delta.
    delta_data = PlatformData(
        platform=PlatformType.JIRA,
        platform_key="TEST_PROJ",
        platform_url="https://test.atlassian.net",
        auth_type="api_token",
        features=[
            Feature(id="TEST-2", name="Feature 2", status=FeatureStatus.DONE), # Updated
            Feature(id="TEST-3", name="Feature 3", status=FeatureStatus.TODO), # New
        ],
        timeline_events=[],
        contributors=[]
    )
    
    # 3. Apply Merge (Upsert)
    merged_data = service._merge_platform_data(existing_data, delta_data)
    
    # 4. Assertions
    assert len(merged_data.features) == 3, "Merged data should contain 3 features"
    
    feature_map = {f.id: f for f in merged_data.features}
    
    # Unchanged
    assert "TEST-1" in feature_map
    assert feature_map["TEST-1"].status == FeatureStatus.TODO
    
    # Updated
    assert "TEST-2" in feature_map
    assert feature_map["TEST-2"].status == FeatureStatus.DONE
    
    # New
    assert "TEST-3" in feature_map
    assert feature_map["TEST-3"].status == FeatureStatus.TODO
    
    print("Upsert logic test passed.")

if __name__ == "__main__":
    test_upsert_merge_logic()
