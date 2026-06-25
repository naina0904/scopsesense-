from backend.services.normalization_service import NormalizationService


def test_normalization_service_removes_noise_and_deduplicates():
    service = NormalizationService()

    raw_features = [
        {"feature_name": "invoice generation"},
        {"feature_name": "invoice generation."},
        {"feature_name": "dependency reasoning."},
        {"feature_name": "dependency reasoning"},
        {"feature_name": "quick actions"},
        {"feature_name": "quick actions."},
        {"feature_name": "failed-attempt handling"},
        {"feature_name": "customize"},
        {"feature_name": "edit"},
        {"feature_name": "filter"},
        {"feature_name": "preview"},
        {"feature_name": "action"},
        {"feature_name": "localization"},
        {"feature_name": "defaults"},
        {"feature_name": "notification services"},
    ]

    normalized = service.normalize_semantic_features(raw_features)

    normalized_names = [f["feature_name"] for f in normalized]

    assert "invoice generation" in normalized_names
    assert "dependency reasoning" in normalized_names
    assert "quick actions" in normalized_names
    assert "failed-attempt handling" not in normalized_names
    assert "customize" not in normalized_names
    assert "localization" not in normalized_names
    assert "defaults" not in normalized_names
    assert normalized_names.count("invoice generation") == 1
    assert normalized_names.count("dependency reasoning") == 1
    assert normalized_names.count("quick actions") == 1


def test_normalization_service_preserves_canonical_name_variants():
    service = NormalizationService()

    raw_features = [
        {"feature_name": "admin actions."},
        {"feature_name": "secure password reset workflow interface."},
    ]

    normalized = service.normalize_semantic_features(raw_features)
    normalized_names = [f["feature_name"] for f in normalized]

    assert "admin actions" in normalized_names
    assert "secure password reset workflow interface" in normalized_names
