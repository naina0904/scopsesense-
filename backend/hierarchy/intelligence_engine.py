import logging
from typing import Dict, List, Any, Optional
from backend.integrations.core.unified_schema import PlatformData, PlatformType, Feature

logger = logging.getLogger(__name__)

class HierarchicalIntelligenceEngine:
    """
    Phase 1: Propagates assignees down the Jira hierarchy (Epic -> Story -> Subtask).
    Uses BFS traversal via HierarchyNodes.
    """
    
    def apply(self, platform_data: PlatformData, org_profile: Optional[Dict] = None) -> None:
        if platform_data.platform != PlatformType.JIRA:
            return
            
        ownership_anchor = org_profile.get("ownership_anchor", {}).get("value") if org_profile else None
            
        nodes_by_id = {n.id: n for n in platform_data.hierarchy_nodes}
        features_by_id = {f.id: f for f in platform_data.features}
        
        # Find root nodes to start top-down BFS
        roots = [n for n in platform_data.hierarchy_nodes if not n.parent_id]
        
        queue = list(roots)
        while queue:
            current_node = queue.pop(0)
            current_feature = features_by_id.get(current_node.id)
            
            for child_id in current_node.child_ids:
                child_node = nodes_by_id.get(child_id)
                child_feature = features_by_id.get(child_id)
                
                if child_node and child_feature:
                    child_type = child_feature.platform_specific.get("issue_type", "Unknown")
                    
                    # Adaptive HIE Logic
                    can_inherit = True
                    if ownership_anchor:
                        # If the child's issue type is the ownership anchor (e.g. Task), it must be explicitly assigned.
                        # It should NOT inherit from Epic or Story.
                        if child_type == ownership_anchor:
                            can_inherit = False
                    
                    # Propagate Assignee if child is unassigned and allowed to inherit
                    if current_feature and current_feature.assigned_to and not child_feature.assigned_to and can_inherit:
                        child_feature.assigned_to = current_feature.assigned_to
                        
                        from datetime import datetime
                        # Preserve Lineage Truth
                        child_feature.inherited_attributes["assigned_to"] = {
                            "value": current_feature.assigned_to,
                            "source_node_id": current_node.id,
                            "confidence": 0.85 if not ownership_anchor else 0.92,
                            "rule_applied": "Epic/Story Assignee Fallback" if not ownership_anchor else f"Inherited from ancestor (JUIL allowed: {child_type} != {ownership_anchor})",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        logger.debug(f"HIE: Inherited assignee {current_feature.assigned_to} for {child_id} from {current_node.id}")
                        
                if child_node:
                    queue.append(child_node)
