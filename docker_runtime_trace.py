#!/usr/bin/env python3
"""
Docker Runtime Trace
====================
Executes inside backend-worker container to verify:
1. Exact extractor.py file path loaded at runtime
2. Container image build timestamp
3. Whether _fallback_heuristic_extract() exists
4. Whether extract_features() executed
5. Parsed content length
6. Feature count returned by extract_features()
7. Feature count immediately before save_audit()
"""

import sys
import os
import json
import inspect
import subprocess
from pathlib import Path

print("\n" + "="*70)
print("DOCKER RUNTIME TRACE - Backend Worker Verification")
print("="*70 + "\n")

# =========================================================================
# 1. EXTRACTOR MODULE PATH
# =========================================================================
print("[1] EXTRACTOR MODULE PATH")
print("-" * 70)
try:
    from backend.srs.extractor import SRSFeatureExtractor
    extractor_path = inspect.getfile(SRSFeatureExtractor)
    print(f"    Module file: {extractor_path}")
    print(f"    Exists: {os.path.exists(extractor_path)}")
    print(f"    Size: {os.path.getsize(extractor_path)} bytes")
    if os.path.exists(extractor_path):
        stat_info = os.stat(extractor_path)
        print(f"    Modified: {stat_info.st_mtime}")
except Exception as e:
    print(f"    ERROR: {e}")

# =========================================================================
# 2. CONTAINER IMAGE BUILD TIMESTAMP
# =========================================================================
print("\n[2] CONTAINER IMAGE BUILD TIMESTAMP")
print("-" * 70)
try:
    result = subprocess.run(
        ["docker", "inspect", "--format={{.Created}}", "scopesense-v2-backend-worker"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        build_time = result.stdout.strip()
        print(f"    Image build time: {build_time}")
    else:
        print(f"    ERROR: {result.stderr}")
except Exception as e:
    print(f"    ERROR (docker inspect failed): {e}")

# =========================================================================
# 3. CHECK FOR _fallback_heuristic_extract METHOD
# =========================================================================
print("\n[3] FALLBACK HEURISTIC METHOD")
print("-" * 70)
try:
    extractor = SRSFeatureExtractor()
    has_fallback = hasattr(extractor, '_fallback_heuristic_extract')
    print(f"    _fallback_heuristic_extract exists: {has_fallback}")
    if has_fallback:
        method = getattr(extractor, '_fallback_heuristic_extract')
        method_source_lines = len(inspect.getsource(method).split('\n'))
        print(f"    Method source lines: {method_source_lines}")
except Exception as e:
    print(f"    ERROR: {e}")

# =========================================================================
# 4. TEST EXTRACT_FEATURES EXECUTION
# =========================================================================
print("\n[4] EXTRACT_FEATURES EXECUTION TEST")
print("-" * 70)
try:
    extractor = SRSFeatureExtractor()
    
    # Sample SRS content to test extraction
    sample_content = """
Feature: User Authentication
Hours: 40
Developers: Alice, Charlie
Timeline: 2w
Priority: High

Feature: Realtime Notification System
Hours: 56
Developers: Alice, David, Charlie
Timeline: 14d
Priority: High

Feature: AI Insights Dashboard
Hours: 72
Developers: Bob, Charlie
Timeline: 3w
Priority: Critical

Feature: Role-Based Access Control
Hours: 32
Developers: Alice, Bob
Timeline: 2w
Priority: High

Feature: Logging and Monitoring
Hours: 24
Developers: David
Timeline: 1.5w
Priority: Medium
"""
    
    print(f"    Sample SRS content length: {len(sample_content)} chars")
    print(f"    Calling extract_features()...")
    features = extractor.extract_features(sample_content)
    print(f"    extract_features() executed successfully")
    print(f"    Type returned: {type(features)}")
    print(f"    Feature count: {len(features) if features else 0}")
    
    if features and len(features) > 0:
        print(f"    First feature: {features[0].get('feature_name', 'N/A')}")
    
except Exception as e:
    print(f"    ERROR: {e}")
    import traceback
    traceback.print_exc()

# =========================================================================
# 5. QUERY DATABASE FOR AUDIT ID=21
# =========================================================================
print("\n[5] DATABASE AUDIT ID=21 INSPECTION")
print("-" * 70)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    # Use Docker internal DB connection
    db_host = os.getenv("DATABASE_URL", "postgresql://postgres:12345@db:5432/scopesense").split("@")[1].split("/")[0]
    db_host = "db"  # Inside container, use service name
    
    conn = psycopg2.connect(
        host=db_host,
        port=5432,
        dbname="scopesense",
        user="postgres",
        password="12345"
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT id, project_name, length(ai_summary) as len, created_at FROM audits WHERE id=21;")
    row = cur.fetchone()
    
    if row:
        print(f"    Audit ID 21 found:")
        print(f"      Project: {row['project_name']}")
        print(f"      ai_summary length: {row['len']} bytes")
        print(f"      Created: {row['created_at']}")
        
        # Get the actual ai_summary JSON
        cur.execute("SELECT ai_summary FROM audits WHERE id=21;")
        ai_summary = cur.fetchone()['ai_summary']
        
        if ai_summary:
            try:
                obj = json.loads(ai_summary)
                print(f"      Keys in payload: {list(obj.keys())[:10]}")
                print(f"      semantic_features count: {len(obj.get('semantic_features', []))}")
                print(f"      feature_ownership count: {len(obj.get('feature_ownership', []))}")
                print(f"      timeline_analysis count: {len(obj.get('timeline_analysis', []))}")
                print(f"      insights count: {len(obj.get('insights', []))}")
            except Exception as parse_err:
                print(f"      JSON parse error: {parse_err}")
    else:
        print(f"    Audit ID 21 NOT FOUND in database")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"    ERROR: {e}")
    import traceback
    traceback.print_exc()

# =========================================================================
# 6. CELERY TASK STATE FOR AUDIT ID=21
# =========================================================================
print("\n[6] CELERY TASK STATE")
print("-" * 70)
try:
    from backend.tasks.celery_app import celery
    
    # Try to find tasks that match the audit_run_id
    print(f"    Celery app: {celery}")
    print(f"    Celery broker: {celery.conf.broker_url}")
    
    # Query recent completed tasks
    inspect_obj = celery.control.Inspect()
    active = inspect_obj.active()
    if active:
        print(f"    Active tasks: {len(active) if active else 0}")
    
except Exception as e:
    print(f"    ERROR: {e}")

# =========================================================================
# 7. BACKEND AUDIT WORKFLOW VERIFICATION
# =========================================================================
print("\n[7] BACKEND AUDIT WORKFLOW CODE")
print("-" * 70)
try:
    from backend.core.audit_workflow import AuditWorkflow
    workflow_path = inspect.getfile(AuditWorkflow)
    print(f"    Workflow module: {workflow_path}")
    print(f"    Exists: {os.path.exists(workflow_path)}")
except Exception as e:
    print(f"    ERROR: {e}")

print("\n" + "="*70)
print("TRACE COMPLETE")
print("="*70 + "\n")
