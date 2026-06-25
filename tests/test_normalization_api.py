import inspect
import json

from backend.api import routes


class FakeQuery:
    def __init__(self, audit):
        self.audit = audit

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.audit


class FakeDB:
    def __init__(self, audit):
        self.audit = audit

    def query(self, *args, **kwargs):
        return FakeQuery(self.audit)

    def close(self):
        return None


class FakeAudit:
    def __init__(self, ai_summary):
        self.ai_summary = ai_summary
        self.project_name = "owner/repo"
        self.id = 123


def test_latest_audit_accepts_normalize_parameter():
    signature = inspect.signature(routes.latest_audit)
    assert "normalize" in signature.parameters
    assert signature.parameters["normalize"].default is False


def test_latest_audit_payload_returns_raw_when_normalize_false(monkeypatch):
    raw_payload = {
        "semantic_features": [{"feature_name": "invoice generation"}],
        "_raw_semantic_features": [{"feature_name": "invoice generation"}],
    }
    fake_audit = FakeAudit(json.dumps(raw_payload))
    monkeypatch.setattr(routes, "SessionLocal", lambda: FakeDB(fake_audit))

    result = routes._latest_audit_payload(owner="owner", repo="repo", normalize=False)

    assert result["_normalization_applied"] is False
    assert result["semantic_features"] == raw_payload["semantic_features"]


def test_latest_audit_payload_applies_normalization_when_true(monkeypatch):
    raw_payload = {
        "semantic_features": [
            {"feature_name": "invoice generation."},
            {"feature_name": "invoice generation"},
        ],
        "_raw_semantic_features": [
            {"feature_name": "invoice generation."},
            {"feature_name": "invoice generation"},
        ],
    }
    fake_audit = FakeAudit(json.dumps(raw_payload))
    monkeypatch.setattr(routes, "SessionLocal", lambda: FakeDB(fake_audit))

    result = routes._latest_audit_payload(owner="owner", repo="repo", normalize=True)

    assert result["_normalization_applied"] is True
    normalized_names = [f["feature_name"] for f in result["semantic_features"]]
    assert normalized_names.count("invoice generation") == 1
