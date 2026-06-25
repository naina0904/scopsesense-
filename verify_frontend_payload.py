"""
End-to-End Frontend Verification

Captures what the frontend is actually receiving and comparing with backend state.

Trace path:
1. /audit/latest endpoint
2. API response payload 
3. Database record
4. Memory snapshot
5. Frontend rendering data
"""
import sys
import json
import os
import urllib.request
from urllib.error import HTTPError, URLError
from datetime import datetime

# Ensure the verification script targets the running Compose database
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:12345@localhost:5433/scopesense"
)

sys.path.insert(0, os.path.dirname(__file__))

from backend.storage.database import SessionLocal
from backend.storage.models import Audit

API_BASE_URL = os.getenv('AUDIT_API_URL', 'http://localhost:8000')
API_LATEST_URL = f"{API_BASE_URL}/audit/latest"

print("\n" + "="*80)
print("FRONTEND RENDERING VERIFICATION")
print("="*80)


def fetch_latest_audit_http():
    print(f"\n[PHASE 1] HTTP GET {API_LATEST_URL}")
    print("-" * 80)
    try:
        with urllib.request.urlopen(API_LATEST_URL, timeout=15) as response:
            raw = response.read().decode('utf-8')
            payload = json.loads(raw)
            print(f"\nHTTP GET succeeded: status={response.status}")
            return payload
    except HTTPError as exc:
        print(f"\nHTTPError: {exc.code} {exc.reason}")
    except URLError as exc:
        print(f"\nURLError: {exc.reason}")
    except Exception as exc:
        print(f"\nUnexpected error fetching API payload: {exc}")
    sys.exit(1)


def get_audit_record_summary(audit):
    return {
        'id': getattr(audit, 'id', None),
        'project_name': getattr(audit, 'project_name', None),
        'created_at': getattr(audit, 'created_at', None),
        'health_score': getattr(audit, 'health_score', None),
        'semantic_confidence': getattr(audit, 'semantic_confidence', None),
        'github_owner': getattr(audit, 'github_owner', None),
        'github_repo': getattr(audit, 'github_repo', None),
    }

# ============================================================================
# PHASE 1: GET API RESPONSE (what frontend receives)
# ============================================================================

api_response_payload = fetch_latest_audit_http()
api_response_inner = api_response_payload.get('result') if isinstance(api_response_payload, dict) and 'result' in api_response_payload else api_response_payload

print(f"\n[PHASE 1] Simulate Frontend API Call: GET /audit/latest")
print("-" * 80)
print(f"\nAPI Response Status: ✓ Retrieved")
print(f"  Keys in response: {list(api_response_payload.keys())[:10]}...")
print(f"  Has result wrapper: {'result' in api_response_payload}")
print(f"  semantic_features count: {len(api_response_inner.get('semantic_features', []))}")
print(f"  timeline_analysis count: {len(api_response_inner.get('timeline_analysis', []))}")

api_semantic_features = api_response_inner.get('semantic_features', [])
api_timeline_analysis = api_response_inner.get('timeline_analysis', [])
print(f"\nAPI semantic_features (first 3):")
for i, feat in enumerate(api_semantic_features[:3]):
    print(f"  {i+1}. {feat.get('feature_name', 'UNKNOWN')}")

print(f"\nAPI timeline_analysis (first 3):")
for i, item in enumerate(api_timeline_analysis[:3]):
    print(f"  {i+1}. {item.get('feature', 'UNKNOWN')}")

print(f"\nAPI metadata: audit_id={api_response_inner.get('audit_id')}, created_at={api_response_inner.get('created_at')}, project_name={api_response_inner.get('project_name')}")

# ============================================================================
# PHASE 2: GET DATABASE RECORD (raw DB state)
# ============================================================================

print(f"\n[PHASE 2] Database Audit Record")
print("-" * 80)

db = SessionLocal()
audit_count = db.query(Audit).count()
print(f"\nDatabase audits found: {audit_count}")

latest_audit = db.query(Audit).order_by(Audit.id.desc()).first()

if latest_audit:
    db_ai_summary = json.loads(latest_audit.ai_summary)
    
    print(f"\nLatest Database Record:")
    print(f"  Project: {latest_audit.project_name}")
    print(f"  Created: {latest_audit.created_at}")
    print(f"  ID: {latest_audit.id}")
    print(f"  Health Score: {latest_audit.health_score}")
    
    db_semantic_features = db_ai_summary.get('semantic_features', [])
    db_timeline_analysis = db_ai_summary.get('timeline_analysis', [])
    
    print(f"\n  semantic_features count: {len(db_semantic_features)}")
    print(f"  timeline_analysis count: {len(db_timeline_analysis)}")
    
    print(f"\n  DB semantic_features (first 3):")
    for i, feat in enumerate(db_semantic_features[:3]):
        print(f"    {i+1}. {feat.get('feature_name', 'UNKNOWN')}")
    
    print(f"\n  DB timeline_analysis (first 3):")
    for i, item in enumerate(db_timeline_analysis[:3]):
        print(f"    {i+1}. {item.get('feature', 'UNKNOWN')}")
else:
    db_ai_summary = {}
    print("\nNo audit records in database")

# ============================================================================
# PHASE 3: CHECK MEMORY SNAPSHOT
# ============================================================================

print(f"\n[PHASE 3] Memory Snapshot")
print("-" * 80)

memory_snapshot_path = "backend/memory/storage/local_aurora-engineering-platform.json"

memory_data = None
if os.path.exists(memory_snapshot_path):
    with open(memory_snapshot_path, 'r') as f:
        memory_snapshots = json.load(f)
        print(f"\nMemory snapshots found: {len(memory_snapshots)}")
        
        if memory_snapshots:
            latest_snapshot = memory_snapshots[-1]  # Most recent
            memory_data = latest_snapshot.get('data', {})
            
            print(f"Latest snapshot timestamp: {latest_snapshot.get('timestamp')}")
            print(f"  semantic_features count: {len(memory_data.get('semantic_features', []))}")
            print(f"  timeline_analysis count: {len(memory_data.get('timeline_analysis', []))}")
else:
    print(f"\nMemory snapshot not found at: {memory_snapshot_path}")

# ============================================================================
# PHASE 4: COMPARE ALL THREE SOURCES
# ============================================================================

print(f"\n[PHASE 4] Comparison: API vs DB vs Memory")
print("-" * 80)

# Extract identifiers
def get_feature_names(features):
    return [f.get('feature_name', '') for f in features]

def get_timeline_names(timelines):
    return [t.get('feature', '') for t in timelines]

api_feat_names = get_feature_names(api_semantic_features)
db_feat_names = get_feature_names(db_semantic_features)
mem_feat_names = get_feature_names(memory_data.get('semantic_features', [])) if memory_data else []

print(f"\nSemantic Features Names Comparison:")
print(f"  API:    {api_feat_names}")
print(f"  DB:     {db_feat_names}")
print(f"  Memory: {mem_feat_names}")

match_api_db = api_feat_names == db_feat_names
match_db_mem = db_feat_names == mem_feat_names
match_api_mem = api_feat_names == mem_feat_names

print(f"\nMatches:")
print(f"  API == DB:     {'✓ YES' if match_api_db else '✗ NO'}")
print(f"  DB == Memory:  {'✓ YES' if match_db_mem else '✗ NO'}")
print(f"  API == Memory: {'✓ YES' if match_api_mem else '✗ NO'}")

# ============================================================================
# PHASE 5: CHECK FOR DOCUMENTS IN API RESPONSE
# ============================================================================

print(f"\n[PHASE 5] Document Sanitization Status")
print("-" * 80)

def has_documents(audit_dict):
    """Check if documents exist anywhere in audit dict"""
    optional = audit_dict.get('optional_intelligence', {})
    matches = optional.get('semantic_matches', [])
    
    for item in matches:
        if isinstance(item, dict) and 'documents' in item:
            return True
        if isinstance(item, dict) and 'matches' in item and isinstance(item['matches'], dict) and 'documents' in item['matches']:
            return True
    
    root_matches = audit_dict.get('semantic_matches', [])
    for item in root_matches:
        if isinstance(item, dict) and 'documents' in item:
            return True
        if isinstance(item, dict) and 'matches' in item and isinstance(item['matches'], dict) and 'documents' in item['matches']:
            return True
    
    return False

api_has_docs = has_documents(api_response_inner)
db_has_docs = has_documents(db_ai_summary)
mem_has_docs = has_documents(memory_data) if memory_data else False

print(f"\nDocuments Present:")
print(f"  API Response:     {'✗ YES (NOT SANITIZED)' if api_has_docs else '✓ NO (sanitized)'}")
print(f"  Database Record:  {'✗ YES (NOT SANITIZED)' if db_has_docs else '✓ NO (sanitized)'}")
print(f"  Memory Snapshot:  {'✗ YES (NOT SANITIZED)' if mem_has_docs else '✓ NO (sanitized)'}")

# ============================================================================
# PHASE 6: TRACE FRONTEND RENDERING
# ============================================================================

print(f"\n[PHASE 6] Frontend Rendering Trace")
print("-" * 80)

print(f"\nFeaturesPage.jsx rendering:")
print(f"  API call: axios.get('/audit/latest')")
print(f"  Extract: response.data.result.semantic_features")
print(f"  Count: {len(api_semantic_features)} features")
print(f"  Render: FeatureCard per feature")
print(f"  Fields: feature.name, feature.developer, feature.status")

print(f"\nTimelinePage.jsx rendering:")
print(f"  API call: axios.get('/audit/latest')")
print(f"  Extract: response.data.result.timeline_analysis")
print(f"  Count: {len(api_timeline_analysis)} items")
print(f"  Render: TimelineChart + item list")
print(f"  Fields: item.feature, item.status, item.delay_days")

# ============================================================================
# PHASE 7: IDENTIFY NOISY ITEMS (if present)
# ============================================================================

print(f"\n[PHASE 7] Scan for Noisy Items")
print("-" * 80)

noisy_keywords = ['retry', 'quick', 'action', 'default', 'locali', 'failed', 'error', 'handle']

def find_noisy_in_features(features):
    noisy = []
    for feat in features:
        name = feat.get('feature_name', '').lower()
        for kw in noisy_keywords:
            if kw in name:
                noisy.append(feat.get('feature_name', ''))
                break
    return noisy

api_noisy = find_noisy_in_features(api_semantic_features)
db_noisy = find_noisy_in_features(db_semantic_features)
mem_noisy = find_noisy_in_features(memory_data.get('semantic_features', [])) if memory_data else []

print(f"\nNoisy Items Found:")
print(f"  API Response:    {api_noisy if api_noisy else '✓ None'}")
print(f"  Database:        {db_noisy if db_noisy else '✓ None'}")
print(f"  Memory:          {mem_noisy if mem_noisy else '✓ None'}")

# ============================================================================
# PHASE 8: DIAGNOSIS
# ============================================================================

print(f"\n[PHASE 8] Diagnosis")
print("-" * 80)

print(f"\nData Source Analysis:")

if match_api_db and match_db_mem:
    print(f"  ✓ All sources (API, DB, Memory) are IDENTICAL")
    print(f"    → Using same audit record")
    
    if api_has_docs:
        print(f"    → BUT documents NOT removed by API sanitization")
        print(f"      ROOT CAUSE: API sanitization not working")
    else:
        print(f"    → AND documents properly removed")
        print(f"      → No noisy data in persistence layer")
elif not match_api_db:
    print(f"  ✗ API response DIFFERS from Database")
    print(f"    → API is returning different data than what's stored")
    print(f"      ROOT CAUSE: API endpoint mismatch or caching issue")
elif not match_db_mem:
    print(f"  ✗ Database DIFFERS from Memory snapshot")
    print(f"    → Different audit records or out-of-sync")
    print(f"      ROOT CAUSE: Multiple audit records or stale memory")
else:
    print(f"  ? Partial mismatch - investigate further")

print(f"\nDocumentation Sanitization Status:")
if api_has_docs:
    print(f"  ✗ Documents STILL in API response")
    print(f"    → Sanitization not applied or not working")
else:
    print(f"  ✓ Documents REMOVED in API response")
    print(f"    → Sanitization working correctly")

# ============================================================================
# EXPORT DIAGNOSTIC DATA
# ============================================================================

print(f"\n[PHASE 9] Export Diagnostic Data")
print("-" * 80)

export_data = {
    "timestamp": datetime.now().isoformat(),
    "api_response": {
        "semantic_features_count": len(api_semantic_features),
        "semantic_features_names": api_feat_names,
        "timeline_analysis_count": len(api_timeline_analysis),
        "has_documents": api_has_docs,
        "audit_id": api_response_payload.get('audit_run_id'),
        "generated_at": api_response_payload.get('generated_at'),
    },
    "database": {
        "project_name": latest_audit.project_name if latest_audit else None,
        "created_at": str(latest_audit.created_at) if latest_audit else None,
        "semantic_features_count": len(db_semantic_features),
        "semantic_features_names": db_feat_names,
        "timeline_analysis_count": len(db_timeline_analysis),
        "has_documents": db_has_docs,
        "db_id": latest_audit.id if latest_audit else None,
    },
    "matches": {
        "api_eq_db": match_api_db,
        "db_eq_memory": match_db_mem,
        "api_eq_memory": match_api_mem,
    },
    "noisy_items": {
        "api": api_noisy,
        "database": db_noisy,
        "memory": mem_noisy,
    }
}

with open("verify_payload.json", 'w') as f:
    json.dump(export_data, f, indent=2)

print(f"\nExported to: verify_payload.json")

db.close()

print(f"\n" + "="*80)
