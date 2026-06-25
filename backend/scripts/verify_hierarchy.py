import sys
import json
sys.path.insert(0, '/app')

from backend.storage.database import SessionLocal
from backend.storage.models_extended import PlatformFetchResult
from backend.integrations.core.unified_schema import PlatformData, PlatformType
from backend.integrations.jira.jira_adapter import JiraAdapter
from backend.hierarchy.jira_hierarchy_extractor import JiraHierarchyExtractor
from backend.hierarchy.hierarchy_builder import HierarchyBuilder
from backend.services.platform_fetch_service import PlatformFetchService

def verify():
    db = SessionLocal()
    try:
        fetch = db.query(PlatformFetchResult).filter_by(id=19).first()
        raw_data = fetch.raw_data
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)
        
        issues = raw_data.get('issues', [])
        
        # 1. Normalize
        adapter = JiraAdapter("DUMMY", "DUMMY", "DUMMY")
        platform_data = PlatformData(platform=PlatformType.JIRA, platform_key="DUMMY")
        
        for issue in issues:
            feat = adapter._convert_issue_to_feature(issue, adapter.client, None)
            platform_data.features.append(feat)
            
        # 2. Extract Hierarchy
        extractor = JiraHierarchyExtractor(None)
        platform_data = extractor.apply(platform_data)
        
        # 3. Build Tree
        HierarchyBuilder().build(platform_data)
        
        # 4. Canonicalize
        service = PlatformFetchService()
        canonical_actual = service._canonicalize_actual(platform_data)
        
        # Output results
        target_keys = ["SCRUM-35", "SCRUM-32", "SCRUM-31", "SCRUM-26", "SCRUM-24", "SCRUM-4", "SCRUM-1"]
        print("=== VERIFICATION RESULTS ===")
        for item in canonical_actual:
            req = item["requirement"]
            key = req.split()[0] if "SCRUM-" not in req else "Unknown" # Not easy to get key from just req string if it changed.
            # actually req is feature.name, not the key.
            pass
            
        # Let's map by looping over features directly so we can see the keys
        hierarchy_dict = {node.id: node for node in platform_data.hierarchy_nodes}
        for f in platform_data.features:
            if f.id in target_keys:
                node = hierarchy_dict.get(f.id)
                module_name = "Unmapped Work Item"
                if node and node.root_id:
                    root_feat = next((feat for feat in platform_data.features if feat.id == node.root_id), None)
                    if root_feat and root_feat.platform_specific.get("issue_type", "").lower() == "epic":
                        module_name = root_feat.name
                
                print(f"Issue: {f.id} | Type: {f.platform_specific.get('issue_type')} | Parent ID: {f.parent_id} | Resolved Root: {node.root_id if node else 'None'} | Module: {module_name}")

    finally:
        db.close()

if __name__ == "__main__":
    verify()
