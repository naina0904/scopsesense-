from typing import Dict, Any
from backend.integrations.core.unified_schema import Feature


def analyze_root_cause(features: Dict[str, Any]) -> Dict[str, Any]:
    """Very simple placeholder root‑cause analysis.
    
    * Looks for features where variance is high (absolute > 10).
    * Flags missing ``actual_hours`` as a potential data‑gap cause.
    * Returns a JSON‑serialisable dict with ``issues`` list.
    """
    issues = []
    for fid, data in features.items():
        variance = data.get("variance")
        actual = data.get("actual_hours")
        if variance is None:
            continue
        if abs(variance) > 10:
            issues.append({
                "feature_id": fid,
                "type": "high_variance",
                "message": f"Variance of {variance:.1f} hours exceeds threshold.",
            })
        if actual is None:
            issues.append({
                "feature_id": fid,
                "type": "missing_actual",
                "message": "Actual hours not recorded.",
            })
    return {"issues": issues}
