import sys
from collections import Counter
from backend.integrations.github.github_adapter import GitHubAdapter

class MockGitHubClient:
    def __init__(self, token):
        self.token = token
        
    def get_repo_details(self, owner, repo):
        return {"name": repo, "full_name": f"{owner}/{repo}"}
        
    def get_commits(self, owner, repo):
        # We don't really care about the generic commits endpoint for hierarchy here
        return []
        
    def get_pull_requests(self, owner, repo):
        return [{
            "id": 456, 
            "number": 456, 
            "title": "Fix the issue", 
            "body": "This PR closes #123 and implements the fix.", 
            "state": "closed", 
            "html_url": "url_pr"
        }]
        
    def get_issues(self, owner, repo):
        return [{
            "id": 123, 
            "number": 123, 
            "title": "Bug 1", 
            "state": "open", 
            "html_url": "url_issue", 
            "milestone": None
        }]
        
    def get_milestones(self, owner, repo):
        return []
        
    def get_pr_commits(self, owner, repo, pr_number):
        if str(pr_number) == "456":
            return [{
                "sha": "abcdef123456",
                "commit": {"message": "Implement fix"},
                "author": {"name": "dev1", "date": "2023-01-01T00:00:00Z"},
                "html_url": "url_commit"
            }]
        return []

def verify():
    # Monkey-patch GitHubClient
    import backend.integrations.github.github_adapter as g_adapter
    g_adapter.GitHubClient = MockGitHubClient
    
    adapter = GitHubAdapter("test-owner", "test-repo", "dummy")
    adapter.authenticated = True
    
    # Run normalization
    pd = adapter.normalize()
    nodes = pd.hierarchy_nodes
    
    # Verify Issue -> PR -> Commit chain
    issue_node = next((n for n in nodes if n.node_type == "ISSUE"), None)
    pr_node = next((n for n in nodes if n.node_type == "PULL_REQUEST"), None)
    commit_node = next((n for n in nodes if n.node_type == "COMMIT"), None)
    
    issue_id_pass = "FAIL"
    pr_id_pass = "FAIL"
    commit_id_pass = "FAIL"
    
    chain_valid = False
    
    if issue_node and pr_node and commit_node:
        issue_id_pass = "PASS" if issue_node.id == "ISSUE#123" else "FAIL"
        pr_id_pass = "PASS" if pr_node.id == "PR#456" else "FAIL"
        commit_id_pass = "PASS" if commit_node.id == "COMMIT#abcdef123456" else "FAIL"
        
        # Check parents
        if pr_node.parent_id == issue_node.id and commit_node.parent_id == pr_node.id:
            chain_valid = True
            
        # Check children
        if pr_node.id in issue_node.child_ids and commit_node.id in pr_node.child_ids:
            # Fully valid
            pass
        else:
            chain_valid = False

    chain_pass = "PASS" if chain_valid else "FAIL"

    # Counts
    issues_fetched = len([n for n in nodes if n.node_type == "ISSUE"])
    prs_fetched = len([n for n in nodes if n.node_type == "PULL_REQUEST"])
    commits_fetched = len([n for n in nodes if n.node_type == "COMMIT"])
    
    linked_issue_to_pr = len([n for n in nodes if n.node_type == "PULL_REQUEST" and n.parent_id and "ISSUE#" in n.parent_id])
    linked_pr_to_commit = len([n for n in nodes if n.node_type == "COMMIT" and n.parent_id and "PR#" in n.parent_id])
    total_chains = 1 if linked_issue_to_pr > 0 and linked_pr_to_commit > 0 else 0
    
    print("--- Traceability Counts ---")
    print(f"Issues fetched: {issues_fetched}")
    print(f"Pull Requests fetched: {prs_fetched}")
    print(f"Commits fetched: {commits_fetched}")
    print(f"Linked Issue -> PR relationships: {linked_issue_to_pr}")
    print(f"Linked PR -> Commit relationships: {linked_pr_to_commit}")
    print(f"Total traceability chains: {total_chains}")
    print("\n--- Hierarchy Evidence ---")
    
    import json
    if issue_node: print("ISSUE:\n" + json.dumps(issue_node.__dict__, indent=2))
    if pr_node: print("PULL REQUEST:\n" + json.dumps(pr_node.__dict__, indent=2))
    if commit_node: print("COMMIT:\n" + json.dumps(commit_node.__dict__, indent=2))

    print("\n--- Sprint 2B Verification ---")
    print(f"Issue Node Extracted: {issue_id_pass}")
    print(f"PR Node Extracted: {pr_id_pass}")
    print(f"Commit Node Extracted: {commit_id_pass}")
    print(f"Parent Links Valid: {chain_pass}")
    
    overall = "PASS" if chain_valid and issue_id_pass == "PASS" and pr_id_pass == "PASS" and commit_id_pass == "PASS" else "FAIL"
    print(f"Result: {overall}")
    
    if overall != "PASS":
        sys.exit(1)

if __name__ == "__main__":
    verify()
