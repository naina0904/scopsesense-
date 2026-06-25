import logging
from typing import Dict, Any, Optional
from backend.integrations.core.unified_schema import PlatformData, Feature
from backend.observability.structured_logger import get_logger

logger = get_logger(__name__)

class JiraUsageIntelligenceEngine:
    """
    Analyzes organizational Jira usage patterns (ownership, estimates, story points)
    to dynamically determine how an organization tracks work, without hardcoded assumptions.
    """

    def discover(self, platform_data: PlatformData) -> Dict[str, Any]:
        """
        Discovers organizational anchors from the platform data.
        Returns a dictionary representing the organization_profile_json.
        """
        org_profile = {
            "ownership_anchor": {"value": None, "confidence": 0.0},
            "story_point_anchor": {"value": None, "confidence": 0.0},
            "estimate_anchor": {"value": None, "confidence": 0.0}
        }
        
        if not platform_data.features:
            return org_profile

        ownership_counts = {}
        total_assigned = 0
        
        sp_counts = {}
        total_sp = 0
        
        est_counts = {}
        total_est = 0
        
        for feature in platform_data.features:
            # Use lower casing for consistent grouping
            issue_type = feature.platform_specific.get("issue_type")
            # If issue_type is empty or None, treat as "Unknown"
            if not issue_type:
                issue_type = "Unknown"
            
            # 1. Ownership Discovery
            if feature.assigned_to:
                ownership_counts[issue_type] = ownership_counts.get(issue_type, 0) + 1
                total_assigned += 1
                
            # 2. Story Point Discovery
            if feature.platform_specific.get("story_points") is not None:
                sp_counts[issue_type] = sp_counts.get(issue_type, 0) + 1
                total_sp += 1
                
            # 3. Estimate Discovery
            if feature.estimated_hours and feature.estimated_hours > 0:
                est_counts[issue_type] = est_counts.get(issue_type, 0) + 1
                total_est += 1

        # Calculate Anchors statistically
        if total_assigned > 0:
            best_type = max(ownership_counts, key=ownership_counts.get)
            confidence = round(ownership_counts[best_type] / total_assigned, 4)
            org_profile["ownership_anchor"] = {"value": best_type, "confidence": confidence}

        if total_sp > 0:
            best_type = max(sp_counts, key=sp_counts.get)
            confidence = round(sp_counts[best_type] / total_sp, 4)
            org_profile["story_point_anchor"] = {"value": best_type, "confidence": confidence}

        if total_est > 0:
            best_type = max(est_counts, key=est_counts.get)
            confidence = round(est_counts[best_type] / total_est, 4)
            org_profile["estimate_anchor"] = {"value": best_type, "confidence": confidence}

        logger.info("discovered_organizational_profile", org_profile=org_profile)
        return org_profile
