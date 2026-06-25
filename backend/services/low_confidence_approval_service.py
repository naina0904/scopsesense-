from typing import List, Dict
from backend.models.module_match import ModuleMatch
from backend.models.calendar_profile import CalendarProfile
from backend.services.effort_normalizer import EffortNormalizer
from backend.services.module_match_service import ModuleMatchService

def process_module_matches(matches: List[Dict[str, any]], threshold: float = 0.7) -> Dict[str, List[ModuleMatch]]:
    """Process raw matcher output, persist ModuleMatch records, and flag low‑confidence items.

    Returns a dict with keys:
    * ``approved`` – matches with confidence >= threshold (auto‑approved).
    * ``pending`` – low‑confidence matches awaiting manager approval.
    """
    approved: List[ModuleMatch] = []
    pending: List[ModuleMatch] = []
    for match in matches:
        srs_id = match.get("srs_node_id")
        feature_ids = match.get("matched_feature_ids", [])
        confidences = match.get("confidence_scores", [])
        for fid, conf in zip(feature_ids, confidences):
            mm = ModuleMatch(
                id=f"{srs_id}:{fid}",
                srs_node_id=srs_id,
                feature_id=fid,
                matched_type="feature",
                confidence_score=conf,
                approval_status="AUTO_APPROVED" if conf >= threshold else "PENDING_REVIEW",
                approval_timestamp=datetime.utcnow() if conf >= threshold else None,
                metadata={"matched_documents": match.get("matched_documents", [])},
            )
            # Persist the match using the service layer
            ModuleMatchService.save(mm)
            if mm.approval_status == "AUTO_APPROVED":
                approved.append(mm)
            else:
                pending.append(mm)
    return {"approved": approved, "pending": pending}

def get_pending_matches() -> List[ModuleMatch]:
    """Retrieve all pending low‑confidence matches awaiting approval via the service layer."""
    return ModuleMatchService.get_pending()

def approve_match(match_id: int) -> bool:
    """Mark a pending match as approved using the service layer. Returns ``True`` if successful."""
    return ModuleMatchService.approve(match_id)
