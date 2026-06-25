from typing import List, Dict

from backend.integrations.core.unified_schema import Feature
from backend.models.calendar_profile import CalendarProfile
from backend.services.effort_normalizer import EffortNormalizer
from backend.models.module_match import ModuleMatch


def compute_variance(
    features: List[Feature],
    calendar_profile: CalendarProfile,
    module_matches: List[ModuleMatch]
) -> Dict[str, float]:
    """Calculate variance between planned and actual effort for each feature.

    The function only includes features whose corresponding ``ModuleMatch`` has
    been approved (``approved=True``). Effort values are normalized to hours
    using the provided ``CalendarProfile`` via the ``EffortNormalizer`` service.
    It prefers ``aggregated_actual_hours`` (computed by ``hours_aggregator``) when
    present; otherwise it falls back to ``actual_hours``.
    """

    # Build a set of feature IDs that have an approved match.
    approved_feature_ids = {match.feature_id for match in module_matches if getattr(match, "approval_status", None) in {"APPROVED", "AUTO_APPROVED"}}

    normalizer = EffortNormalizer(calendar_profile)
    variance_map: Dict[str, float] = {}
    for f in features:
        # Skip features without an approved match.
        if f.id not in approved_feature_ids:
            continue
        # Planned effort – use estimated_hours if present, else 0.
        planned_raw = getattr(f, "estimated_hours", 0.0) or 0.0
        planned = normalizer.normalize(planned_raw, "hours")
        # Actual effort – use aggregated if available, else actual_hours.
        actual_raw = getattr(f, "aggregated_actual_hours", None)
        if actual_raw is None:
            actual_raw = getattr(f, "actual_hours", 0.0) or 0.0
        actual = normalizer.normalize(actual_raw, "hours")
        variance_map[f.id] = planned - actual
    return variance_map
