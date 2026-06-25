# Platform Fetch Service

"""Service to fetch data from selected platform (GitHub or Jira) and persist raw results."""

from backend.integrations.core.unified_schema import PlatformType, PlatformData
from backend.storage.repositories_extended import PlatformFetchRepository, IntegrationSyncStateRepository
from backend.integrations.github.github_adapter import GitHubAdapter
from backend.integrations.jira.jira_adapter import JiraAdapter
from backend.hierarchy.intelligence_engine import HierarchicalIntelligenceEngine
from backend.jira_usage.jira_usage_intelligence import JiraUsageIntelligenceEngine
from fastapi.encoders import jsonable_encoder
import datetime
import os

# Feature flag for Sprint 3 (JUIL)
ENABLE_JUIL = True

class PlatformFetchService:
    """Fetches platform data using appropriate adapter and stores raw result."""

    def __init__(self):
        self.repo = PlatformFetchRepository()
        self.sync_repo = IntegrationSyncStateRepository()

    def _merge_platform_data(self, existing_data: PlatformData, delta_data: PlatformData) -> PlatformData:
        """Merge delta features into existing features (Upsert)."""
        if not existing_data:
            return delta_data
            
        feature_map = {f.id: f for f in existing_data.features}
        
        # Upsert delta features
        for df in delta_data.features:
            feature_map[df.id] = df
            
        existing_data.features = list(feature_map.values())
        
        # Merge timeline events safely
        existing_event_ids = {f"{e.feature_id}-{e.timestamp.isoformat()}" for e in existing_data.timeline_events if e.timestamp}
        for e in delta_data.timeline_events:
            if e.timestamp:
                event_id = f"{e.feature_id}-{e.timestamp.isoformat()}"
                if event_id not in existing_event_ids:
                    existing_data.timeline_events.append(e)

        # Merge contributors
        contrib_map = {c.id: c for c in existing_data.contributors}
        for dc in delta_data.contributors:
            contrib_map[dc.id] = dc
        existing_data.contributors = list(contrib_map.values())
        
        # Merge hierarchy nodes
        node_map = {n.id: n for n in existing_data.hierarchy_nodes}
        for dn in delta_data.hierarchy_nodes:
            node_map[dn.id] = dn
        existing_data.hierarchy_nodes = list(node_map.values())

        # Merge sprints
        sprint_map = {s.id: s for s in existing_data.sprints}
        for ds in delta_data.sprints:
            sprint_map[ds.id] = ds
        existing_data.sprints = list(sprint_map.values())
                    
        return existing_data

    def _canonicalize_actual(self, platform_data):
        hierarchy_dict = {node.id: node for node in getattr(platform_data, "hierarchy_nodes", [])}
        
        canonical_actual = []
        for idx, f in enumerate(platform_data.features):
            issue_type = f.platform_specific.get("issue_type", "Task")
            
            module_name = "Unmapped Work Item"
            
            if issue_type.lower() == "epic":
                module_name = f.name
            else:
                # Determine Epic name from hierarchy
                node = hierarchy_dict.get(f.id)
                if node:
                    if node.root_id:
                        root_feature = next((feat for feat in platform_data.features if feat.id == node.root_id), None)
                        if root_feature and root_feature.platform_specific.get("issue_type", "").lower() == "epic":
                            module_name = root_feature.name
                
                if module_name == "Unmapped Work Item" and f.platform_specific.get("component"):
                    module_name = f.platform_specific.get("component")
                elif module_name == "Unmapped Work Item" and f.parent_id:
                    module_name = f.parent_id # Fallback if hierarchy is broken

            assigned_name = "Unassigned"
            if f.assigned_to:
                contributor = platform_data.get_contributor_by_id(f.assigned_to)
                if contributor:
                    assigned_name = contributor.name
                else:
                    assigned_name = f.assigned_to

            raw_status = f.status.value if hasattr(f.status, "value") else str(f.status)
            formatted_status = "Todo"
            if raw_status == "in_progress": formatted_status = "In Progress"
            elif raw_status == "in_review": formatted_status = "In Review"
            elif raw_status == "done": formatted_status = "Done"
            elif raw_status == "blocked": formatted_status = "Blocked"
            
            raw_priority = f.priority or "medium"
            formatted_priority = raw_priority.capitalize()
            
            canonical_actual.append({
                "module": module_name,
                "requirement": f.name or f"Requirement {idx + 1}",
                "issue_type": f.platform_specific.get("issue_type", "Task"),
                "status": formatted_status,
                "assigned_developer": assigned_name,
                "priority": formatted_priority,
                "created_date": f.created_date.isoformat() if f.created_date else None,
                "completed_date": f.completed_date.isoformat() if hasattr(f, "completed_date") and f.completed_date else None,
                "actual_hours": float(f.actual_hours or f.aggregated_actual_hours or 0.0),
                "hours_remaining": float(f.estimated_hours or 0.0) - float(f.actual_hours or f.aggregated_actual_hours or 0.0),
                "hierarchy_level": f.platform_specific.get("hierarchy_level"),
                "rollup_parent_id": f.platform_specific.get("rollup_parent_id"),
                "story_points": f.platform_specific.get("story_points"),
                "resolutiondate": f.platform_specific.get("resolutiondate"),
                "duedate": f.platform_specific.get("duedate"),
                "issue_key": f.id
            })
        return canonical_actual

    def fetch_github(self, owner: str, repo: str, pat_token: str):
        identifier = f"{owner}/{repo}"
        sync_state = self.sync_repo.get("github", identifier)
        last_synced_at = sync_state.last_synced_at if sync_state else None
        
        adapter = GitHubAdapter(owner=owner, repo=repo, pat_token=pat_token)
        if not adapter.authenticate():
            raise Exception("GitHub authentication failed")
            
        # Fetch delta
        raw_data = adapter.fetch_raw_data(last_synced_at=last_synced_at)
        platform_data = adapter.normalize(last_synced_at=last_synced_at)
        
        # Upsert Strategy
        latest_fetch = self.repo.get_latest("github")
        if last_synced_at and latest_fetch and latest_fetch.platform_data_json:
            # We assume latest fetch is for the same repo in this MVP architecture
            existing_data = PlatformData(**latest_fetch.platform_data_json)
            platform_data = self._merge_platform_data(existing_data, platform_data)
            
        canonical_actual = self._canonicalize_actual(platform_data)
        platform_data_json = jsonable_encoder(platform_data)
        
        fetch_entry = self.repo.save(
            platform="github", 
            raw_data=raw_data, # For delta sync, this is just the delta raw data
            actual_data_json=canonical_actual,
            platform_data_json=platform_data_json
        )
        
        # Update sync state
        self.sync_repo.upsert("github", identifier, datetime.datetime.now(datetime.timezone.utc))
        
        return fetch_entry, adapter

    def fetch_jira(self, project_key: str, domain: str, api_token: str, email: str, username: str = None, force_full_sync: bool = False):
        """Fetch JIRA data, build hierarchy, roll up worklogs, and persist result."""
        identifier = project_key
        latest_fetch = self.repo.get_latest("jira")
        existing_data = None
        if latest_fetch and latest_fetch.platform_data_json:
            existing_data = PlatformData(**latest_fetch.platform_data_json)

        sync_state = self.sync_repo.get("jira", identifier)
        last_synced_at = sync_state.last_synced_at if sync_state else None
        
        # POISONED SYNC STATE RECOVERY
        # If we have a sync_state but our baseline has 0 features, force a full fetch.
        if last_synced_at and existing_data and len(existing_data.features) == 0:
            last_synced_at = None

        if force_full_sync:
            last_synced_at = None
            existing_data = None

        adapter = JiraAdapter(project_key=project_key, domain=domain, api_token=api_token, email=email, username=username)
        if not adapter.authenticate():
            raise Exception("Jira authentication failed")
            
        # Normalize raw data into PlatformData (Delta Fetch)
        platform_data = adapter.normalize(last_synced_at=last_synced_at)
        
        # Upsert Strategy
        if last_synced_at and existing_data:
            platform_data = self._merge_platform_data(existing_data, platform_data)
            
        # Preserve Epic/Story hierarchy
        from backend.hierarchy.jira_hierarchy_extractor import JiraHierarchyExtractor
        extractor = JiraHierarchyExtractor(adapter.client)
        platform_data = extractor.apply(platform_data)
        # Build full hierarchy nodes
        from backend.hierarchy.hierarchy_builder import HierarchyBuilder
        HierarchyBuilder().build(platform_data)
        
        # --- SPRINT 3: JUIL Discovery (Phase 1-5) ---
        org_profile = None
        if ENABLE_JUIL and platform_data.platform == PlatformType.JIRA:
            juil_engine = JiraUsageIntelligenceEngine()
            org_profile = juil_engine.discover(platform_data)

        # HIE Phase 1: Contextual Inheritance
        if os.environ.get("HIE_ENABLED", "False").lower() == "true":
            # --- Hierarchical Intelligence Engine (HIE) ---
            hie = HierarchicalIntelligenceEngine()
            hie.apply(platform_data, org_profile=org_profile)
            
        # Roll up worklog hours
        from backend.hierarchy.jira_worklog_rollup_service import JiraWorklogRollupService
        JiraWorklogRollupService(adapter.client).apply(platform_data)
        
        # Persist raw data (delta) and canonical actuals, plus the new enriched payload
        raw_data = adapter.fetch_raw_data(last_synced_at=last_synced_at)
        canonical_actual = self._canonicalize_actual(platform_data)
        platform_data_json = jsonable_encoder(platform_data)
        
        fetch_entry = self.repo.save(
            platform="jira", 
            raw_data=raw_data, 
            actual_data_json=canonical_actual,
            platform_data_json=platform_data_json,
            organization_profile_json=org_profile
        )
        
        # Update sync state
        self.sync_repo.upsert("jira", identifier, datetime.datetime.now(datetime.timezone.utc))
        
        return fetch_entry, platform_data
