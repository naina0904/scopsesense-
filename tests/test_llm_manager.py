from backend.config.settings import settings
from backend.llm import manager


class FakeProvider:

    def __init__(self, name):
        self.name = name

    def generate(self, prompt):
        if self.name == "groq" and prompt == "fail":
            raise RuntimeError("groq failed")
        return f"{self.name}:{prompt}"


def test_llm_manager_respects_provider_feature_flags(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_ENABLED", True)
    monkeypatch.setattr(settings, "GROQ_ENABLED", False)
    monkeypatch.setattr(settings, "OLLAMA_ENABLED", False)

    monkeypatch.setattr(manager, "GeminiProvider", lambda: FakeProvider("gemini"))
    monkeypatch.setattr(manager, "GroqProvider", lambda: FakeProvider("groq"))
    monkeypatch.setattr(manager, "OllamaProvider", lambda: FakeProvider("ollama"))

    llm = manager.LLMManager("gemini")

    assert set(llm.providers.keys()) == {"gemini"}
    assert llm.provider == "gemini"


def test_llm_manager_falls_back_to_enabled_provider_when_default_disabled(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_ENABLED", True)
    monkeypatch.setattr(settings, "GROQ_ENABLED", False)
    monkeypatch.setattr(settings, "OLLAMA_ENABLED", False)

    monkeypatch.setattr(manager, "GeminiProvider", lambda: FakeProvider("gemini"))
    monkeypatch.setattr(manager, "GroqProvider", lambda: FakeProvider("groq"))
    monkeypatch.setattr(manager, "OllamaProvider", lambda: FakeProvider("ollama"))

    llm = manager.LLMManager("groq")

    assert llm.provider == "gemini"
    assert llm.default_provider_order == ["gemini"]


def test_llm_manager_generates_using_failover_order(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_ENABLED", True)
    monkeypatch.setattr(settings, "GROQ_ENABLED", True)
    monkeypatch.setattr(settings, "OLLAMA_ENABLED", True)

    monkeypatch.setattr(manager, "GeminiProvider", lambda: FakeProvider("gemini"))
    monkeypatch.setattr(manager, "GroqProvider", lambda: FakeProvider("groq"))
    monkeypatch.setattr(manager, "OllamaProvider", lambda: FakeProvider("ollama"))

    llm = manager.LLMManager("groq")
    result = llm.generate("fail")

    assert result == "gemini:fail"
    assert llm.last_successful_provider == "gemini"
    assert llm.last_attempts["groq"] == "groq failed"
