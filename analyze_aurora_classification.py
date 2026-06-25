#!/usr/bin/env python3
"""Analyze Aurora audit classification metrics."""

import json
from collections import defaultdict
from pathlib import Path

def analyze_classification():
    audit_path = Path("backend/memory/storage/local_aurora-engineering-platform.json")
    
    with open(audit_path, 'r') as f:
        audit_list = json.load(f)
    
    # Get the latest audit record
    if isinstance(audit_list, list):
        audit_record = audit_list[-1]  # Latest record
        audit = audit_record.get("data", {})
    else:
        audit = audit_list
    
    # Extract classification metrics
    debug_extraction = audit.get("debug_extraction", {})
    classification = debug_extraction.get("classification", {})
    
    if not classification:
        print("❌ No classification metrics found in audit")
        return
    
    category_counts = classification.get("category_counts", {})
    kept_count = classification.get("kept_count", 0)
    filtered_count = classification.get("filtered_count", 0)
    sample_classifications = classification.get("sample_classifications", [])
    
    semantic_features = audit.get("semantic_features", [])
    total_features = len(semantic_features)
    
    # Calculate metrics
    total_categories = sum(category_counts.values())
    precision = kept_count / total_features if total_features > 0 else 0
    
    print("\n" + "="*80)
    print("AURORA AUDIT - CLASSIFICATION ANALYSIS")
    print("="*80)
    
    # 1. Category Counts
    print("\n1. CATEGORY COUNTS")
    print("-" * 80)
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {category:35s}: {count:5d}")
    print(f"   {'TOTAL':35s}: {total_categories:5d}")
    
    # 2. Category Percentages
    print("\n2. CATEGORY PERCENTAGES")
    print("-" * 80)
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_categories * 100) if total_categories > 0 else 0
        bar_length = int(pct / 2)
        bar = "█" * bar_length
        print(f"   {category:35s}: {pct:6.2f}% {bar}")
    
    # 3. Extraction Metrics
    print("\n3. EXTRACTION METRICS")
    print("-" * 80)
    print(f"   Total Semantic Features      : {total_features:d}")
    print(f"   Kept Count (SOFTWARE_FEATURE): {kept_count:d}")
    print(f"   Filtered Count               : {filtered_count:d}")
    print(f"   Extraction Precision         : {precision:.4f} ({precision*100:.2f}%)")
    
    # 4. Sample Classifications by Category
    print("\n4. SAMPLE CLASSIFICATIONS (by category)")
    print("-" * 80)
    
    # Group by category
    by_category = defaultdict(list)
    for sample in sample_classifications:
        category = sample.get("category", "UNKNOWN")
        by_category[category].append(sample)
    
    for category in sorted(by_category.keys()):
        samples = by_category[category]
        print(f"\n   {category} ({len(samples)} total)")
        print(f"   {'-' * 76}")
        
        # Show up to 20 examples
        for i, sample in enumerate(samples[:20], 1):
            feature_name = sample.get("feature_name", "N/A")
            confidence = sample.get("confidence", 0)
            reasoning = sample.get("reasoning", "")[:60]
            print(f"      {i:2d}. [{confidence:.2f}] {feature_name}")
            if reasoning:
                print(f"          → {reasoning}...")
    
    # Statistics
    print("\n5. SAMPLE STATISTICS")
    print("-" * 80)
    print(f"   Total samples analyzed       : {len(sample_classifications)}")
    for category in sorted(by_category.keys()):
        print(f"   {category:35s}: {len(by_category[category]):5d}")
    
    print("\n" + "="*80)
    print(f"Audit File: {audit_path}")
    print("="*80 + "\n")

if __name__ == "__main__":
    analyze_classification()
