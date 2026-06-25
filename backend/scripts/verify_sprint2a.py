import sys
from collections import Counter
from backend.integrations.github.github_adapter import GitHubAdapter

class MockGitHubClient:
    def __init__(self, token):
        self.token = token
        
    def get_repo_details(self, owner, repo):
        return {"name": repo, "full_name": f"{owner}/{repo}"}
        
    def get_commits(self, owner, repo):
        return [{"sha": "abc", "commit": {"message": "Fix 1", "author": {"date": "2023-01-01T00:00:00Z"}}, "author": {"login": "dev1"}}]
        
    def get_pull_requests(self, owner, repo):
        return [{"number": 100, "title": "Add feature", "state": "closed", "html_url": "url1"}]
        
    def get_issues(self, owner, repo):
        return [
            {"number": 10, "title": "Bug 1", "state": "open", "html_url": "url2", "milestone": {"id": 1, "number": 1, "title": "M1"}},
            {"number": 11, "title": "Task 1", "state": "closed", "html_url": "url3", "milestone": None}
        ]
        
    def get_milestones(self, owner, repo):
        return [{"id": 1, "number": 1, "title": "M1", "state": "open"}]

def verify():
    # Monkey-patch GitHubClient
    import backend.integrations.github.github_adapter as g_adapter
    g_adapter.GitHubClient = MockGitHubClient
    
    adapter = GitHubAdapter("test-owner", "test-repo", "dummy")
    adapter.authenticated = True
    
    # 1. & 2. Fetch data
    raw_data = adapter.fetch_raw_data()
    milestones_fetched = len(raw_data.get("milestones", []))
    issues_fetched = len(raw_data.get("issues", []))
    
    # Run normalization
    pd = adapter.normalize()
    
    # 3. & 4. Features created
    issue_features = [f for f in pd.features if f.platform_specific.get("source") == "issue"]
    pr_features = [f for f in pd.features if f.platform_specific.get("source") == "pull_request"]
    
    # 5. Hierarchy nodes
    nodes = pd.hierarchy_nodes
    
    # 6. Issue Count == Issue Feature Count
    count_match = (issues_fetched == len(issue_features))
    
    # 7. No duplicate hierarchy node ids
    ids = [n.id for n in nodes]
    duplicates = [item for item, count in Counter(ids).items() if count > 1]
    duplicate_pass = "PASS" if not duplicates else "FAIL"
    
    # 8. Parent-child links valid
    links_valid = True
    node_map = {n.id: n for n in nodes}
    for n in nodes:
        if n.parent_id:
            if n.parent_id not in node_map:
                links_valid = False
            else:
                parent = node_map[n.parent_id]
                if n.id not in parent.child_ids:
                    links_valid = False
    
    parent_links_pass = "PASS" if links_valid else "FAIL"
    
    overall = "PASS" if (
        milestones_fetched > 0 and 
        issues_fetched > 0 and 
        len(issue_features) > 0 and 
        len(pr_features) > 0 and 
        len(nodes) > 0 and 
        count_match and 
        duplicate_pass == "PASS" and 
        parent_links_pass == "PASS"
    ) else "FAIL"

    print("--- Sprint 2A Verification ---\n")
    print(f"Milestones fetched: {milestones_fetched}")
    print(f"Issues fetched: {issues_fetched}\n")
    print(f"Issue Features: {len(issue_features)}")
    print(f"PR Features: {len(pr_features)}\n")
    print(f"Hierarchy Nodes: {len(nodes)}\n")
    print(f"Duplicate IDs: {duplicate_pass}")
    print(f"Parent Links: {parent_links_pass}\n")
    print(f"Result: {overall}")
    
    if overall != "PASS":
        sys.exit(1)

if __name__ == "__main__":
    verify()
