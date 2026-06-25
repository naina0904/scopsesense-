"""
GitHub adapter for unified platform integration.
Normalizes GitHub repository data to PlatformData schema.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.observability.structured_logger import get_logger

from backend.integrations.core.base_adapter import BaseAdapter
from backend.integrations.core.unified_schema import (
    PlatformData,
    PlatformType,
    Feature,
    FeatureStatus,
    Contributor,
    TimelineEvent
)
from backend.github.client import GitHubClient

logger = get_logger(__name__)


class GitHubAdapter(BaseAdapter):
    """
    GitHub adapter for converting repository data to unified PlatformData schema.
    Fetches PRs, issues, commits, and contributors.
    """
    
    def __init__(
        self,
        owner: str,
        repo: str,
        pat_token: str
    ):
        """
        Initialize GitHub adapter.
        
        Args:
            owner: Repository owner (username or org)
            repo: Repository name
            pat_token: Personal Access Token for authentication
        """
        auth_creds = {"pat": pat_token}
        super().__init__(auth_creds)
        
        self.owner = owner
        self.repo = repo
        self.client = GitHubClient(pat_token)
        self.platform_type = PlatformType.GITHUB
        self.platform_url = f"https://github.com/{owner}/{repo}"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def authenticate(self) -> bool:
        """Test connection to GitHub."""
        try:
            # Try to get repo info to verify auth
            repo_data = self.client.get_repo_details(self.owner, self.repo)
            self.authenticated = bool(repo_data)
            return self.authenticated
        except Exception as e:
            logger.error("GitHub authentication failed", error=str(e))
            return False
    
    def fetch_raw_data(self, last_synced_at: Optional[datetime] = None) -> Dict[str, Any]:
        """Fetch all necessary data from GitHub."""
        if not self.authenticated:
            return {}
        
        since_str = None
        if last_synced_at:
            since_str = last_synced_at.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        try:
            repo_data = self.client.get_repo_details(self.owner, self.repo)
            commits = self.client.get_commits(self.owner, self.repo, since=since_str)
            prs_all = self.client.get_pull_requests(self.owner, self.repo) if hasattr(self.client, 'get_pull_requests') else []
            
            # Filter PRs locally
            prs = []
            if last_synced_at:
                for pr in prs_all:
                    updated_at_str = pr.get("updated_at")
                    if updated_at_str:
                        updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                        if updated_at >= last_synced_at.replace(tzinfo=None):
                            prs.append(pr)
            else:
                prs = prs_all

            issues = self.client.get_issues(self.owner, self.repo, since=since_str) if hasattr(self.client, 'get_issues') else []
            milestones = self.client.get_milestones(self.owner, self.repo) if hasattr(self.client, 'get_milestones') else []
            
            pr_commits = {}
            pr_reviews = {}
            for pr in prs:
                pr_number = pr.get("number")
                if pr_number and hasattr(self.client, 'get_pr_commits'):
                    pr_commits[str(pr_number)] = self.client.get_pr_commits(self.owner, self.repo, pr_number)
                if pr_number and hasattr(self.client, 'get_pr_reviews'):
                    pr_reviews[str(pr_number)] = self.client.get_pr_reviews(self.owner, self.repo, pr_number)
            
            issue_comments = {}
            for issue in issues:
                issue_number = issue.get("number")
                if issue_number and hasattr(self.client, 'get_issue_comments'):
                    issue_comments[str(issue_number)] = self.client.get_issue_comments(self.owner, self.repo, issue_number)
            
            for pr in prs:
                pr_number = pr.get("number")
                if pr_number and hasattr(self.client, 'get_issue_comments'):
                    issue_comments[f"PR#{pr_number}"] = self.client.get_issue_comments(self.owner, self.repo, pr_number)

            return {
                "repository": repo_data,
                "commits": commits,
                "pull_requests": prs,
                "issues": issues,
                "milestones": milestones,
                "pr_commits": pr_commits,
                "pr_reviews": pr_reviews,
                "issue_comments": issue_comments
            }
        except Exception as e:
            logger.error("Error fetching GitHub data", error=str(e))
            return {}
    
    def normalize(self, last_synced_at: Optional[datetime] = None) -> PlatformData:
        """Convert GitHub data to PlatformData schema."""
        raw_data = self.fetch_raw_data(last_synced_at=last_synced_at)
        
        platform_data = PlatformData(
            platform=PlatformType.GITHUB,
            platform_key=f"{self.owner}/{self.repo}",
            platform_url=self.platform_url,
            auth_type="pat",
            raw_data=raw_data
        )
        
        if not raw_data:
            return platform_data
        
        # Extract contributors from commits
        contributors_dict = {}
        commits = raw_data.get("commits", [])
        
        for commit in commits:
            author = commit.get("author", {})
            author_login = author.get("login")
            
            if author_login and author_login not in contributors_dict:
                contributors_dict[author_login] = Contributor(
                    id=author_login,
                    name=author.get("name", author_login),
                    email=author.get("email"),
                    commits_count=0,
                    platform_specific={
                        "github_url": author.get("html_url"),
                        "avatar_url": author.get("avatar_url")
                    }
                )
            
            if author_login in contributors_dict:
                contributors_dict[author_login].commits_count += 1
        
        platform_data.contributors = list(contributors_dict.values())
        
        # Extract features from PRs (GitHub PRs as features)
        prs = raw_data.get("pull_requests", [])
        pr_reviews = raw_data.get("pr_reviews", {})
        issue_comments = raw_data.get("issue_comments", {})
        
        for pr in prs:
            pr_number = str(pr.get("number"))
            reviews = pr_reviews.get(pr_number, [])
            comments = issue_comments.get(f"PR#{pr_number}", [])
            feature = self._convert_pr_to_feature(pr, commits, reviews, comments)
            platform_data.features.append(feature)
        
        # Extract features from Issues
        issues = raw_data.get("issues", [])
        for issue in issues:
            issue_number = str(issue.get("number"))
            comments = issue_comments.get(issue_number, [])
            feature = self._convert_issue_to_feature(issue, comments)
            platform_data.features.append(feature)
            
        # Create hierarchy nodes for Milestones and Issues
        self._create_hierarchy_nodes(raw_data, platform_data)
        
        # Extract timeline events from commits
        for commit in commits:
            event = self._convert_commit_to_event(commit)
            if event:
                platform_data.timeline_events.append(event)
                
        # Enrich features with traceabililty intelligence
        self._enrich_features_with_traceability(platform_data)
        
        return platform_data
    
    @staticmethod
    def _convert_pr_to_feature(pr: Dict[str, Any], commits: List[Dict[str, Any]], reviews: List[Dict[str, Any]], comments: List[Dict[str, Any]]) -> Feature:
        """Convert a GitHub PR to Feature."""
        # Determine status from state
        state = pr.get("state", "open")
        status_map = {
            "open": FeatureStatus.IN_PROGRESS,
            "closed": FeatureStatus.DONE,
            "draft": FeatureStatus.TODO
        }
        status = status_map.get(state, FeatureStatus.TODO)
        
        # Parse dates
        created_at_str = pr.get("created_at")
        closed_at_str = pr.get("closed_at")
        updated_at_str = pr.get("updated_at")
        
        created_at = datetime.fromisoformat(created_at_str) if created_at_str else None
        closed_at = datetime.fromisoformat(closed_at_str) if closed_at_str else None
        updated_at = datetime.fromisoformat(updated_at_str) if updated_at_str else None
        
        # Get assignee
        assignee = pr.get("assignee")
        assignee_id = assignee.get("login") if assignee else None
        
        # Count related commits (rough estimate)
        related_commits = [c for c in commits if pr.get("number") in c.get("pr_numbers", [])]
        
        feature = Feature(
            id=f"PR#{pr.get('number')}",
            name=pr.get("title", "Unknown"),
            description=pr.get("body", ""),
            status=status,
            assigned_to=assignee_id,
            created_date=created_at,
            due_date=updated_at,
            completed_date=closed_at,
            platform_specific={
                "pr_number": pr.get("number"),
                "url": pr.get("html_url"),
                "commits": len(related_commits),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
                "changed_files": pr.get("changed_files", 0),
                "source": "pull_request",
                "reviews": reviews,
                "comments": comments
            }
        )
        
        return feature
    
    @staticmethod
    def _convert_commit_to_event(commit: Dict[str, Any]) -> Optional[TimelineEvent]:
        """Convert a GitHub commit to TimelineEvent."""
        try:
            timestamp_str = commit.get("commit", {}).get("author", {}).get("date")
            if not timestamp_str:
                return None
            
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            
            author = commit.get("author", {})
            contributor_id = author.get("login")
            
            message = commit.get("commit", {}).get("message", "")
            
            event = TimelineEvent(
                timestamp=timestamp,
                event_type="commit",
                description=message.split("\n")[0],  # First line of commit message
                contributor_id=contributor_id,
                metadata={
                    "sha": commit.get("sha"),
                    "url": commit.get("html_url"),
                    "additions": commit.get("stats", {}).get("additions", 0),
                    "deletions": commit.get("stats", {}).get("deletions", 0)
                }
            )
            
            return event
        except Exception as e:
            logger.warning("Failed to convert commit to event", error=str(e))
            return None

    @staticmethod
    def _convert_issue_to_feature(issue: Dict[str, Any], comments: List[Dict[str, Any]]) -> Feature:
        """Convert a GitHub issue to Feature."""
        # Determine status from state
        state = issue.get("state", "open")
        status_map = {
            "open": FeatureStatus.TODO,
            "closed": FeatureStatus.DONE
        }
        status = status_map.get(state, FeatureStatus.TODO)
        
        # Parse dates
        created_at_str = issue.get("created_at")
        closed_at_str = issue.get("closed_at")
        updated_at_str = issue.get("updated_at")
        
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")) if created_at_str else None
        closed_at = datetime.fromisoformat(closed_at_str.replace("Z", "+00:00")) if closed_at_str else None
        updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00")) if updated_at_str else None
        
        # Get assignee
        assignees = issue.get("assignees", [])
        if len(assignees) == 1:
            assignee_id = assignees[0]
        elif len(assignees) > 1:
            assignee_id = "Multiple"
        else:
            assignee_id = "Unassigned"
        
        # Get labels
        labels = [l.get("name") for l in issue.get("labels", []) if isinstance(l, dict)]
        
        feature = Feature(
            id=f"ISSUE#{issue.get('number')}",
            name=issue.get("title", "Unknown"),
            description=issue.get("body", "") or "",
            status=status,
            assigned_to=assignee_id,
            created_date=created_at,
            due_date=updated_at,
            completed_date=closed_at,
            platform_specific={
                "issue_number": issue.get("number"),
                "url": issue.get("html_url") or issue.get("url"),
                "labels": labels,
                "source": "issue",
                "milestone_id": issue.get("milestone", {}).get("id") if issue.get("milestone") else None,
                "assignees": assignees,
                "comments": comments
            }
        )
        return feature

    @staticmethod
    def _create_hierarchy_nodes(raw_data: Dict[str, Any], platform_data: PlatformData) -> None:
        """Create hierarchy nodes for Milestones and Issues."""
        # Note: HierarchyNode must be imported at the top of the file if not already
        from backend.hierarchy.models import HierarchyNode
        
        milestones = raw_data.get("milestones", [])
        issues = raw_data.get("issues", [])
        
        # Map milestone ID to internal ID
        milestone_id_map = {}
        for ms in milestones:
            ms_id = f"MILESTONE#{ms.get('id')}"
            milestone_id_map[ms.get("id")] = ms_id
            
            node = HierarchyNode(
                id=ms_id,
                external_id=str(ms.get("id")),
                title=ms.get("title", "Unknown"),
                node_type="MILESTONE",
                parent_id=None,
                root_id=ms_id,
                hierarchy_level=1,
                platform="github",
                child_ids=[],
                metadata={"state": ms.get("state")}
            )
            platform_data.hierarchy_nodes.append(node)
            
        # Map issues to milestones
        for issue in issues:
            issue_id = f"ISSUE#{issue.get('number')}"
            
            ms_info = issue.get("milestone")
            parent_id = milestone_id_map.get(ms_info.get("id")) if ms_info else None
            root_id = parent_id if parent_id else issue_id
            level = 2 if parent_id else 1
            
            node = HierarchyNode(
                id=issue_id,
                external_id=str(issue.get("number")),
                title=issue.get("title", "Unknown"),
                node_type="ISSUE",
                parent_id=parent_id,
                root_id=root_id,
                hierarchy_level=level,
                platform="github",
                child_ids=[],
                metadata={"state": issue.get("state")}
            )
            
            if parent_id:
                for n in platform_data.hierarchy_nodes:
                    if n.id == parent_id:
                        n.child_ids.append(issue_id)
                        break
                        
            platform_data.hierarchy_nodes.append(node)

        import re
        prs = raw_data.get("pull_requests", [])
        pr_commits = raw_data.get("pr_commits", {})
        
        # Add PR nodes and their commits
        for pr in prs:
            pr_id = f"PR#{pr.get('number')}"
            body = pr.get("body") or ""
            
            # Regex to find closes #xxx etc.
            match = re.search(r'(?i)(?:close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)\s+#(\d+)', body)
            linked_issue_number = match.group(1) if match else None
            
            parent_id = f"ISSUE#{linked_issue_number}" if linked_issue_number else None
            # Need to check if the issue node actually exists in our hierarchy
            parent_node = next((n for n in platform_data.hierarchy_nodes if n.id == parent_id), None)
            
            if parent_node:
                root_id = parent_node.root_id
                level = parent_node.hierarchy_level + 1
            else:
                parent_id = None
                root_id = pr_id
                level = 1
                
            node = HierarchyNode(
                id=pr_id,
                external_id=str(pr.get("number")),
                title=pr.get("title", "Unknown"),
                node_type="PULL_REQUEST",
                parent_id=parent_id,
                root_id=root_id,
                hierarchy_level=level,
                platform="github",
                child_ids=[],
                metadata={"linked_issue": linked_issue_number} if linked_issue_number else {}
            )
            
            if parent_node:
                parent_node.child_ids.append(pr_id)
                
            platform_data.hierarchy_nodes.append(node)
            
            # Now add Commit nodes
            commits_for_pr = pr_commits.get(str(pr.get("number")), [])
            for commit in commits_for_pr:
                sha = commit.get("sha")
                if not sha: 
                    continue
                commit_id = f"COMMIT#{sha}"
                
                commit_node = HierarchyNode(
                    id=commit_id,
                    external_id=sha,
                    title=commit.get("message", "Unknown").split("\n")[0],
                    node_type="COMMIT",
                    parent_id=pr_id,
                    root_id=root_id,
                    hierarchy_level=level + 1,
                    platform="github",
                    child_ids=[],
                    metadata={"author": commit.get("author")}
                )
                node.child_ids.append(commit_id)
                platform_data.hierarchy_nodes.append(commit_node)

    @staticmethod
    def _enrich_features_with_traceability(platform_data: PlatformData) -> None:
        """Enrich Feature schemas with traceability intelligence (Sprint 2C)."""
        nodes_by_id = {n.id: n for n in platform_data.hierarchy_nodes}
        
        for feature in platform_data.features:
            issue_id = feature.id
            if not issue_id.startswith("ISSUE#"):
                continue
                
            issue_node = nodes_by_id.get(issue_id)
            if not issue_node:
                continue
            
            # 1. Discover PRs and Commits
            linked_prs = [nodes_by_id[c_id] for c_id in issue_node.child_ids if c_id in nodes_by_id and nodes_by_id[c_id].node_type == "PULL_REQUEST"]
            linked_commits = []
            for pr in linked_prs:
                linked_commits.extend([nodes_by_id[c_id] for c_id in pr.child_ids if c_id in nodes_by_id and nodes_by_id[c_id].node_type == "COMMIT"])
                
            # 2. Evidence Score
            score = 0.3
            if linked_prs:
                score += 0.4
            if linked_commits:
                score += 0.3
            feature.evidence_score = round(score, 1)
            
            # 3. Actual Hours (Heuristic logic removed - effort must come from explicit evidence)
            feature.actual_hours = None
            if not feature.platform_specific:
                feature.platform_specific = {}
            feature.platform_specific["effort_status"] = "Unknown"
            
            # 4. Active Contributors
            authors = set()
            for commit_node in linked_commits:
                author_data = commit_node.metadata.get("author")
                if isinstance(author_data, dict):
                    author = author_data.get("login") or author_data.get("name")
                    if author:
                        authors.add(author)
                elif isinstance(author_data, str):
                    authors.add(author_data)
            feature.active_contributors = list(authors)
            
            # 5. Variance Detection
            assigned_login = feature.assigned_to
            variance = False
            reasons = []
            if assigned_login and authors and assigned_login not in authors:
                variance = True
                reasons.append(f"Ghost Authorship: Assigned to {assigned_login} but developed by {', '.join(authors)}")
            if feature.estimated_hours and feature.actual_hours > feature.estimated_hours:
                variance = True
                reasons.append(f"Effort Overrun: Actual ({feature.actual_hours}h) > Estimated ({feature.estimated_hours}h)")
                
            feature.variance_detected = variance
            if reasons:
                feature.variance_reason = " | ".join(reasons)
                
            # 6. Delay Detection
            if feature.created_date and feature.completed_date:
                delta_days = (feature.completed_date - feature.created_date).total_seconds() / 86400.0
                feature.delay_days = round(delta_days, 1)
