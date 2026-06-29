"""
Real JIRA API client for fetching issues, sprints, and timeline data.
Supports both Atlassian Cloud and Server instances.
"""

import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.observability.structured_logger import get_logger

logger = get_logger(__name__)


class JiraClient:
    """
    JIRA API client for fetching project data.
    
    Authentication:
    - Uses API tokens (not passwords) for Atlassian Cloud
    - Basic auth: email:api_token
    - For Server/DC: personal access tokens
    """
    
    def __init__(
        self,
        domain: str,  # company.atlassian.net or jira.company.com
        api_token: str,
        email: Optional[str] = None,  # Required for Cloud
        username: Optional[str] = None  # For Server/DC
    ):
        """
        Initialize JIRA client.
        
        Args:
            domain: JIRA instance domain
            api_token: API token for authentication
            email: Email for Cloud API (basic auth: email:token)
            username: Username for Server/DC
        """
        domain = domain.strip().rstrip("/")
        if not domain.startswith("http"):
            self.domain = f"https://{domain}"
        else:
            self.domain = domain
            
        self.api_token = api_token
        self.email = email or username
        self.base_url = f"{self.domain}/rest/api/3"
        self.session = requests.Session()
        self._setup_auth()
    
    def _setup_auth(self):
        """Setup HTTP Basic Authentication."""
        if self.email and self.api_token:
            self.session.auth = (self.email, self.api_token)
        else:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_token}"
            })
    
    def test_connection(self) -> bool:
        """Test if connection to JIRA works."""
        try:
            response = self.session.get(
                f"{self.base_url}/myself",
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"JIRA connection test failed: {e}")
            return False
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_project(self, project_key: str) -> Optional[Dict[str, Any]]:
        """Fetch project details by key."""
        try:
            response = self.session.get(
                f"{self.base_url}/project/{project_key}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch project {project_key}: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_projects(self) -> List[Dict[str, Any]]:
        """Fetch all projects accessible by the user."""
        try:
            response = self.session.get(
                f"{self.base_url}/project",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _paginate_jira(self, url: str, params: Dict[str, Any], result_key: str, max_results: int = 50) -> List[Dict[str, Any]]:
        results = []
        start_at = 0
        if params is None:
            params = {}
            
        while True:
            params["startAt"] = start_at
            params["maxResults"] = max_results
            response = self.session.get(url, params=params, timeout=30)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                logger.error(f"Jira API HTTPError on {url}: {e} - Response Body: {response.text}")
                raise
            data = response.json()
            
            items = data.get(result_key, [])
            if not items:
                break
                
            results.extend(items)
            
            if len(items) < max_results:
                break

                
            start_at += max_results
            
        return results

    def get_issues(
        self,
        project_key: str,
        jql: Optional[str] = None,
        max_results: int = 50,
        last_synced_at: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch issues from a project.
        """
        try:
            if not jql:
                jql = f"project = {project_key}"
            
            if last_synced_at:
                formatted_date = last_synced_at.strftime("%Y-%m-%d %H:%M")
                jql += f" AND updated >= '{formatted_date}'"
            
            url = f"{self.base_url}/search/jql"
            params = {
                "jql": jql,
                "expand": "changelog,operations",
                "fields": "*all"
            }
            return self._paginate_jira(url, params, result_key="issues", max_results=max_results)
        except Exception as e:
            logger.error(f"Failed to fetch issues for {project_key}: {e}")
            return []
    
    def get_sprints(self, board_id: int) -> List[Dict[str, Any]]:
        """Fetch sprints for a board."""
        try:
            url = f"{self.domain}/rest/agile/1.0/board/{board_id}/sprint"
            return self._paginate_jira(url, {}, result_key="values", max_results=50)
        except Exception as e:
            logger.error(f"Failed to fetch sprints: {e}")
            return []
    
    def get_sprint_issues(
        self,
        sprint_id: int,
        board_id: int
    ) -> List[Dict[str, Any]]:
        """Fetch issues for a specific sprint."""
        try:
            url = f"{self.domain}/rest/agile/1.0/board/{board_id}/sprint/{sprint_id}/issue"
            return self._paginate_jira(url, {}, result_key="issues", max_results=50)
        except Exception as e:
            logger.error(f"Failed to fetch sprint {sprint_id} issues: {e}")
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_issue_history(self, issue_key: str) -> List[Dict[str, Any]]:
        """Fetch changelog for an issue to track transitions."""
        try:
            response = self.session.get(
                f"{self.base_url}/issue/{issue_key}",
                params={"expand": "changelog"},
                timeout=10
            )
            response.raise_for_status()
            changelog = response.json().get("changelog", {})
            return changelog.get("histories", [])
        except Exception as e:
            logger.error(f"Failed to fetch issue history {issue_key}: {e}")
            raise
    
    def get_boards(self, project_key: str) -> List[Dict[str, Any]]:
        """Fetch boards for a project."""
        try:
            url = f"{self.domain}/rest/agile/1.0/board"
            params = {"projectKey": project_key}
            return self._paginate_jira(url, params, result_key="values", max_results=50)
        except Exception as e:
            logger.error(f"Failed to fetch boards for {project_key}: {e}")
            return []
    
    def parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse JIRA date string to datetime."""
        if not date_str:
            return None
        try:
            # JIRA returns ISO format: 2024-01-15T10:30:00.000+0000
            return datetime.fromisoformat(
                date_str.replace("Z", "+00:00")
            )
        except Exception as e:
            logger.warning(f"Failed to parse date {date_str}: {e}")
            return None
    
    def extract_status(self, issue: Dict[str, Any]) -> str:
        """Extract status from JIRA issue."""
        try:
            return issue.get("fields", {}).get("status", {}).get("name", "Unknown")
        except:
            return "Unknown"
    
    def extract_assignee(self, issue: Dict[str, Any]) -> Optional[str]:
        """Extract assignee from JIRA issue."""
        try:
            assignee = issue.get("fields", {}).get("assignee")
            if assignee:
                return assignee.get("accountId") or assignee.get("name")
            return None
        except:
            return None
    
    def extract_dates(self, issue: Dict[str, Any]) -> tuple:
        """Extract created and due dates from issue."""
        fields = issue.get("fields", {})
        created = self.parse_date(fields.get("created"))
        due = self.parse_date(fields.get("duedate"))
        return created, due
    
    def extract_time_tracking(self, issue: Dict[str, Any]) -> tuple:
        """Extract estimated and actual time from issue."""
        fields = issue.get("fields", {})
        time_tracking = fields.get("timetracking", {})
        
        estimated_seconds = time_tracking.get("timeEstimateSeconds") or fields.get("timeoriginalestimate")
        spent_seconds = time_tracking.get("timeSpentSeconds") or fields.get("timespent") or fields.get("aggregatetimespent")
        
        estimated_hours = (estimated_seconds / 3600) if estimated_seconds else None
        actual_hours = (spent_seconds / 3600) if spent_seconds else None
        
        return estimated_hours, actual_hours

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_fields(self) -> List[Dict[str, Any]]:
        """Fetch all JIRA fields to map custom fields like Story Points."""
        try:
            response = self.session.get(
                f"{self.base_url}/field",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch JIRA fields: {e}")
            raise