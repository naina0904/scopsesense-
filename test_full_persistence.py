"""
Test that persisted Aurora audit does NOT contain documents field.
Queries the latest persisted audit from DB to verify sanitization.
"""
import sys
import json
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from storage.database import SessionLocal
from storage.models import Audit

# Query latest Aurora audit from DB
print("\n[TEST] Querying persisted audits from DB...")
try:
    db = SessionLocal()
    
    # First, list all audits to see what we have
    all_audits = db.query(Audit).order_by(Audit.created_at.desc()).limit(5).all()
    print(f"Total recent audits in DB: {len(all_audits)}")
    for audit in all_audits:
        print(f"  - {audit.project_name} ({audit.created_at})")
    
    # Get the most recent audit (any project)
    latest_audit = db.query(Audit).order_by(Audit.created_at.desc()).first()
    
    if latest_audit:
        ai_summary = json.loads(latest_audit.ai_summary)
        
        print(f"\n[CHECKING LATEST AUDIT]")
        print(f"Project: {latest_audit.project_name}")
        print(f"Created: {latest_audit.created_at}")
        
        print(f"\n[AUDIT STRUCTURE]")
        print(f"  semantic_features count: {len(ai_summary.get('semantic_features', []))}")
        print(f"  feature_ownership count: {len(ai_summary.get('feature_ownership', []))}")
        print(f"  timeline_analysis count: {len(ai_summary.get('timeline_analysis', []))}")
        
        # Deep check for documents field in semantic_matches
        optional_intel = ai_summary.get('optional_intelligence', {})
        semantic_matches_list = optional_intel.get('semantic_matches', [])
        
        has_documents = False
        doc_locations = []
        
        # Check optional_intelligence.semantic_matches[*].matches.documents
        if isinstance(semantic_matches_list, list):
            for i, item in enumerate(semantic_matches_list):
                if isinstance(item, dict) and 'matches' in item:
                    if 'documents' in item['matches']:
                        has_documents = True
                        doc_locations.append(f"optional_intelligence.semantic_matches[{i}].matches.documents")
        
        # Check root-level semantic_matches
        root_semantic_matches = ai_summary.get('semantic_matches', [])
        if isinstance(root_semantic_matches, list):
            for i, item in enumerate(root_semantic_matches):
                if isinstance(item, dict) and 'matches' in item:
                    if 'documents' in item['matches']:
                        has_documents = True
                        doc_locations.append(f"semantic_matches[{i}].matches.documents")
        
        print(f"\n[SANITIZATION STATUS]")
        if not has_documents:
            print(f"✓ SUCCESS: No 'documents' field in persisted audit")
            print(f"  - Sanitization working correctly")
        else:
            print(f"✗ FAILED: Documents still present:")
            for loc in doc_locations:
                print(f"    - {loc}")
        
        # Show structure of first semantic match
        print(f"\n[PRESERVED FIELDS IN SEMANTIC_MATCHES]")
        if semantic_matches_list and len(semantic_matches_list) > 0:
            first_match = semantic_matches_list[0]
            if isinstance(first_match, dict) and 'matches' in first_match:
                matches_obj = first_match['matches']
                fields = list(matches_obj.keys())
                print(f"  Fields present: {fields}")
                
                # Show preserved metadata
                if 'metadatas' in matches_obj:
                    print(f"  metadatas preserved: ✓")
                if 'ids' in matches_obj:
                    print(f"  ids preserved: ✓")
                if 'distances' in matches_obj:
                    print(f"  distances preserved: ✓")
                if 'documents' in matches_obj:
                    print(f"  documents: ✗ SHOULD NOT BE HERE")
    else:
        print("No audit records found in database")
    
    db.close()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
