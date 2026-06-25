import sys
import json
from backend.integrations.core.unified_schema import PlatformData, Feature
from backend.hierarchy.models import HierarchyNode
from backend.hierarchy.cross_platform_mapper import CrossPlatformMapper

def verify():
    # 1. Mock Jira Data
    jira_data = PlatformData(platform="jira", platform_key="PROJ", auth_type="api")
    jira_issue = HierarchyNode(
        id="PROJ-123",
        external_id="123",
        title="Database migration",
        node_type="STORY",
        platform="jira"
    )
    jira_data.hierarchy_nodes.append(jira_issue)
    
    # 2. Mock GitHub Data
    github_data = PlatformData(platform="github", platform_key="org/repo", auth_type="api")
    pr_node = HierarchyNode(
        id="PR#456",
        external_id="456",
        title="[PROJ-123] Migrate database schema",
        node_type="PULL_REQUEST",
        platform="github"
    )
    github_data.hierarchy_nodes.append(pr_node)
    
    commit_node = HierarchyNode(
        id="COMMIT#abc",
        external_id="abc",
        title="PROJ-123: dropped old tables",
        node_type="COMMIT",
        platform="github"
    )
    github_data.hierarchy_nodes.append(commit_node)
    
    unrelated_node = HierarchyNode(
        id="PR#789",
        external_id="789",
        title="Fix typo in readme",
        node_type="PULL_REQUEST",
        platform="github"
    )
    github_data.hierarchy_nodes.append(unrelated_node)
    
    # 3. Correlate
    unified_nodes = CrossPlatformMapper.correlate_platforms(jira_data, github_data)
    nodes_by_id = {n.id: n for n in unified_nodes}
    
    print("--- Sprint 3A Verification ---")
    
    j_node = nodes_by_id.get("PROJ-123")
    pr_n = nodes_by_id.get("PR#456")
    c_n = nodes_by_id.get("COMMIT#abc")
    u_n = nodes_by_id.get("PR#789")
    
    # Assert PR is linked and has high confidence
    pr_linked = "PROJ-123" in pr_n.linked_nodes
    pr_conf = pr_n.confidence_score
    print(f"PR Linked to Jira: {pr_linked} (Expected: True) -> {'PASS' if pr_linked else 'FAIL'}")
    print(f"PR Confidence: {pr_conf} (Expected: 0.95) -> {'PASS' if pr_conf == 0.95 else 'FAIL'}")
    
    # Assert Commit is linked
    c_linked = "PROJ-123" in c_n.linked_nodes
    c_conf = c_n.confidence_score
    print(f"Commit Linked to Jira: {c_linked} (Expected: True) -> {'PASS' if c_linked else 'FAIL'}")
    print(f"Commit Confidence: {c_conf} (Expected: 0.95) -> {'PASS' if c_conf == 0.95 else 'FAIL'}")
    
    # Assert Unrelated is NOT linked
    u_linked = "PROJ-123" in u_n.linked_nodes
    print(f"Unrelated PR Linked: {u_linked} (Expected: False) -> {'PASS' if not u_linked else 'FAIL'}")
    
    # Assert Jira node has reciprocal links
    j_links = set(j_node.linked_nodes)
    expected_j_links = {"PR#456", "COMMIT#abc"}
    j_links_valid = expected_j_links.issubset(j_links)
    print(f"Jira Node Linked to GH: {j_links} -> {'PASS' if j_links_valid else 'FAIL'}")
    
    passed = pr_linked and c_linked and not u_linked and j_links_valid and pr_conf == 0.95
    print(f"\nResult: {'PASS' if passed else 'FAIL'}")
    
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    verify()
