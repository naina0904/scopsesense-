import unittest
from backend.hierarchy.intelligence_engine import HierarchicalIntelligenceEngine
from backend.integrations.core.unified_schema import PlatformData, PlatformType, Feature, HierarchyNode

class TestHierarchicalIntelligenceEngine(unittest.TestCase):
    def setUp(self):
        self.engine = HierarchicalIntelligenceEngine()

    def test_hie_jira_assignee_propagation(self):
        epic = Feature(id="EPIC-1", name="Epic 1", assigned_to="alice")
        subtask = Feature(id="SUB-1", name="Subtask 1", assigned_to=None)
        
        epic_node = HierarchyNode(id="EPIC-1", external_id="EPIC-1", title="Epic 1", node_type="epic", parent_id=None, child_ids=["SUB-1"])
        subtask_node = HierarchyNode(id="SUB-1", external_id="SUB-1", title="Subtask 1", node_type="subtask", parent_id="EPIC-1", child_ids=[])
        
        data = PlatformData(
            platform=PlatformType.JIRA,
            platform_key="TEST",
            features=[epic, subtask],
            hierarchy_nodes=[epic_node, subtask_node]
        )
        
        self.engine.apply(data)
        
        self.assertEqual(subtask.assigned_to, "alice")
        self.assertIn("assigned_to", subtask.inherited_attributes)
        self.assertEqual(subtask.inherited_attributes["assigned_to"]["value"], "alice")
        self.assertEqual(subtask.inherited_attributes["assigned_to"]["source_node_id"], "EPIC-1")
        self.assertEqual(subtask.inherited_attributes["assigned_to"]["rule_applied"], "Epic/Story Assignee Fallback")
        self.assertIn("timestamp", subtask.inherited_attributes["assigned_to"])

    def test_hie_explicit_override_protection(self):
        epic = Feature(id="EPIC-2", name="Epic 2", assigned_to="alice")
        subtask = Feature(id="SUB-2", name="Subtask 2", assigned_to="bob")
        
        epic_node = HierarchyNode(id="EPIC-2", external_id="EPIC-2", title="Epic 2", node_type="epic", parent_id=None, child_ids=["SUB-2"])
        subtask_node = HierarchyNode(id="SUB-2", external_id="SUB-2", title="Subtask 2", node_type="subtask", parent_id="EPIC-2", child_ids=[])
        
        data = PlatformData(
            platform=PlatformType.JIRA,
            platform_key="TEST",
            features=[epic, subtask],
            hierarchy_nodes=[epic_node, subtask_node]
        )
        
        self.engine.apply(data)
        
        self.assertEqual(subtask.assigned_to, "bob")
        self.assertNotIn("assigned_to", subtask.inherited_attributes)

if __name__ == '__main__':
    unittest.main()
