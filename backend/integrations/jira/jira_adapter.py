"""
JIRA adapter for unified platform integration.
Normalizes JIRA project data to PlatformData schema.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from backend.observability.structured_logger import get_logger

from backend.integrations.core.base_adapter import BaseAdapter
from backend.integrations.core.unified_schema import (
    PlatformData,
    PlatformType,
    Feature,
    FeatureStatus,
    Contributor,
    TimelineEvent,
    Sprint
)
from backend.integrations.jira.jira_client import JiraClient

logger = get_logger(__name__)


class JiraAdapter(BaseAdapter):
    """
    JIRA adapter for converting JIRA data to unified PlatformData schema.
    Handles both Cloud and Server instances.
    """
    
    def __init__(
        self,
        project_key: str,
        domain: str,
        api_token: str,
        email: Optional[str] = None,
        username: Optional[str] = None
    ):
        """
        Initialize JIRA adapter.
        
        Args:
            project_key: JIRA project key (e.g., 'PROJ')
            domain: JIRA domain (e.g., 'company.atlassian.net')
            api_token: API token for authentication
            email: Email for Cloud (required for Cloud)
            username: Username for Server/DC
        """
        auth_creds = {
            "api_token": api_token,
            "domain": domain,
            "email": email,
            "username": username
        }
        super().__init__(auth_creds)
        
        self.project_key = project_key
        self.domain = domain
        self.client = JiraClient(
            domain=domain,
            api_token=api_token,
            email=email,
            username=username
        )
        self.platform_type = PlatformType.JIRA
        self.platform_url = f"https://{domain}/browse/{project_key}"
    
    def authenticate(self) -> bool:
        """Test connection to JIRA."""
        try:
            is_connected = self.client.test_connection()
            self.authenticated = is_connected
            return is_connected
        except Exception as e:
            logger.error(f"JIRA authentication failed: {e}")
            return False
    
    def fetch_raw_data(self, last_synced_at: Optional[datetime] = None) -> Dict[str, Any]:
        """Fetch all necessary data from JIRA."""
        if not self.authenticated:
            return {}
        
        try:
            # Get project info
            project = self.client.get_project(self.project_key)
            if not project:
                logger.error(f"Project {self.project_key} not found")
                return {}
            
            # Get issues (stories, tasks, bugs)
            issues = self.client.get_issues(self.project_key, max_results=100, last_synced_at=last_synced_at)
            
            # Get boards and sprints
            boards = self.client.get_boards(self.project_key)
            sprints = []
            for board in boards:
                board_sprints = self.client.get_sprints(board["id"])
                sprints.extend(board_sprints)
            
            # Get issue histories for timeline
            issue_histories = {}
            for issue in issues:
                history = self.client.get_issue_history(issue["key"])
                issue_histories[issue["key"]] = history
            
            # Find Story Point field ID
            fields = self.client.get_fields()
            story_point_field_id = None
            for field in fields:
                if field.get("name") and "story point" in field.get("name").lower():
                    story_point_field_id = field.get("id")
                    break
            
            return {
                "project": project,
                "issues": issues,
                "boards": boards,
                "sprints": sprints,
                "issue_histories": issue_histories,
                "story_point_field_id": story_point_field_id
            }
        except Exception as e:
            logger.error(f"Error fetching JIRA data: {e}")
            raise RuntimeError(f"Failed to fetch JIRA data: {str(e)}")

    def normalize(self, last_synced_at: Optional[datetime] = None) -> PlatformData:
        """Convert JIRA data to PlatformData schema."""
        raw_data = self.fetch_raw_data(last_synced_at=last_synced_at)
        
        platform_data = PlatformData(
            platform=PlatformType.JIRA,
            platform_key=self.project_key,
            platform_url=self.platform_url,
            auth_type="api_token",
            raw_data=raw_data
        )
        
        if not raw_data:
            return platform_data
        
        # Extract contributors
        contributors_dict = {}
        issues = raw_data.get("issues", [])
        
        for issue in issues:
            # Get assignee
            assignee_id = self.client.extract_assignee(issue)
            if assignee_id and assignee_id not in contributors_dict:
                assignee = issue.get("fields", {}).get("assignee", {})
                contributors_dict[assignee_id] = Contributor(
                    id=assignee_id,
                    name=assignee.get("displayName", assignee.get("name", "Unknown")),
                    email=assignee.get("emailAddress"),
                    platform_specific={"accountId": assignee_id}
                )
            
            # Get reporter
            reporter_id = issue.get("fields", {}).get("reporter", {}).get("accountId")
            if reporter_id and reporter_id not in contributors_dict:
                reporter = issue.get("fields", {}).get("reporter", {})
                contributors_dict[reporter_id] = Contributor(
                    id=reporter_id,
                    name=reporter.get("displayName", reporter.get("name", "Unknown")),
                    email=reporter.get("emailAddress"),
                    platform_specific={"accountId": reporter_id}
                )
        
        platform_data.contributors = list(contributors_dict.values())
        
        # Extract features (issues/stories)
        features_dict = {}
        story_point_field_id = raw_data.get("story_point_field_id")
        for issue in issues:
            feature = self._convert_issue_to_feature(issue, self.client, story_point_field_id)
            features_dict[feature.id] = feature
            platform_data.features.append(feature)
        
        # Extract timeline events
        issue_histories = raw_data.get("issue_histories", {})
        for issue_key, histories in issue_histories.items():
            events = self._extract_timeline_from_history(
                issue_key,
                histories,
                features_dict
            )
            platform_data.timeline_events.extend(events)
        
        # Extract sprints
        sprints = raw_data.get("sprints", [])
        for sprint in sprints:
            sprint_obj = self._convert_sprint(sprint)
            platform_data.sprints.append(sprint_obj)
        
        return platform_data
    
    @staticmethod
    def _convert_issue_to_feature(
        issue: Dict[str, Any],
        client: JiraClient,
        story_point_field_id: Optional[str] = None
    ) -> Feature:
        """Convert a JIRA issue to Feature."""
        fields = issue.get("fields", {})
        issue_key = issue.get("key")
        
        # Determine status
        raw_status = client.extract_status(issue)
        print(f"DEBUG: JIRA RAW STATUS FOR {issue_key}: '{raw_status}'", flush=True)
        print(f"DEBUG: JIRA ISSUE FIELDS: {list(issue.get('fields', {}).keys())}", flush=True)
        if "statuscategory" in issue.get("fields", {}):
            print(f"DEBUG: statuscategory: {issue['fields']['statuscategory']}", flush=True)
            
        status_str = raw_status.lower()
        status_map = {
            "to do": FeatureStatus.TODO,
            "todo": FeatureStatus.TODO,
            "in progress": FeatureStatus.IN_PROGRESS,
            "in-progress": FeatureStatus.IN_PROGRESS,
            "inprogress": FeatureStatus.IN_PROGRESS,
            "in review": FeatureStatus.IN_REVIEW,
            "review": FeatureStatus.IN_REVIEW,
            "done": FeatureStatus.DONE,
            "completed": FeatureStatus.DONE,
            "blocked": FeatureStatus.BLOCKED
        }
        status = FeatureStatus.TODO
        for k, v in status_map.items():
            if k in status_str:
                status = v
                break
        
        # Extract dates
        created_date, due_date = client.extract_dates(issue)
        
        # Extract time tracking
        estimated_hours, actual_hours = client.extract_time_tracking(issue)
        
        # Get assignee
        assignee_id = client.extract_assignee(issue)
        
        # Get parent (for sub-tasks)
        parent_link = fields.get("parent")
        parent_id = parent_link.get("key") if parent_link else None
        
        # Get Story Points
        story_points = fields.get(story_point_field_id) if story_point_field_id else None

        feature = Feature(
            id=issue_key,
            name=fields.get("summary", "Unknown"),
            description=fields.get("description", ""),
            status=status,
            assigned_to=assignee_id,
            created_date=created_date,
            due_date=due_date,
            estimated_hours=estimated_hours,
            actual_hours=actual_hours,
            parent_id=parent_id,
            priority=(fields.get("priority") or {}).get("name", "medium").lower(),
            platform_specific={
                "issue_type": fields.get("issuetype", {}).get("name"),
                "labels": fields.get("labels", []),
                "components": [c.get("name") for c in fields.get("components", [])],
                "resolution": fields.get("resolution", {}).get("name") if fields.get("resolution") else None,
                "story_points": story_points,
                "raw_parent": fields.get("parent"),
                "raw_epic_link_10008": fields.get("customfield_10008"),
                "raw_epic_link_10014": fields.get("customfield_10014"),
                "raw_epic": fields.get("epic"),
                "created": fields.get("created"),
                "updated": fields.get("updated"),
                "resolutiondate": fields.get("resolutiondate"),
                "duedate": fields.get("duedate")
            }
        )
        
        return feature
    
    @staticmethod
    def _extract_timeline_from_history(
        issue_key: str,
        histories: List[Dict[str, Any]],
        features_dict: Dict[str, Feature]
    ) -> List[TimelineEvent]:
        """Extract timeline events from issue changelog."""
        events = []
        
        for history in histories:
            timestamp_str = history.get("created")
            try:
                timestamp = datetime.fromisoformat(
                    timestamp_str.replace("Z", "+00:00")
                )
            except:
                continue
            
            # Get author
            author = history.get("author", {})
            contributor_id = author.get("accountId")
            
            # Get changes
            items = history.get("items", [])
            for item in items:
                field = item.get("field")
                from_value = item.get("fromString")
                to_value = item.get("toString")
                
                description = f"{field}: {from_value} → {to_value}"
                
                event_type = "issue_updated"
                if field == "status":
                    event_type = "status_changed"
                elif field == "assignee":
                    event_type = "ownership_transfer"
                
                event = TimelineEvent(
                    timestamp=timestamp,
                    event_type=event_type,
                    description=description,
                    contributor_id=contributor_id,
                    feature_id=issue_key,
                    metadata={
                        "field": field,
                        "from": from_value,
                        "to": to_value
                    }
                )
                events.append(event)
                
                if field == "assignee" and issue_key in features_dict:
                    features_dict[issue_key].ownership_history.append({
                        "previous_owner": from_value,
                        "new_owner": to_value,
                        "timestamp": timestamp
                    })
        
        if issue_key in features_dict and features_dict[issue_key].ownership_history:
            features_dict[issue_key].ownership_history.sort(key=lambda x: x["timestamp"])
        
        return events
    
    @staticmethod
    def _convert_sprint(sprint: Dict[str, Any]) -> Sprint:
        """Convert JIRA sprint to unified Sprint."""
        start_date_str = sprint.get("startDate")
        end_date_str = sprint.get("endDate")
        
        start_date = None
        end_date = None
        
        try:
            if start_date_str:
                start_date = datetime.fromisoformat(
                    start_date_str.replace("Z", "+00:00")
                )
            if end_date_str:
                end_date = datetime.fromisoformat(
                    end_date_str.replace("Z", "+00:00")
                )
        except:
            pass
        
        sprint_obj = Sprint(
            id=str(sprint.get("id")),
            name=sprint.get("name", "Unknown"),
            start_date=start_date,
            end_date=end_date,
            goal=sprint.get("goal"),
            status=sprint.get("state", "active").lower()
        )
        
        return sprint_obj
