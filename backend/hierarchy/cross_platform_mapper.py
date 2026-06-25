import re
from typing import List
from backend.integrations.core.unified_schema import PlatformData
from backend.hierarchy.models import HierarchyNode

class CrossPlatformMapper:
    """Correlates Jira hierarchy with GitHub hierarchy."""
    
    @staticmethod
    def correlate_platforms(jira_data: PlatformData, github_data: PlatformData) -> List[HierarchyNode]:
        """
        Takes data from both platforms and establishes cross-platform links.
        Returns a single merged list of HierarchyNodes with linked_nodes populated.
        """
        # Identify Jira Project Key to build regex
        project_key = jira_data.platform_key
        if not project_key:
            # Generic fallback
            jira_regex = re.compile(r'(?i)\b([A-Z]+-\d+)\b')
        else:
            jira_regex = re.compile(rf'(?i)\b({project_key}-\d+)\b')
            
        jira_nodes_by_id = {n.id: n for n in jira_data.hierarchy_nodes}
        
        for g_node in github_data.hierarchy_nodes:
            matches = set()
            
            # 1. Scan Title (PR Title, Commit Message, etc.)
            if g_node.title:
                matches.update(jira_regex.findall(g_node.title))
                
            for match in matches:
                issue_key = match.upper()
                if issue_key in jira_nodes_by_id:
                    jira_node = jira_nodes_by_id[issue_key]
                    
                    # 2. Confidence Scoring
                    confidence = 0.6  # Default Medium
                    
                    upper_title = g_node.title.upper()
                    # High confidence if title starts with key or contains bracketed key
                    if upper_title.startswith(issue_key) or f"[{issue_key}]" in upper_title:
                        confidence = 0.95
                        
                    # 3. Establish bi-directional link
                    if issue_key not in g_node.linked_nodes:
                        g_node.linked_nodes.append(issue_key)
                        g_node.confidence_score = confidence
                        g_node.correlation_reason = f"Extracted Jira Key {issue_key} from title."
                        
                    if g_node.id not in jira_node.linked_nodes:
                        jira_node.linked_nodes.append(g_node.id)
                        
        combined_nodes = list(jira_data.hierarchy_nodes) + list(github_data.hierarchy_nodes)
        return combined_nodes
