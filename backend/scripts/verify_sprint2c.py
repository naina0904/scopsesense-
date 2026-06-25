import sys
import json
from collections import Counter
from datetime import datetime, timedelta

from backend.integrations.github.github_adapter import GitHubAdapter

class MockGitHubClient:
    def __init__(self, token):
        self.token = token
        
    def get_repo_details(self, owner, repo):
        return {"name": repo, "full_name": f"{owner}/{repo}"}
        
    def get_commits(self, owner, repo):
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
        # We simulate a created_at 15 days ago and closed_at 1 day ago
        # We assign it to "pm_lead" but the PR commits will be from "dev1"
        created_at = (datetime.utcnow() - timedelta(days=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
        closed_at = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return [{
            "id": 123, 
            "number": 123, 
            "title": "Bug 1", 
            "state": "closed", 
            "html_url": "url_issue", 
            "milestone": None,
            "created_at": created_at,
            "closed_at": closed_at,
            "user": "pm_lead"
        }]
        
    def get_milestones(self, owner, repo):
        return []
        
    def get_pr_commits(self, owner, repo, pr_number):
        if str(pr_number) == "456":
            return [
                {
                    "sha": "abcdef123456",
                    "commit": {"message": "Implement fix part 1"},
                    "author": {"name": "dev1"},
                    "html_url": "url_commit1"
                },
                {
                    "sha": "abcdef654321",
                    "commit": {"message": "Implement fix part 2"},
                    "author": {"name": "dev1"},
                    "html_url": "url_commit2"
                }
            ]
        return []

def verify():
    # Monkey-patch GitHubClient
    import backend.integrations.github.github_adapter as g_adapter
    g_adapter.GitHubClient = MockGitHubClient
    
    adapter = GitHubAdapter("test-owner", "test-repo", "dummy")
    adapter.authenticated = True
    
    pd = adapter.normalize()
    
    issue_feature = next((f for f in pd.features if f.id == "ISSUE#123"), None)
    
    if not issue_feature:
        print("FAIL: ISSUE#123 feature not found")
        sys.exit(1)
        
    # Set an estimated hours mock to trigger variance
    issue_feature.estimated_hours = 2.0
    # Re-run enrichment manually to simulate estimated_hours variance (since estimate is often set externally or via LLM)
    adapter._enrich_features_with_traceability(pd)
    
    print("--- Sprint 2C Verification ---")
    
    # 1. Actual Hours (2 commits * 2.5 = 5.0)
    actual_hours = issue_feature.actual_hours
    print(f"Actual Hours: {actual_hours} (Expected: 5.0) -> {'PASS' if actual_hours == 5.0 else 'FAIL'}")
    
    # 2. Evidence Score (Issue 0.3 + PR 0.4 + Commits 0.3 = 1.0)
    score = issue_feature.evidence_score
    print(f"Evidence Score: {score} (Expected: 1.0) -> {'PASS' if score == 1.0 else 'FAIL'}")
    
    # 3. Contributor Activity
    active_contributors = issue_feature.active_contributors
    print(f"Active Contributors: {active_contributors} (Expected: ['dev1']) -> {'PASS' if 'dev1' in active_contributors else 'FAIL'}")
    
    # 4. Variance Detection
    variance = issue_feature.variance_detected
    reason = issue_feature.variance_reason
    print(f"Variance Detected: {variance} -> {'PASS' if variance else 'FAIL'}")
    print(f"Variance Reason: {reason}")
    
    # 5. Delay Detection (approx 14 days)
    delay_days = issue_feature.delay_days
    print(f"Delay Days: {delay_days} (Expected: ~14.0) -> {'PASS' if delay_days and 13.5 <= delay_days <= 14.5 else 'FAIL'}")
    
    print("\n--- Feature JSON Dump ---")
    
    # Exclude datetime objects for clean json print
    feat_dict = {k: v for k, v in issue_feature.__dict__.items() if not isinstance(v, datetime) and not k.startswith('_')}
    feat_dict["status"] = issue_feature.status.value
    print(json.dumps(feat_dict, indent=2))
    
    passed = (
        actual_hours == 5.0 and 
        score == 1.0 and 
        "dev1" in active_contributors and 
        variance is True and 
        delay_days and 13.5 <= delay_days <= 14.5
    )
    
    print(f"\nResult: {'PASS' if passed else 'FAIL'}")
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    verify()
