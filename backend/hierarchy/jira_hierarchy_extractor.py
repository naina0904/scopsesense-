import logging
from typing import Optional

from backend.integrations.core.unified_schema import PlatformData

logger = logging.getLogger(__name__)

class JiraHierarchyExtractor:
    """Robust Jira Hierarchy Resolver.
    
    Supports Classic, Team-Managed, Company-Managed, Epic Links, and Parent relationships.
    Assigns the correct ``parent_id`` to each feature.
    """

    def __init__(self, client=None):
        self.client = client

    def extract(self, platform_data: PlatformData) -> None:
        # Detect active hierarchy model based on available fields
        has_10014 = any(f.platform_specific.get("raw_epic_link_10014") for f in platform_data.features)
        has_10008 = any(f.platform_specific.get("raw_epic_link_10008") for f in platform_data.features)
        has_epic = any(f.platform_specific.get("raw_epic") for f in platform_data.features)

        for feature in platform_data.features:
            ps = feature.platform_specific
            
            # Subtask parent resolution
            parent_link = ps.get("raw_parent")
            parent_key = parent_link.get("key") if isinstance(parent_link, dict) else parent_link
            
            epic_key = None
            if has_10014:
                epic_key = ps.get("raw_epic_link_10014")
            elif has_10008:
                epic_key = ps.get("raw_epic_link_10008")
            elif has_epic:
                epic_key = ps.get("raw_epic")
                if isinstance(epic_key, dict):
                    epic_key = epic_key.get("key")

            issue_type = (ps.get("issue_type") or "").lower()

            if issue_type in ["subtask", "sub-task"]:
                # Subtasks strictly link to their parent
                feature.parent_id = parent_key
                ps["hierarchy_level"] = "SUBTASK"
                ps["rollup_parent_id"] = parent_key
            elif issue_type == "epic":
                feature.parent_id = None
                ps["hierarchy_level"] = "EPIC"
                ps["rollup_parent_id"] = None
            elif issue_type == "story":
                feature.parent_id = epic_key or parent_key
                ps["hierarchy_level"] = "STORY"
                ps["rollup_parent_id"] = epic_key or parent_key
            else:
                # Tasks, Bugs, etc.
                feature.parent_id = epic_key or parent_key
                ps["hierarchy_level"] = "TASK"
                ps["rollup_parent_id"] = epic_key or parent_key

    def apply(self, platform_data: PlatformData) -> PlatformData:
        """Run extraction and return the updated ``PlatformData``.

        This wrapper enables a fluent style in the fetch pipeline.
        """
        self.extract(platform_data)
        return platform_data
