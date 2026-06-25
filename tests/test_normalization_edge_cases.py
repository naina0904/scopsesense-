from backend.services.normalization_service import NormalizationService


def test_empty_semantic_features_normalizes_to_empty_list():
    service = NormalizationService()

    normalized = service.normalize_audit_result({
        "semantic_features": [],
        "timeline_analysis": [],
        "feature_ownership": [],
        "insights": [],
        "hotspots": [],
    })

    assert normalized["semantic_features"] == []
    assert normalized["timeline_analysis"] == []
    assert normalized["feature_ownership"] == []
    assert normalized["insights"] == []
    assert normalized["hotspots"] == []
    assert normalized["_normalized_feature_count"] == 0


def test_all_noise_features_are_filtered_out():
    service = NormalizationService()

    normalized = service.normalize_semantic_features([
        {"feature_name": "customize"},
        {"feature_name": "edit"},
        {"feature_name": "filter"},
        {"feature_name": "preview"},
        {"feature_name": "action"},
        {"feature_name": "failed-attempt handling"},
        {"feature_name": "retry handling"},
        {"feature_name": "administrative changes"},
        {"feature_name": "important business events. Target: Critical user"},
        {"feature_name": "localization"},
        {"feature_name": "defaults"},
    ])

    assert normalized == []
