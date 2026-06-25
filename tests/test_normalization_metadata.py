from backend.services.normalization_service import NormalizationService
from backend.services.audit_service import AuditService


def test_normalization_metadata_is_added_to_response():
    service = NormalizationService()

    audit = {
        "semantic_features": [
            {"feature_name": "invoice generation."},
            {"feature_name": "invoice generation"},
        ]
    }

    normalized = service.normalize_audit_result(audit)

    assert normalized["_normalization_applied"] is True
    assert normalized["_normalization_applied_at_response"] is True
    assert normalized["_normalization_config_version"] == "1.0"
    assert normalized["_normalized_feature_count"] == len(normalized["semantic_features"])


def test_persisted_audit_contains_raw_feature_copy():
    result = {
        "semantic_features": [
            {"feature_name": "notification services"},
        ]
    }
    audit_service = AuditService()
    sanitized = audit_service._sanitize_persisted_audit(result)

    assert sanitized["_raw_semantic_features"] == result["semantic_features"]
    assert sanitized["_raw_feature_count"] == 1
    assert sanitized["_normalization_applied_at_response"] is False
