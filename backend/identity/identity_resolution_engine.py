import difflib
import json
from typing import List, Dict, Any, Optional

class IdentityResolutionEngine:
    def __init__(self, manual_aliases: Dict[str, List[str]] = None):
        """
        Initializes the Identity Resolution Engine.
        manual_aliases format: {"Alice Smith": ["S2", "alice-smith99", "alice"]}
        """
        self.manual_aliases = manual_aliases or {}
        # Pre-compute inverted index for faster manual alias lookup
        self._inverted_aliases = {}
        for canonical, aliases in self.manual_aliases.items():
            for alias in aliases:
                self._inverted_aliases[alias.lower()] = canonical

    def _normalize(self, identity: str) -> str:
        if not identity:
            return ""
        return str(identity).strip().lower()

    def _fuzzy_match(self, identity_a: str, identity_b: str) -> float:
        """
        Uses difflib SequenceMatcher to determine the similarity ratio between two identities.
        """
        norm_a = self._normalize(identity_a)
        norm_b = self._normalize(identity_b)
        
        if not norm_a or not norm_b:
            return 0.0

        # Exact match
        if norm_a == norm_b:
            return 1.0

        # Simple substitutions often found in identities (e.g., john.doe vs john_doe)
        a_clean = norm_a.replace(".", "").replace("_", "").replace("-", "")
        b_clean = norm_b.replace(".", "").replace("_", "").replace("-", "")
        if a_clean == b_clean:
            return 0.95 # Almost exact

        # Fuzzy match
        return difflib.SequenceMatcher(None, norm_a, norm_b).ratio()

    def resolve_identities(self, source_identities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolves a list of identity records from different sources into canonical identities.
        
        source_identities expected format:
        [
            {"identity": "S2", "source": "SRS"},
            {"identity": "Alice Smith", "source": "Jira"},
            {"identity": "alice-smith99", "source": "GitHub"}
        ]
        
        Returns a dictionary mapping the original raw identity string to its canonical resolution record.
        """
        resolution_map = {}
        canonical_groups = {} # canonical_name -> {"aliases": set(), "sources": set(), "method": str, "confidence": float}

        # Step 1: Process Manual Aliases (Level 1)
        unresolved = []
        for record in source_identities:
            raw_id = record.get("identity")
            if not raw_id:
                continue
                
            norm_id = self._normalize(raw_id)
            source = record.get("source", "Unknown")
            
            canonical = self._inverted_aliases.get(norm_id)
            if canonical:
                if canonical not in canonical_groups:
                    canonical_groups[canonical] = {
                        "aliases": {canonical},
                        "sources": set(),
                        "method": "manual_alias",
                        "confidence": 1.0
                    }
                canonical_groups[canonical]["aliases"].add(raw_id)
                canonical_groups[canonical]["sources"].add(source)
                
                resolution_map[raw_id] = canonical
            else:
                unresolved.append(record)

        # Step 2: Process Fuzzy Matches (Level 2)
        # For each unresolved, check if it matches an existing canonical group or another unresolved
        for record in unresolved:
            raw_id = record.get("identity")
            source = record.get("source", "Unknown")
            
            best_match_canonical = None
            best_score = 0.0
            
            # Check against existing groups
            for canonical, group_data in canonical_groups.items():
                for alias in group_data["aliases"]:
                    score = self._fuzzy_match(raw_id, alias)
                    if score > best_score:
                        best_score = score
                        best_match_canonical = canonical
                        
            # Check against other unresolved (to form new groups)
            best_unresolved_match = None
            best_unresolved_score = 0.0
            for other in unresolved:
                other_id = other.get("identity")
                if other_id == raw_id:
                    continue
                score = self._fuzzy_match(raw_id, other_id)
                if score > best_unresolved_score:
                    best_unresolved_score = score
                    best_unresolved_match = other_id

            if best_score >= 0.75 and best_score >= best_unresolved_score:
                # Add to existing canonical group
                canonical_groups[best_match_canonical]["aliases"].add(raw_id)
                canonical_groups[best_match_canonical]["sources"].add(source)
                if canonical_groups[best_match_canonical]["method"] != "manual_alias":
                    canonical_groups[best_match_canonical]["method"] = "fuzzy_match"
                    canonical_groups[best_match_canonical]["confidence"] = min(canonical_groups[best_match_canonical]["confidence"], best_score)
                resolution_map[raw_id] = best_match_canonical
                
            elif best_unresolved_score >= 0.75:
                # Form new group (use the longer/more readable one as canonical)
                new_canonical = raw_id if len(raw_id) > len(best_unresolved_match) else best_unresolved_match
                if new_canonical not in canonical_groups:
                    canonical_groups[new_canonical] = {
                        "aliases": {raw_id, best_unresolved_match},
                        "sources": {source},
                        "method": "fuzzy_match",
                        "confidence": best_unresolved_score
                    }
                else:
                    canonical_groups[new_canonical]["aliases"].add(raw_id)
                    canonical_groups[new_canonical]["sources"].add(source)
                resolution_map[raw_id] = new_canonical
                
            else:
                # Exact match or standalone
                canonical_groups[raw_id] = {
                    "aliases": {raw_id},
                    "sources": {source},
                    "method": "exact",
                    "confidence": 1.0
                }
                resolution_map[raw_id] = raw_id

        # Format output
        final_output = {}
        for canonical, data in canonical_groups.items():
            record = {
                "canonical_identity": canonical,
                "aliases": list(data["aliases"]),
                "source_systems": list(data["sources"]),
                "resolution_method": data["method"],
                "confidence": data["confidence"]
            }
            # Map every alias to this complete record
            for alias in data["aliases"]:
                final_output[alias] = record

        return final_output

    def are_same_person(self, identity_a: str, identity_b: str, identity_map: Dict[str, Any]) -> bool:
        """
        Given the identity_map produced by resolve_identities, check if a and b resolve to the same person.
        Also performs a fallback fuzzy match if they aren't in the map but are very similar.
        """
        # Exact string match shortcut
        if self._normalize(identity_a) == self._normalize(identity_b):
            return True
            
        record_a = identity_map.get(identity_a)
        record_b = identity_map.get(identity_b)
        
        if record_a and record_b and record_a["canonical_identity"] == record_b["canonical_identity"]:
            return True
            
        # Fallback to direct fuzzy match if not in map
        if self._fuzzy_match(identity_a, identity_b) >= 0.75:
            return True
            
        return False

    def explain_resolution(self, identity_a: str, identity_b: str, identity_map: Dict[str, Any]) -> str:
        """
        Generates the explainability lineage for the resolution.
        """
        if self.are_same_person(identity_a, identity_b, identity_map):
            record = identity_map.get(identity_a) or identity_map.get(identity_b)
            if record:
                method = record["resolution_method"]
                sources = record["source_systems"]
                aliases = record["aliases"]
                
                # Format explanation as requested
                # Example:
                # S2 (SRS)
                # ↓
                # Alice Smith (Jira)
                # ...
                
                # We don't have per-alias source mapping easily accessible here without expanding the model,
                # but we can provide a simplified lineage showing they belong to the same canonical group.
                if method == "manual_alias":
                    method_str = "Manual Alias Mapping"
                elif method == "fuzzy_match":
                    method_str = f"Fuzzy Resolution (Confidence: {record['confidence']:.2f})"
                else:
                    method_str = "Exact Match"
                    
                explanation = f"Ghost Authorship Suppressed.\n\nReason:\n{identity_a}\n↓\n{identity_b}\n\nresolved using {method_str}."
                return explanation
                
        return ""
