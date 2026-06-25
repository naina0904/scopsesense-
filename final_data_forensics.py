"""
Final Data Forensics: Inspect exact audit record and trace noisy items.
"""
import sys
import json
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from storage.database import SessionLocal
from storage.models import Audit

print("\n" + "="*80)
print("FINAL DATA FORENSICS: AUDIT RECORD INSPECTION")
print("="*80)

db = SessionLocal()

try:
    # Get the latest audit
    latest_audit = db.query(Audit).order_by(Audit.id.desc()).first()
    
    if not latest_audit:
        print("\nNo audit records in database")
        sys.exit(0)
    
    ai_summary = json.loads(latest_audit.ai_summary)
    
    print(f"\n[AUDIT METADATA]")
    print(f"  Project: {latest_audit.project_name}")
    print(f"  Created: {latest_audit.created_at}")
    print(f"  Health Score: {latest_audit.health_score}")
    print(f"  Semantic Confidence: {latest_audit.semantic_confidence}")
    
    # =========================================================================
    # 1. SEMANTIC_FEATURES INSPECTION
    # =========================================================================
    
    print(f"\n" + "-"*80)
    print("1. SEMANTIC_FEATURES ANALYSIS")
    print("-"*80)
    
    semantic_features = ai_summary.get('semantic_features', [])
    print(f"\nCount: {len(semantic_features)}")
    
    if semantic_features:
        print(f"\nStructure of first item:")
        first_item = semantic_features[0]
        print(f"  Keys: {list(first_item.keys())}")
        print(f"\nFull first 3 items (pretty printed):")
        print(json.dumps(semantic_features[:3], indent=2))
    
    # Check for noisy patterns in semantic_features
    print(f"\n[NOISY ITEM CHECK in semantic_features]")
    noisy_keywords = ['retry', 'action', 'default', 'localization', 'failed', 'exception', 'error', 'fallback']
    for feature in semantic_features:
        name = feature.get('feature_name', '')
        desc = feature.get('description', '')
        for keyword in noisy_keywords:
            if keyword.lower() in name.lower() or keyword.lower() in desc.lower():
                print(f"  ✗ Found '{keyword}' in: {name}")
                print(f"    Description: {desc[:100]}")
    
    # =========================================================================
    # 2. TIMELINE_ANALYSIS INSPECTION
    # =========================================================================
    
    print(f"\n" + "-"*80)
    print("2. TIMELINE_ANALYSIS INSPECTION")
    print("-"*80)
    
    timeline_analysis = ai_summary.get('timeline_analysis', [])
    print(f"\nCount: {len(timeline_analysis)}")
    
    if timeline_analysis:
        print(f"\nStructure of first item:")
        first_item = timeline_analysis[0]
        print(f"  Keys: {list(first_item.keys())}")
        print(f"\nFull first 3 items (pretty printed):")
        print(json.dumps(timeline_analysis[:3], indent=2))
    
    # Check for noisy patterns in timeline_analysis
    print(f"\n[NOISY ITEM CHECK in timeline_analysis]")
    for item in timeline_analysis:
        feature = item.get('feature', '')
        status = item.get('status', '')
        for keyword in noisy_keywords:
            if keyword.lower() in feature.lower() or keyword.lower() in status.lower():
                print(f"  ✗ Found '{keyword}' in feature: {feature}")
                print(f"    Status: {status[:100]}")
    
    # =========================================================================
    # 3. FEATURE_OWNERSHIP INSPECTION
    # =========================================================================
    
    print(f"\n" + "-"*80)
    print("3. FEATURE_OWNERSHIP INSPECTION")
    print("-"*80)
    
    feature_ownership = ai_summary.get('feature_ownership', [])
    print(f"\nCount: {len(feature_ownership)}")
    
    if feature_ownership:
        print(f"\nStructure of first item:")
        first_item = feature_ownership[0]
        print(f"  Keys: {list(first_item.keys())}")
        print(f"\nFull first 3 items (pretty printed):")
        print(json.dumps(feature_ownership[:3], indent=2))
    
    # =========================================================================
    # 4. OPTIONAL_INTELLIGENCE INSPECTION
    # =========================================================================
    
    print(f"\n" + "-"*80)
    print("4. OPTIONAL_INTELLIGENCE INSPECTION")
    print("-"*80)
    
    optional_intelligence = ai_summary.get('optional_intelligence', {})
    print(f"  Keys: {list(optional_intelligence.keys())}")
    
    semantic_matches = optional_intelligence.get('semantic_matches', [])
    print(f"  semantic_matches count: {len(semantic_matches)}")
    
    if semantic_matches:
        print(f"\n  First semantic_match item structure:")
        first_match = semantic_matches[0]
        print(f"    Keys: {list(first_match.keys())}")
        if 'matches' in first_match:
            print(f"    matches sub-keys: {list(first_match['matches'].keys())}")
            if 'documents' in first_match['matches']:
                print(f"    ⚠️  documents field EXISTS (count: {len(first_match['matches']['documents'])})")
                print(f"    Sample doc: {str(first_match['matches']['documents'][0])[:100]}")
            else:
                print(f"    ✓ documents field REMOVED (sanitized)")
    
    # =========================================================================
    # 5. INSIGHTS INSPECTION
    # =========================================================================
    
    print(f"\n" + "-"*80)
    print("5. INSIGHTS INSPECTION")
    print("-"*80)
    
    insights = ai_summary.get('insights', [])
    print(f"\nCount: {len(insights)}")
    
    if insights:
        print(f"\nFirst 3 insights (pretty printed):")
        print(json.dumps(insights[:3], indent=2))
    
    # Check for noisy patterns in insights
    print(f"\n[NOISY ITEM CHECK in insights]")
    for insight in insights:
        title = insight.get('title', '')
        description = insight.get('description', '')
        for keyword in noisy_keywords:
            if keyword.lower() in title.lower() or keyword.lower() in description.lower():
                print(f"  ✗ Found '{keyword}' in title: {title}")
                print(f"    Description: {description[:100]}")
    
    # =========================================================================
    # 6. SCAN ALL FIELDS FOR NOISY KEYWORDS
    # =========================================================================
    
    print(f"\n" + "-"*80)
    print("6. COMPREHENSIVE NOISY KEYWORD SCAN")
    print("-"*80)
    
    def find_noisy_in_dict(obj, path="root"):
        """Recursively search for noisy keywords in dict/list."""
        findings = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                for keyword in noisy_keywords:
                    if keyword.lower() in key.lower():
                        findings.append(f"  {path}.{key} contains '{keyword}'")
                
                if isinstance(value, (dict, list)):
                    findings.extend(find_noisy_in_dict(value, f"{path}.{key}"))
                elif isinstance(value, str):
                    for keyword in noisy_keywords:
                        if keyword.lower() in value.lower():
                            findings.append(f"  {path}.{key} = '{value[:100]}...' (contains '{keyword}')")
                            break
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    findings.extend(find_noisy_in_dict(item, f"{path}[{i}]"))
        
        return findings
    
    all_findings = find_noisy_in_dict(ai_summary)
    if all_findings:
        print("\nNoisy keywords found at:")
        for finding in all_findings[:20]:  # Limit output
            print(finding)
        if len(all_findings) > 20:
            print(f"  ... and {len(all_findings) - 20} more")
    else:
        print("\nNo noisy keywords found in audit result")
    
    # =========================================================================
    # 7. TRACE SPECIFIC NOISY ITEMS (EXAMPLES)
    # =========================================================================
    
    print(f"\n" + "-"*80)
    print("7. TRACE EXAMPLES OF NOISY ITEMS")
    print("-"*80)
    
    # Example 1: Look for items with "retry" in semantic_features
    print("\n[RETRY]")
    retry_features = [f for f in semantic_features if 'retry' in f.get('feature_name', '').lower()]
    if retry_features:
        for f in retry_features:
            print(f"  Found in semantic_features: {f.get('feature_name')}")
            print(f"    JSON path: result.semantic_features[...]")
            print(f"    Source: Phase 1B/2D filtered from extracted_features")
    else:
        print("  Not found in semantic_features")
    
    # Example 2: Look for "action" in timeline
    print("\n[QUICK ACTIONS]")
    action_timeline = [t for t in timeline_analysis if 'action' in t.get('feature', '').lower()]
    if action_timeline:
        for t in action_timeline:
            print(f"  Found in timeline_analysis: {t.get('feature')}")
            print(f"    JSON path: result.timeline_analysis[...]")
            print(f"    Source: Derived from filtered semantic_features")
    else:
        print("  Not found in timeline_analysis")
    
    # Example 3: Look for default handling
    print("\n[DEFAULTS]")
    default_features = [f for f in semantic_features if 'default' in f.get('feature_name', '').lower()]
    if default_features:
        for f in default_features:
            print(f"  Found in semantic_features: {f.get('feature_name')}")
    else:
        print("  Not found in semantic_features")
    
    # Example 4: Check insights for failed-attempt handling
    print("\n[FAILED-ATTEMPT HANDLING]")
    failed_insights = [i for i in insights if 'fail' in i.get('title', '').lower() or 'fail' in i.get('description', '').lower()]
    if failed_insights:
        for i in failed_insights:
            print(f"  Found in insights: {i.get('title')}")
            print(f"    JSON path: result.insights[...]")
    else:
        print("  Not found in insights")
    
    # =========================================================================
    # 8. EXPORT RAW JSON FOR ANALYSIS
    # =========================================================================
    
    print(f"\n" + "-"*80)
    print("8. EXPORTING RAW JSON FOR DETAILED ANALYSIS")
    print("-"*80)
    
    # Create focused JSON dump
    export_data = {
        "metadata": {
            "project": latest_audit.project_name,
            "created": str(latest_audit.created_at),
            "health_score": latest_audit.health_score
        },
        "semantic_features": semantic_features,
        "timeline_analysis": timeline_analysis,
        "feature_ownership": feature_ownership,
        "insights": insights,
        "semantic_matches_count": len(semantic_matches),
        "has_documents": any(
            'documents' in (m.get('matches', {}))
            for m in semantic_matches
        )
    }
    
    export_path = "debug_audit_forensics.json"
    with open(export_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n✓ Exported to: {export_path}")
    
    # =========================================================================
    # 9. SUMMARY AND RECOMMENDATIONS
    # =========================================================================
    
    print(f"\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    print(f"\n[FIELD COUNTS]")
    print(f"  semantic_features: {len(semantic_features)}")
    print(f"  timeline_analysis: {len(timeline_analysis)}")
    print(f"  feature_ownership: {len(feature_ownership)}")
    print(f"  insights: {len(insights)}")
    print(f"  semantic_matches: {len(semantic_matches)}")
    
    print(f"\n[SANITIZATION STATUS]")
    has_docs = any(
        'documents' in (m.get('matches', {}))
        for m in semantic_matches
    )
    if has_docs:
        print(f"  ✗ Documents still in semantic_matches (DB pre-sanitization)")
    else:
        print(f"  ✓ Documents removed from semantic_matches")
    
    print(f"\n[POSSIBLE NOISE SOURCES]")
    print(f"  1. semantic_features - contains {len(semantic_features)} items")
    print(f"  2. timeline_analysis - derived from #1")
    print(f"  3. insights - AI-generated insights")
    print(f"  4. semantic_matches - requirement matching results")
    
    print(f"\n[NEXT STEPS]")
    print(f"  1. Check debug_audit_forensics.json for exact field values")
    print(f"  2. Identify which field contains noisy item")
    print(f"  3. Trace back to audit_workflow source")
    print(f"  4. Apply targeted fix")
    
finally:
    db.close()

print(f"\n" + "="*80)
