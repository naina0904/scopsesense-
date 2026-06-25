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
        
        adapter = JiraAdapter("DUMMY", "DUMMY", "DUMMY")
        platform_data = PlatformData(platform=PlatformType.JIRA, platform_key="DUMMY")
        
        for issue in issues:
            feat = adapter._convert_issue_to_feature(issue, adapter.client, None)
            platform_data.features.append(feat)
            
        extractor = JiraHierarchyExtractor(None)
        platform_data = extractor.apply(platform_data)
        HierarchyBuilder().build(platform_data)
        service = PlatformFetchService()
        canonical_actual = service._canonicalize_actual(platform_data)

        # Create dictionaries for fast lookup
        raw_dict = {i["key"]: i for i in issues}
        feat_dict = {f.id: f for f in platform_data.features}
        node_dict = {n.id: n for n in platform_data.hierarchy_nodes}
        canon_dict = {c["requirement"].split()[0] if "SCRUM-" in c["requirement"] else c["requirement"]: c for c in canonical_actual}
        # Wait, the requirement field in canonical_actual is feature.name. 
        # So we can't key canon_dict by f.id reliably. Let's just zip or rebuild canon.
        
        def trace_issue(issue_key):
            print(f"\n────────────────────────────────────────────")
            print(f"TRACE FOR: {issue_key}")
            
            f = feat_dict.get(issue_key)
            if not f:
                print("Issue not found in features.")
                return
            
            node = node_dict.get(issue_key)
            
            # Module Assignment Logic Replicated for tracing
            module_name = "Unmapped Work Item"
            root_feature = None
            if node and node.root_id:
                root_feature = feat_dict.get(node.root_id)
                if root_feature and root_feature.platform_specific.get("issue_type", "").lower() == "epic":
                    module_name = root_feature.name
            
            print(f"Issue Key: {f.id}")
            print(f"Issue Type: {f.platform_specific.get('issue_type')}")
            print(f"Issue Summary: {f.name}")
            
            current_id = f.id
            depth = 1
            print(f"\nTraversal Depth {depth}:")
            
            while True:
                curr_feat = feat_dict.get(current_id)
                if not curr_feat: break
                
                print(f"  [{current_id}] Type: {curr_feat.platform_specific.get('issue_type')}")
                print(f"  Raw Parent Field: {curr_feat.platform_specific.get('raw_parent')}")
                print(f"  Raw Epic Link (10008): {curr_feat.platform_specific.get('raw_epic_link_10008')}")
                print(f"  Raw Epic Link (10014): {curr_feat.platform_specific.get('raw_epic_link_10014')}")
                
                if curr_feat.parent_id:
                    print(f"  -> Extracted Parent: {curr_feat.parent_id}")
                    current_id = curr_feat.parent_id
                    depth += 1
                    print(f"\nTraversal Depth {depth}:")
                else:
                    print(f"  -> Extracted Parent: None (End of traversal)")
                    break

            print(f"\nResolved Root: {node.root_id if node else 'None'}")
            print(f"Resolved Root Type: {root_feature.platform_specific.get('issue_type') if root_feature else 'None'}")
            print(f"Resolved Module: {module_name}")

        trace_issue("SCRUM-4")
        trace_issue("SCRUM-2")
        trace_issue("SCRUM-1")

    finally:
        db.close()

if __name__ == "__main__":
    verify()
