#!/usr/bin/env python3
"""Run an Aurora audit with SRS to generate classification metrics."""

import json
import asyncio
from pathlib import Path
from backend.core.audit_workflow import AuditWorkflow


async def run_aurora_audit_with_srs():
    """Run audit with SRS file to generate classification metrics."""
    
    # Create project context
    workflow = AuditWorkflow()
    
    # Run audit with SRS
    srs_path = Path("aurora_srs.txt")
    
    # Create a minimal repository context dict
    repository_context = {
        "repo_path": ".",
        "languages": ["python"],
        "file_count": 100,
        "total_lines": 50000
    }
    
    print("[*] Running Aurora audit with SRS file...")
    result = workflow.execute_audit(
        repository_context=repository_context,
        srs_path=str(srs_path),
        provider="openai",  # or default provider
        audit_run_id="aurora-classification-test"
    )
    
    print("[✓] Audit completed")
    
    # Check for classification metrics
    debug_extraction = result.get("debug_extraction", {})
    classification = debug_extraction.get("classification", {})
    
    if classification:
        print("[✓] Classification metrics found!")
        print(json.dumps(classification, indent=2))
    else:
        print("[✗] No classification metrics found")
        print(f"debug_extraction keys: {list(debug_extraction.keys())}")
    
    # Show summary
    semantic_features = result.get("semantic_features", [])
    print(f"\n[*] Total semantic features: {len(semantic_features)}")
    print(f"[*] Sample feature names:")
    for feature in semantic_features[:5]:
        print(f"    - {feature.get('feature_name', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(run_aurora_audit_with_srs())
