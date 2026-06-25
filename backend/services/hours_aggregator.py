from typing import List, Dict
from backend.integrations.core.unified_schema import Feature

def aggregate_hours(features: List[Feature]) -> Dict[str, float]:
    """Aggregate actual_hours across the Jira hierarchy.

    Returns a mapping from feature ID (typically a module/epic) to the total
    actual hours of that feature and all its descendant features.
    """
    # Build lookup dict
    feature_dict: Dict[str, Feature] = {f.id: f for f in features}
    # Initialize aggregation dict
    aggregated: Dict[str, float] = {f.id: 0.0 for f in features}

    # Helper to recursively sum hours
    def _sum_hours(feature_id: str) -> float:
        feature = feature_dict.get(feature_id)
        if not feature:
            return 0.0
        # Start with its own actual hours if present
        total = feature.actual_hours or 0.0
        # Add hours of children
        for child in features:
            if child.parent_id == feature_id:
                total += _sum_hours(child.id)
        return total

    for fid in feature_dict:
        aggregated[fid] = _sum_hours(fid)
        # Also store back into the Feature for convenience
        feature_dict[fid].aggregated_actual_hours = aggregated[fid]

    return aggregated
