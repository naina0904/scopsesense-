from fastapi.testclient import TestClient

from backend.api.routes import router
from backend.config.settings import settings
from backend.llm import manager
from backend.srs.extractor import SRSFeatureExtractor


class FakeProvider:
    def __init__(self, name, should_fail=False):
        self.name = name
        self.should_fail = should_fail

    def generate(self, prompt):
        if self.should_fail:
            raise RuntimeError(f"{self.name} failed")
        return f"{self.name}:success"


def test_health_providers_route():
    app = TestClient(__import__("backend.main", fromlist=["app"]).app)
    response = app.get("/health/providers")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "providers" in data
    assert set(data["providers"].keys()) >= {"gemini", "groq", "ollama", "heuristic"}


def test_llm_manager_gemini_success(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_ENABLED", True)
    monkeypatch.setattr(settings, "GROQ_ENABLED", True)
    monkeypatch.setattr(settings, "OLLAMA_ENABLED", True)

    monkeypatch.setattr(manager, "GeminiProvider", lambda: FakeProvider("gemini"))
    monkeypatch.setattr(manager, "GroqProvider", lambda: FakeProvider("groq", should_fail=True))
    monkeypatch.setattr(manager, "OllamaProvider", lambda: FakeProvider("ollama", should_fail=True))

    llm = manager.LLMManager(provider="gemini")
    result = llm.generate("test")

    assert result == "gemini:success"
    assert llm.provider_used == "gemini"
    assert llm.provider_fallbacks == []
    assert llm.provider_latency_ms["gemini"] >= 0


def test_llm_manager_gemini_to_groq(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_ENABLED", True)
    monkeypatch.setattr(settings, "GROQ_ENABLED", True)
    monkeypatch.setattr(settings, "OLLAMA_ENABLED", False)

    monkeypatch.setattr(manager, "GeminiProvider", lambda: FakeProvider("gemini", should_fail=True))
    monkeypatch.setattr(manager, "GroqProvider", lambda: FakeProvider("groq"))
    monkeypatch.setattr(manager, "OllamaProvider", lambda: FakeProvider("ollama"))

    llm = manager.LLMManager(provider="gemini")
    result = llm.generate("test")

    assert result == "groq:success"
    assert llm.provider_used == "groq"
    assert llm.provider_fallbacks == ["gemini"]
    assert llm.last_attempts["gemini"] == "gemini failed"


def test_llm_manager_gemini_groq_ollama(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_ENABLED", True)
    monkeypatch.setattr(settings, "GROQ_ENABLED", True)
    monkeypatch.setattr(settings, "OLLAMA_ENABLED", True)

    monkeypatch.setattr(manager, "GeminiProvider", lambda: FakeProvider("gemini", should_fail=True))
    monkeypatch.setattr(manager, "GroqProvider", lambda: FakeProvider("groq", should_fail=True))
    monkeypatch.setattr(manager, "OllamaProvider", lambda: FakeProvider("ollama"))

    llm = manager.LLMManager(provider="gemini")
    result = llm.generate("test")

    assert result == "ollama:success"
    assert llm.provider_used == "ollama"
    assert llm.provider_fallbacks == ["gemini", "groq"]
    assert llm.last_attempts["gemini"] == "gemini failed"
    assert llm.last_attempts["groq"] == "groq failed"


def test_srs_feature_extractor_full_fallback_to_heuristic(monkeypatch):
    # Provide content without explicit Feature markers so the heuristic fallback is required.
    sample_content = """
# Features

The platform includes user management, billing, and reporting services.
"""

    fake_llm_manager = type("FakeLLMManager", (), {
        "provider": "gemini",
        "generate": lambda self, prompt: (_ for _ in ()).throw(RuntimeError("all providers failed")),
        "last_successful_provider": None,
        "provider_used": None,
        "provider_fallbacks": ["gemini", "groq", "ollama"],
        "provider_latency_ms": {}
    })()

    extractor = SRSFeatureExtractor(llm_manager=fake_llm_manager)
    features = extractor.extract_features(sample_content)

    assert isinstance(features, list)
    assert features, "Expected heuristic fallback to extract features"
    assert extractor.debug_info["fallback_extraction_used"] is True
    assert extractor.debug_info["provider_used"] is None
    assert extractor.debug_info["provider_fallbacks"] == ["gemini", "groq", "ollama"]
