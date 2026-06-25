"""
Deep diagnostic: Look for noisy items in debug_extraction and other debug fields.
"""
import sys
import json
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from storage.database import SessionLocal
from storage.models import Audit

db = SessionLocal()

try:
    latest_audit = db.query(Audit).order_by(Audit.id.desc()).first()
    
    if not latest_audit:
        print("No audit records")
        sys.exit(0)
    
    ai_summary = json.loads(latest_audit.ai_summary)
    
    # =========================================================================
    # 1. CHECK DEBUG_EXTRACTION FIELD
    # =========================================================================
    
    print("\n" + "="*80)
    print("DEBUG_EXTRACTION FIELD INSPECTION")
    print("="*80)
    
    debug_extraction = ai_summary.get('debug_extraction', {})
    
    if debug_extraction:
        print(f"\nDebug extraction keys: {list(debug_extraction.keys())}")
        
        # Check for extracted features (before filtering)
        extracted_features = debug_extraction.get('extracted_features', [])
        print(f"\nExtracted features (before filtering): {len(extracted_features)} items")
        
        if extracted_features:
            print(f"\nFirst 5 extracted features:")
            for i, feat in enumerate(extracted_features[:5]):
                name = feat.get('feature_name', 'UNKNOWN')
                classification = feat.get('classification', 'UNKNOWN')
                print(f"  {i+1}. {name} (classification: {classification})")
            
            # Look for noisy keywords
            print(f"\n[SEARCHING FOR NOISY PATTERNS IN EXTRACTED FEATURES]")
            noisy_keywords = ['retry', 'quick', 'action', 'default', 'locali', 'failed', 'error', 'exception', 'handle']
            found_noisy = False
            
            for feat in extracted_features:
                name = feat.get('feature_name', '').lower()
                for keyword in noisy_keywords:
                    if keyword in name:
                        found_noisy = True
                        print(f"  ✗ Found '{keyword}' in: {feat.get('feature_name')}")
                        print(f"    Classification: {feat.get('classification')}")
        
        # Check classification details
        classification_debug = debug_extraction.get('classification', {})
        if classification_debug:
            print(f"\n[CLASSIFICATION DEBUG INFO]")
            print(f"  Keys: {list(classification_debug.keys())}")
            
            kept = classification_debug.get('kept_count', 0)
            filtered = classification_debug.get('filtered_count', 0)
            
            print(f"\n  Kept count: {kept}")
            print(f"  Filtered count: {filtered}")
            
            # Show which features were filtered out
            filtered_features = classification_debug.get('filtered_features', [])
            if filtered_features:
                print(f"\n  Filtered features:")
                for feat in filtered_features:
                    name = feat.get('feature_name', 'UNKNOWN')
                    category = feat.get('category', 'UNKNOWN')
                    print(f"    - {name} (category: {category})")
    else:
        print("\nNo debug_extraction field found")
    
    # =========================================================================
    # 2. CHECK FOR FALLBACK INDICATORS
    # =========================================================================
    
    print(f"\n" + "="*80)
    print("FALLBACK & ERROR DETECTION")
    print("="*80)
    
    # Look for any error-related fields
    print(f"\n[TOP-LEVEL ERROR/FALLBACK FIELDS]")
    suspicious_fields = ['error', 'failed', 'fallback', 'exception', 'warning', 'retry']
    
    for key in ai_summary.keys():
        for pattern in suspicious_fields:
            if pattern in key.lower():
                value = ai_summary[key]
                print(f"  Found: {key} = {str(value)[:100]}")
    
    # =========================================================================
    # 3. CHECK EXTRACTED FEATURES vs SEMANTIC FEATURES
    # =========================================================================
    
    print(f"\n" + "="*80)
    print("EXTRACTED vs SEMANTIC FEATURES COMPARISON")
    print("="*80)
    
    if debug_extraction and 'extracted_features' in debug_extraction:
        extracted = debug_extraction['extracted_features']
        semantic = ai_summary.get('semantic_features', [])
        
        print(f"\nExtracted: {len(extracted)} features")
        print(f"Semantic (after filtering): {len(semantic)} features")
        
        extracted_names = set(f.get('feature_name') for f in extracted)
        semantic_names = set(f.get('feature_name') for f in semantic)
        
        filtered_out = extracted_names - semantic_names
        
        if filtered_out:
            print(f"\n[FEATURES FILTERED OUT BY PHASE 1B]")
            print(f"Count: {len(filtered_out)}")
            for name in filtered_out:
                print(f"  - {name}")
        
        # Now check if any filtered-out features have noisy keywords
        print(f"\n[NOISY KEYWORDS IN FILTERED-OUT FEATURES]")
        noisy_keywords = ['retry', 'quick', 'action', 'default', 'locali', 'failed', 'error', 'exception', 'handle']
        found = False
        
        for feat in extracted:
            name = feat.get('feature_name', '')
            if name not in semantic_names:  # This feature was filtered out
                for keyword in noisy_keywords:
                    if keyword.lower() in name.lower():
                        found = True
                        print(f"  ✗ {name} (classification: {feat.get('classification')})")
        
        if not found:
            print("  No noisy keywords found in filtered-out features")
    
    # =========================================================================
    # 4. TRACE INSIGHTS GENERATION
    # =========================================================================
    
    print(f"\n" + "="*80)
    print("INSIGHTS GENERATION TRACE")
    print("="*80)
    
    insights = ai_summary.get('insights', [])
    print(f"\nInsights count: {len(insights)}")
    
    if insights:
        print(f"\nAnalyzing insight narratives for templates or fallback patterns:")
        
        for i, insight in enumerate(insights[:3]):
            narrative = insight.get('narrative', '')
            # Look for template indicators
            if '**' in narrative or '_' in narrative:
                print(f"\n  Insight {i+1}: {insight.get('feature')}")
                print(f"  Has markdown formatting: Yes")
                print(f"  Sample: {narrative[:100]}")
    
    # =========================================================================
    # 5. EXPORT FULL DEBUG DATA
    # =========================================================================
    
    print(f"\n" + "="*80)
    print("EXPORTING DIAGNOSTIC DATA")
    print("="*80)
    
    export_data = {
        "audit_created": str(latest_audit.created_at),
        "extracted_features_count": len(debug_extraction.get('extracted_features', [])),
        "semantic_features_count": len(ai_summary.get('semantic_features', [])),
        "extracted_features": debug_extraction.get('extracted_features', []),
        "classification_debug": debug_extraction.get('classification', {}),
        "insights": insights[:2],
    }
    
    with open("deep_forensics.json", 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\nExported to: deep_forensics.json")

finally:
    db.close()
