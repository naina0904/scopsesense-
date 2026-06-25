from backend.services.normalization_service import NormalizationService


def test_normalized_timeline_analysis_syncs_feature_names():
    service = NormalizationService()

    audit = {
        "semantic_features": [
            {"feature_name": "invoice generation."},
            {"feature_name": "security updates"},
        ],
        "timeline_analysis": [
            {"feature": "invoice generation.", "status": "pending"},
            {"feature": "security updates", "status": "done"},
            {"feature": "unknown feature", "status": "skipped"},
        ],
    }

    normalized = service.normalize_audit_result(audit)

    assert len(normalized["timeline_analysis"]) == 2
    assert normalized["timeline_analysis"][0]["feature"] == "invoice generation"
    assert normalized["timeline_analysis"][1]["feature"] == "security updates"


def test_derived_collections_preserve_matching_canonical_items():
    service = NormalizationService()

    audit = {
        "semantic_features": [
            {"feature_name": "dependency reasoning."},
            {"feature_name": "notification services"},
        ],
        "feature_ownership": [
            {"feature": "dependency reasoning.", "owner": "alice"},
            {"feature": "notification services", "owner": "bob"},
            {"feature": "action", "owner": "carol"},
        ],
    }

    normalized = service.normalize_audit_result(audit)

    assert len(normalized["feature_ownership"]) == 2
    assert {item["feature"] for item in normalized["feature_ownership"]} == {
        "dependency reasoning",
        "notification services",
    }
