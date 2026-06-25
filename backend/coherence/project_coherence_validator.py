import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ProjectCoherenceValidator:
    """
    Project Coherence Validator
    Detects whether the uploaded SRS and connected Jira/GitHub sources 
    appear to represent the same project by comparing text overlap.
    """

    def __init__(self):
        # We can use basic Jaccard similarity for fast text comparison before embedding matching.
        pass

    def validate(self, extracted_features: List[Dict[str, Any]], platform_data: Any) -> Dict[str, Any]:
        """
        Validate coherence between SRS features and implementation data.
        """
        if not extracted_features or not platform_data:
            return self._build_result(1.0) # Assume OK if missing data, do not alarm unnecessarily
        
        # 1. Extract SRS Terms
        srs_terms = set()
        for f in extracted_features:
            srs_terms.update(self._tokenize(f.get("feature_name", "")))
            srs_terms.update(self._tokenize(f.get("description", "")))
            srs_terms.update(self._tokenize(f.get("milestone", "")))
            
        if not srs_terms:
            return self._build_result(1.0)
            
        # 2. Extract Platform Terms
        platform_terms = set()
        
        # Extract from features (Issues, PRs, etc.)
        features = getattr(platform_data, "features", [])
        for feature in features:
            platform_terms.update(self._tokenize(getattr(feature, "name", "")))
            platform_terms.update(self._tokenize(getattr(feature, "description", "")))
            
        # Extract from timeline events (Commits)
        events = getattr(platform_data, "timeline_events", [])
        for event in events:
            platform_terms.update(self._tokenize(getattr(event, "description", "")))
            
        if not platform_terms:
            return self._build_result(0.5) # Medium risk if platform has no text data at all
            
        # 3. Compute Jaccard Similarity / Overlap Score
        # We look at what percentage of significant SRS terms appear in the platform data
        # Because SRS terms might be very specific, a 20-30% overlap of non-stop-words is usually sufficient for coherence.
        intersection = srs_terms.intersection(platform_terms)
        
        if len(srs_terms) == 0:
            overlap_ratio = 1.0
        else:
            overlap_ratio = len(intersection) / len(srs_terms)
            
        # Normalise score: An overlap of 0.3 (30%) is considered extremely high coherence (score 1.0)
        # An overlap of 0.05 is low.
        normalized_score = min(1.0, overlap_ratio * 3.0)
        
        logger.info(f"[CoherenceValidator] SRS terms: {len(srs_terms)}, Platform terms: {len(platform_terms)}, Overlap: {len(intersection)}, Raw Ratio: {overlap_ratio:.3f}, Score: {normalized_score:.2f}")

        return self._build_result(normalized_score)

    def _tokenize(self, text: str) -> set:
        """Simple tokenizer to extract meaningful lowercase words > 3 chars."""
        if not text or not isinstance(text, str):
            return set()
        
        # Remove common stop words for better signal
        stop_words = {
            "this", "that", "with", "from", "your", "have", "more", "will", "would", 
            "should", "could", "been", "which", "their", "there", "what", "when", 
            "where", "user", "system", "data", "can", "the", "and", "for", "are", "but", "not", "how"
        }
        
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        return set(w for w in words if w not in stop_words)

    def _build_result(self, score: float) -> Dict[str, Any]:
        """Construct the result payload based on score."""
        score = round(score, 2)
        
        if score < 0.40:
            risk_level = "HIGH"
            warning = "Connected implementation sources may not correspond to the uploaded SRS."
        elif score < 0.70:
            risk_level = "MEDIUM"
            warning = "Connected implementation sources show moderate terminology divergence from the uploaded SRS."
        else:
            risk_level = "LOW"
            warning = None
            
        result = {
            "coherence_score": score,
            "risk_level": risk_level,
        }
        
        if warning:
            result["warning"] = warning
            
        return result
