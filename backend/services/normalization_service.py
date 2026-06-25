"""
Normalization Service

Purpose: Encapsulate all normalization logic for semantic features.
- Preserves raw features in storage
- Applies normalization dynamically at API response time
- Supports multiple normalization versions via config_version parameter

Date: 2026-06-02
Author: Implementation Phase 3B
"""

import copy
from typing import Any, Dict, List, Set, Optional


class NormalizationConfig:
    """
    Static configuration for normalization rules.
    All values derived from Phase 3A analysis of audit #31.
    """

    # Exact duplicate feature groups to consolidate.
    # Variants in the same group should collapse to a single canonical feature name.
    DEDUP_GROUPS = {
        "invoice generation": [
            "invoice generation",
            "invoice generation.",
        ],
        "quick actions": [
            "quick actions",
            "quick actions.",
        ],
        "dependency reasoning": [
            "dependency reasoning",
            "dependency reasoning.",
        ],
        "AI-driven engineering governance workflows": [
            "AI-driven engineering governance workflows",
            "AI-driven engineering governance workflows.",
        ],
    }

    # Noise items to exclude when normalize=true.
    # These are the 15 identified noise items from audit #31.
    FRAGMENT_EXCLUSIONS = [
        "failed-attempt handling",
        "retry handling",
        "administrative changes",
        "important business events. Target: Critical user",
        "localization",
        "defaults",
    ]

    UI_VERB_EXCLUSIONS = [
        "customize",
        "edit",
        "filter",
        "preview",
        "action",
    ]

    # Raw names to normalized canonical names.
    # This mapping preserves each distinct feature while normalizing punctuation
    # and minor variant differences.
    CANONICAL_MAPPINGS = {
        "invoice generation.": "invoice generation",
        "quick actions.": "quick actions",
        "dependency reasoning.": "dependency reasoning",
        "AI-driven engineering governance workflows.": "AI-driven engineering governance workflows",
        "admin actions.": "admin actions",
        "system preferences.": "system preferences",
        "export operational reports.": "export operational reports",
        "secure password reset workflow interface.": "secure password reset workflow interface",
    }

    VERSION = "1.0"


class NormalizationService:
    """
    Service to normalize semantic features at API response time.

    Design: Preserve raw in storage, normalize on-the-fly at API response.
    """

    def __init__(self):
        self.config = NormalizationConfig()
        self._canonical_group_cache: Optional[Set[str]] = None

    def normalize_audit_result(
        self, audit_result: Dict[str, Any], config_version: str = "1.0"
    ) -> Dict[str, Any]:
        """
        Main entry point. Normalizes an entire audit result.
        """
        normalized = copy.deepcopy(audit_result)

        raw_features = normalized.get("semantic_features", [])
        normalized_features = self.normalize_semantic_features(raw_features)
        normalized["semantic_features"] = normalized_features

        canonical_feature_names = {
            f.get("feature_name") for f in normalized_features if "feature_name" in f
        }

        if "timeline_analysis" in normalized:
            normalized["timeline_analysis"] = self._sync_collection(
                normalized["timeline_analysis"],
                canonical_feature_names,
                key_field="feature",
            )

        if "feature_ownership" in normalized:
            normalized["feature_ownership"] = self._sync_collection(
                normalized["feature_ownership"],
                canonical_feature_names,
                key_field="feature",
            )

        if "insights" in normalized:
            normalized["insights"] = self._sync_collection(
                normalized["insights"],
                canonical_feature_names,
                key_field="feature",
            )

        if "hotspots" in normalized:
            normalized["hotspots"] = self._sync_collection(
                normalized["hotspots"],
                canonical_feature_names,
                key_field="feature",
            )

        normalized["_normalization_config_version"] = config_version
        normalized["_normalization_applied"] = True
        normalized["_normalization_applied_at_response"] = True
        normalized["_normalized_feature_count"] = len(normalized_features)
        normalized["_canonical_feature_groups"] = len(self._get_canonical_groups())

        return normalized

    def normalize_semantic_features(self, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply normalization rules to semantic features.
        """
        deduplicated = self._consolidate_duplicates(features)
        filtered = self._filter_noise(deduplicated)
        canonical = self._canonicalize_feature_names(filtered)
        return canonical

    def _consolidate_duplicates(self, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Collapse exact duplicate feature variants into a single canonical item.
        """
        seen_groups: Dict[str, Dict[str, Any]] = {}
        deduplicated: List[Dict[str, Any]] = []

        variant_to_group: Dict[str, str] = {}
        for group_name, variants in self.config.DEDUP_GROUPS.items():
            for variant in variants:
                variant_to_group[variant] = group_name

        for feature in features:
            feature_name = feature.get("feature_name", "").strip()
            if not feature_name:
                continue

            if feature_name in variant_to_group:
                canonical_name = variant_to_group[feature_name]
                if canonical_name not in seen_groups:
                    merged_feature = copy.deepcopy(feature)
                    merged_feature["feature_name"] = canonical_name
                    merged_feature["_original_variants"] = [feature_name]
                    seen_groups[canonical_name] = merged_feature
                else:
                    existing = seen_groups[canonical_name]
                    existing.setdefault("_original_variants", []).append(feature_name)
            else:
                deduplicated.append(feature)

        deduplicated.extend(seen_groups.values())
        return deduplicated

    def _filter_noise(self, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out the known noise items only in normalized mode.
        """
        fragment_exclusions = {name.lower() for name in self.config.FRAGMENT_EXCLUSIONS}
        verb_exclusions = {name.lower() for name in self.config.UI_VERB_EXCLUSIONS}

        filtered: List[Dict[str, Any]] = []
        for feature in features:
            feature_name = feature.get("feature_name", "").strip()
            if not feature_name:
                continue

            lower_name = feature_name.lower()
            if lower_name in fragment_exclusions:
                continue
            if lower_name in verb_exclusions:
                continue

            filtered.append(feature)

        return filtered

    def _canonicalize_feature_names(self, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply canonical name normalization to each feature while preserving count.
        """
        canonical_features: List[Dict[str, Any]] = []
        seen: Dict[str, Dict[str, Any]] = {}

        for feature in features:
            feature_name = feature.get("feature_name", "").strip()
            if not feature_name:
                continue

            canonical_name = self._canonical_feature_name(feature_name)
            if canonical_name in seen:
                existing = seen[canonical_name]
                existing.setdefault("_original_variants", []).append(feature_name)
                continue

            normalized_feature = copy.deepcopy(feature)
            normalized_feature["feature_name"] = canonical_name
            normalized_feature["_original_variants"] = [feature_name]
            canonical_features.append(normalized_feature)
            seen[canonical_name] = normalized_feature

        return canonical_features

    def _canonical_feature_name(self, feature_name: str) -> str:
        """Return the normalized canonical feature name for a raw feature name."""
        return self.config.CANONICAL_MAPPINGS.get(feature_name, feature_name)

    def _sync_collection(
        self,
        collection: List[Dict[str, Any]],
        canonical_feature_names: Set[str],
        key_field: str = "feature",
    ) -> List[Dict[str, Any]]:
        """
        Sync derived collection to the normalized feature set.
        """
        synced: List[Dict[str, Any]] = []
        for item in collection:
            if not isinstance(item, dict):
                continue

            feature_key = item.get(key_field, "").strip()
            canonical_feature = self._canonical_feature_name(feature_key)
            if canonical_feature in canonical_feature_names:
                item[key_field] = canonical_feature
                synced.append(item)

        return synced

    def _get_canonical_groups(self) -> Set[str]:
        if self._canonical_group_cache is None:
            self._canonical_group_cache = set(self.config.CANONICAL_MAPPINGS.values())
        return self._canonical_group_cache
