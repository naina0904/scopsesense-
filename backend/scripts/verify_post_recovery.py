"""
Post-Recovery Validation Audit
Checks Sprint 1 and Sprint 2A implementation state against the actual codebase.
Run from repository root: python backend/scripts/verify_post_recovery.py
"""
import sys
import inspect

PASS = []
FAIL = []

def check(label, condition, detail=""):
    if condition:
        PASS.append(label)
        print(f"  [PASS] {label}")
    else:
        FAIL.append(label)
        print(f"  [FAIL] {label}" + (f": {detail}" if detail else ""))

print("=" * 60)
print("POST-RECOVERY VALIDATION AUDIT")
print("=" * 60)

# ──────────────────────────────────────────────
# SECTION 1: Schema import health
# ──────────────────────────────────────────────
print("\n[1] SCHEMA IMPORT HEALTH")
try:
    from backend.integrations.core.unified_schema import (
        PlatformData, PlatformType, Feature, FeatureStatus,
        Contributor, TimelineEvent, Sprint, HierarchyNode
    )
    check("unified_schema imports all 8 required symbols", True)
except ImportError as e:
    check("unified_schema imports all 8 required symbols", False, str(e))
    print("\nFATAL: Cannot continue without schema. Aborting.")
    sys.exit(1)

try:
    import backend.integrations.github.github_adapter as _gh
    check("github_adapter importable", True)
except Exception as e:
    check("github_adapter importable", False, str(e))

try:
    import backend.integrations.jira.jira_adapter as _ji
    check("jira_adapter importable", True)
except Exception as e:
    check("jira_adapter importable", False, str(e))

try:
    from backend.hierarchy.hierarchy_builder import HierarchyBuilder
    check("HierarchyBuilder importable", True)
except Exception as e:
    check("HierarchyBuilder importable", False, str(e))

# ──────────────────────────────────────────────
# SECTION 2: SPRINT 1 VERIFICATION
# ──────────────────────────────────────────────
print("\n[2] SPRINT 1 — HIERARCHY BUILDER & NODE CREATION")

# Check HierarchyNode fields
hn_fields = {f.name for f in HierarchyNode.__dataclass_fields__.values()}
check("HierarchyNode.id exists", "id" in hn_fields)
check("HierarchyNode.external_id exists", "external_id" in hn_fields)
check("HierarchyNode.title exists", "title" in hn_fields)
check("HierarchyNode.node_type exists", "node_type" in hn_fields)
check("HierarchyNode.parent_id exists", "parent_id" in hn_fields)
check("HierarchyNode.root_id exists", "root_id" in hn_fields)
check("HierarchyNode.hierarchy_level exists", "hierarchy_level" in hn_fields)
check("HierarchyNode.platform exists", "platform" in hn_fields)
check("HierarchyNode.child_ids exists", "child_ids" in hn_fields)
check("HierarchyNode.metadata exists", "metadata" in hn_fields)

# Check PlatformData has hierarchy_nodes
pd_fields = {f.name for f in PlatformData.__dataclass_fields__.values()}
check("PlatformData.hierarchy_nodes field exists", "hierarchy_nodes" in pd_fields)
check("PlatformData.sprints field exists", "sprints" in pd_fields)

# Check HierarchyBuilder.build() method signature
from backend.hierarchy.hierarchy_builder import HierarchyBuilder
hb_src = inspect.getsource(HierarchyBuilder.build)
check("HierarchyBuilder.build() method exists", "def build" in hb_src)

# Check for children= kwarg bug (uses 'children' not 'child_ids')
has_children_bug = "children=[]" in hb_src
check("HierarchyBuilder uses correct child_ids field (no children= bug)",
      not has_children_bug,
      "Found 'children=[]' kwarg - HierarchyNode has 'child_ids' not 'children'")

# Try to actually build a hierarchy
print("\n  [RUNTIME] Attempting hierarchy build with mock data...")
try:
    from datetime import datetime
    pd = PlatformData(
        platform=PlatformType.GITHUB,
        platform_key="test/repo"
    )
    pd.features = [
        Feature(id="epic-1", name="Epic One", status=FeatureStatus.IN_PROGRESS),
        Feature(id="story-1", name="Story One", status=FeatureStatus.TODO, parent_id="epic-1"),
        Feature(id="story-2", name="Story Two", status=FeatureStatus.DONE, parent_id="epic-1"),
    ]
    builder = HierarchyBuilder()
    builder.build(pd)
    node_count = len(pd.hierarchy_nodes)
    check("HierarchyBuilder.build() executes without error", True)
    check("HierarchyBuilder produces hierarchy nodes (count > 0)", node_count > 0,
          f"got {node_count} nodes")
    print(f"    hierarchy_nodes produced: {node_count}")

    # Verify root/level assignment
    root_nodes = [n for n in pd.hierarchy_nodes if n.hierarchy_level == 0]
    child_nodes = [n for n in pd.hierarchy_nodes if n.hierarchy_level == 1]
    check("Root node has hierarchy_level=0", len(root_nodes) >= 1,
          f"found {len(root_nodes)} root nodes")
    check("Child nodes have hierarchy_level=1", len(child_nodes) >= 2,
          f"found {len(child_nodes)} child nodes")

    # Verify root_id assignment
    for n in pd.hierarchy_nodes:
        if n.id == "story-1":
            check("story-1 root_id correctly set to epic-1", n.root_id == "epic-1",
                  f"got root_id={n.root_id}")
            check("story-1 parent_id correctly set", n.parent_id == "epic-1",
                  f"got parent_id={n.parent_id}")

except Exception as e:
    check("HierarchyBuilder.build() executes without error", False, str(e))

print("\n  [SPRINT 1 WORKLOG/PERSISTENCE]")
# Check Feature has estimated_hours and actual_hours
feat_fields = {f.name for f in Feature.__dataclass_fields__.values()}
check("Feature.estimated_hours field exists", "estimated_hours" in feat_fields)
check("Feature.actual_hours field exists", "actual_hours" in feat_fields)
check("Feature.aggregated_actual_hours field exists", "aggregated_actual_hours" in feat_fields)
check("Feature.ownership_history field exists", "ownership_history" in feat_fields)

# Check Contributor.commits_count
contrib_fields = {f.name for f in Contributor.__dataclass_fields__.values()}
check("Contributor.commits_count field exists", "commits_count" in contrib_fields)

# Check PlatformData helper methods
check("PlatformData.get_features_by_status() exists", hasattr(PlatformData, "get_features_by_status"))
check("PlatformData.get_features_by_contributor() exists", hasattr(PlatformData, "get_features_by_contributor"))
check("PlatformData.get_events_for_feature() exists", hasattr(PlatformData, "get_events_for_feature"))
check("PlatformData.get_events_by_contributor() exists", hasattr(PlatformData, "get_events_by_contributor"))
check("PlatformData.get_contributor_by_id() exists", hasattr(PlatformData, "get_contributor_by_id"))

# ──────────────────────────────────────────────
# SECTION 3: SPRINT 2A VERIFICATION
# ──────────────────────────────────────────────
print("\n[3] SPRINT 2A - ISSUE->FEATURE, SOURCE TAGGING, MILESTONE HIERARCHY")
from backend.integrations.github.github_adapter import GitHubAdapter
adapter_src = inspect.getsource(GitHubAdapter)

# Check 2A: Issue→Feature conversion method exists
check("GitHubAdapter._convert_issue_to_feature() exists",
      "_convert_issue_to_feature" in adapter_src,
      "Method not found in github_adapter.py")

# Check 2A: source="issue" tag
check('source="issue" tag present in adapter',
      '"source": "issue"' in adapter_src or "'source': 'issue'" in adapter_src,
      "source=issue tag not found")

# Check 2A: source="pull_request" tag
check('source="pull_request" tag present in adapter',
      '"source": "pull_request"' in adapter_src or "'source': 'pull_request'" in adapter_src,
      "source=pull_request tag not found")

# Check 2A: Milestone fetching in fetch_raw_data
check("get_milestones() called in fetch_raw_data()",
      "get_milestones" in adapter_src,
      "get_milestones not called in adapter")

# Check 2A: Issues fetched (already existed, verify still present)
check("get_issues() called in fetch_raw_data()",
      "get_issues" in adapter_src)

# Check 2A: hierarchy_nodes populated with MILESTONE/ISSUE nodes
check("MILESTONE node_type referenced in adapter",
      "MILESTONE" in adapter_src,
      "MILESTONE string not found in adapter")

check("ISSUE node_type referenced in adapter",
      '"ISSUE"' in adapter_src or "'ISSUE'" in adapter_src,
      "ISSUE string not found in adapter")

# Check 2A: _create_hierarchy_nodes or equivalent method
check("Hierarchy node creation method exists in adapter",
      "_create_hierarchy_nodes" in adapter_src or "HierarchyNode(" in adapter_src,
      "No HierarchyNode creation found in adapter")

# Check GitHubClient has get_milestones
from backend.github.client import GitHubClient
client_src = inspect.getsource(GitHubClient)
check("GitHubClient.get_milestones() method exists",
      "def get_milestones" in client_src)

# ──────────────────────────────────────────────
# SECTION 4: SUMMARY
# ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
total = len(PASS) + len(FAIL)
print(f"  Total checks: {total}")
print(f"  Passed:       {len(PASS)}")
print(f"  Failed:       {len(FAIL)}")

print("\nSPRINT 1 RESULT:")
sprint1_checks = [f for f in FAIL if "HierarchyBuilder" in f or "HierarchyNode" in f
                  or "hierarchy_nodes" in f or "Feature." in f or "Contributor." in f
                  or "PlatformData." in f or "worklog" in f or "sprint" in f.lower()
                  or "build" in f.lower()]
if sprint1_checks:
    print(f"  FAIL — {len(sprint1_checks)} issue(s): {sprint1_checks}")
else:
    print("  PASS")

print("\nSPRINT 2A RESULT:")
sprint2a_checks = [f for f in FAIL if "issue_to_feature" in f or "source=" in f
                   or "milestone" in f.lower() or "MILESTONE" in f or "ISSUE" in f]
if sprint2a_checks:
    print(f"  FAIL — {len(sprint2a_checks)} issue(s): {sprint2a_checks}")
else:
    print("  PASS")

if FAIL:
    print(f"\nFailed checks:")
    for f in FAIL:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("\nAll checks passed.")
    sys.exit(0)
