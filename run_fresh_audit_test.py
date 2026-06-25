"""
Run a complete Aurora audit through the full service pipeline to test sanitization on fresh data.
"""
import sys
import json
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.audit_service import AuditService
from storage.database import SessionLocal
from storage.models import Audit

print("\n[STEP 1] Running fresh Aurora audit through full service...")
audit_service = AuditService()

try:
    result = audit_service.execute_audit(
        owner="aurora",
        repo="engineering-platform",
        repo_path=".",
        task_id="fresh_test_sanitization",
        provider_name=None  # Will use default or mock
    )
    print(f"✓ Audit executed successfully")
    print(f"  Result keys: {list(result.keys())}")
except Exception as e:
    print(f"✗ Audit execution failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[STEP 2] Querying the freshly persisted audit from DB...")
db = SessionLocal()

# Get all Aurora audits, sorted by date
aurora_audits = (
    db.query(Audit)
    .filter(Audit.project_name.contains('aurora'))
    .order_by(Audit.created_at.desc())
    .all()
)

print(f"Total Aurora audits in DB: {len(aurora_audits)}")
for audit in aurora_audits:
    print(f"  - {audit.created_at} : {audit.project_name}")

if aurora_audits:
    latest = aurora_audits[0]
    print(f"\n[CHECKING LATEST AURORA AUDIT]")
    print(f"Created: {latest.created_at}")
    
    ai_summary = json.loads(latest.ai_summary)
    
    print(f"\n[AUDIT STRUCTURE]")
    print(f"  semantic_features: {len(ai_summary.get('semantic_features', []))}")
    print(f"  feature_ownership: {len(ai_summary.get('feature_ownership', []))}")
    print(f"  timeline_analysis: {len(ai_summary.get('timeline_analysis', []))}")
    
    # Check for documents
    optional_intel = ai_summary.get('optional_intelligence', {})
    semantic_matches_list = optional_intel.get('semantic_matches', [])
    root_semantic_matches = ai_summary.get('semantic_matches', [])
    
    has_documents = False
    locations = []
    
    if isinstance(semantic_matches_list, list):
        for i, item in enumerate(semantic_matches_list):
            if isinstance(item, dict) and 'matches' in item:
                if 'documents' in item['matches']:
                    has_documents = True
                    locations.append(f"optional_intelligence.semantic_matches[{i}]")
    
    if isinstance(root_semantic_matches, list):
        for i, item in enumerate(root_semantic_matches):
            if isinstance(item, dict) and 'matches' in item:
                if 'documents' in item['matches']:
                    has_documents = True
                    locations.append(f"semantic_matches[{i}]")
    
    print(f"\n[SANITIZATION RESULT]")
    if not has_documents:
        print(f"✓✓✓ SANITIZATION WORKING! ✓✓✓")
        print(f"  Documents field removed from all semantic_matches")
        print(f"  Only preserved: ids, metadatas, distances, confidence")
    else:
        print(f"✗✗✗ SANITIZATION FAILED ✗✗✗")
        print(f"  Documents still present in:")
        for loc in locations:
            print(f"    - {loc}")
    
    # Show first match structure
    if semantic_matches_list and len(semantic_matches_list) > 0:
        first = semantic_matches_list[0]
        if isinstance(first, dict) and 'matches' in first:
            matches = first['matches']
            print(f"\n[FIRST SEMANTIC MATCH STRUCTURE]")
            print(f"  Requirement: {first.get('requirement', 'N/A')}")
            print(f"  Fields: {list(matches.keys())}")
else:
    print("No Aurora audits found in database")

db.close()
