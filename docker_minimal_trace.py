#!/usr/bin/env python3
"""
Minimal Docker Runtime Trace
=============================
Quick inspection of backend-worker runtime state - no LLM calls
"""

import sys
import os
import json
import inspect
import subprocess

print("\n" + "="*70)
print("DOCKER RUNTIME TRACE - Backend Worker Verification")
print("="*70 + "\n")

# 1. EXTRACTOR MODULE PATH
print("[1] EXTRACTOR MODULE PATH")
print("-" * 70)
try:
    from backend.srs.extractor import SRSFeatureExtractor
    extractor_path = inspect.getfile(SRSFeatureExtractor)
    print(f"    File: {extractor_path}")
    print(f"    Exists: {os.path.exists(extractor_path)}")
    print(f"    Size: {os.path.getsize(extractor_path)} bytes")
except Exception as e:
    print(f"    ERROR: {e}")

# 2. CONTAINER IMAGE BUILD TIMESTAMP
print("\n[2] CONTAINER IMAGE BUILD DATE")
print("-" * 70)
try:
    result = subprocess.run(
        ["docker", "inspect", "scopesense-v2-backend-worker"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        import json as json_lib
        data = json_lib.loads(result.stdout)
        if data and len(data) > 0:
            created = data[0].get("Created", "N/A")
            print(f"    Created: {created}")
except Exception as e:
    print(f"    ERROR: {e}")

# 3. CHECK METHODS
print("\n[3] FALLBACK HEURISTIC METHOD")
print("-" * 70)
try:
    extractor = SRSFeatureExtractor()
    has_fallback = hasattr(extractor, '_fallback_heuristic_extract')
    print(f"    Exists: {has_fallback}")
except Exception as e:
    print(f"    ERROR: {e}")

# 4. DATABASE AUDIT ID=21
print("\n[4] AUDIT ID=21 DATABASE STATE")
print("-" * 70)
try:
    import psycopg2
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:12345@db:5432/scopesense")
    
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    cur.execute("SELECT id, project_name, length(ai_summary) as len FROM audits WHERE id=21;")
    row = cur.fetchone()
    
    if row:
        print(f"    ID: {row[0]}")
        print(f"    Project: {row[1]}")
        print(f"    ai_summary length: {row[2]} bytes")
        
        # Get actual data
        cur.execute("SELECT ai_summary FROM audits WHERE id=21;")
        ai_summary = cur.fetchone()[0]
        
        if ai_summary:
            try:
                obj = json.loads(ai_summary)
                print(f"    semantic_features: {len(obj.get('semantic_features', []))}")
                print(f"    feature_ownership: {len(obj.get('feature_ownership', []))}")
                print(f"    timeline_analysis: {len(obj.get('timeline_analysis', []))}")
                print(f"    insights: {len(obj.get('insights', []))}")
            except Exception as e:
                print(f"    JSON error: {e}")
    else:
        print(f"    Audit ID 21 NOT FOUND")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"    ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("TRACE COMPLETE")
print("="*70 + "\n")
