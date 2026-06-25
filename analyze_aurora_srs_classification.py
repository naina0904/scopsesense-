#!/usr/bin/env python3
"""Analyze Aurora SRS classification metrics directly."""

import json
from collections import defaultdict
from pathlib import Path
from backend.srs.extractor import SRSFeatureExtractor


def analyze_aurora_srs():
    """Extract and analyze Aurora SRS features with classification metrics."""
    
    # Read SRS file
    srs_path = Path("aurora_srs.txt")
    with open(srs_path, 'r') as f:
        content = f.read()
    
    # Create extractor
    extractor = SRSFeatureExtractor()
    
    # Extract features
    features = extractor.extract_features(content)
    
    # Get classification metrics
    debug_info = extractor.debug_info
    classification = debug_info.get("classification", {})
    
    if not classification:
        print("❌ No classification metrics found")
        return
    
    category_counts = classification.get("category_counts", {})
    kept_count = classification.get("kept_count", 0)
    filtered_count = classification.get("filtered_count", 0)
    sample_classifications = classification.get("sample_classifications", [])
    
    total_features = len(features)
    total_categories = sum(category_counts.values())
    precision = kept_count / total_features if total_features > 0 else 0
    
    print("\n" + "="*80)
    print("AURORA SRS - CLASSIFICATION ANALYSIS")
    print("="*80)
    
    # 1. Category Counts
    print("\n1. CATEGORY COUNTS")
    print("-" * 80)
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {category:35s}: {count:5d}")
    print(f"   {'TOTAL':35s}: {total_categories:5d}")
    
    # 2. Category Percentages
    print("\n2. CATEGORY PERCENTAGES (%)")
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
    print("\n4. SAMPLE CLASSIFICATIONS BY CATEGORY (up to 20 per category)")
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
            reasoning = sample.get("reasoning", "")[:55]
            print(f"      {i:2d}. [{confidence:.2f}] {feature_name}")
            if reasoning:
                print(f"          → {reasoning}...")
    
    # Statistics
    print("\n5. SAMPLE STATISTICS")
    print("-" * 80)
    print(f"   Total samples analyzed       : {len(sample_classifications)}")
    for category in sorted(by_category.keys()):
        pct = len(by_category[category]) / len(sample_classifications) * 100
        print(f"   {category:35s}: {len(by_category[category]):5d} ({pct:5.1f}%)")
    
    print("\n" + "="*80)
    print(f"Extraction File: {srs_path}")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        analyze_aurora_srs()
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
