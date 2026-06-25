import logging
from time import perf_counter

from backend.config.settings import settings
from backend.llm.providers import (
    GeminiProvider,
    GroqProvider,
    OllamaProvider
)

logger = logging.getLogger(__name__)

class LLMProviderError(RuntimeError):
    def __init__(self, message, attempts=None):
        super().__init__(message)
        self.attempts = attempts or {}

class LLMManager:
    # Ordered provider preference for failover attempts
    default_provider_order = ["gemini", "groq", "ollama"]

    def __init__(
        self,
        provider: str = "groq"
    ):
        # Instantiate available providers based on feature flags
        self.providers = {}
        if settings.GEMINI_ENABLED:
            self.providers["gemini"] = GeminiProvider()
        if settings.GROQ_ENABLED:
            self.providers["groq"] = GroqProvider()
        if settings.OLLAMA_ENABLED:
            self.providers["ollama"] = OllamaProvider()

        if not self.providers:
            logger.critical("No LLM providers are enabled in settings.")
            raise RuntimeError(
                "No LLM providers are enabled. Set GEMINI_ENABLED, GROQ_ENABLED, or OLLAMA_ENABLED to true."
            )

        self.requested_provider = provider
        self.last_requested_provider = provider

        self.default_provider_order = [
            provider_name for provider_name in self.default_provider_order
            if provider_name in self.providers
        ]

        if provider not in self.providers:
            if self.default_provider_order:
                provider = self.default_provider_order[0]
                logger.warning(f"Requested provider '{self.requested_provider}' is not available. Falling back to default: '{provider}'.")
            else:
                raise ValueError(f"Unsupported provider: {provider}")

        self.provider = provider
        self.last_successful_provider = None
        self.last_attempts = {}
        self.provider_used = None
        self.provider_fallbacks = []
        self.provider_latency_ms = {}

    def get_provider_status(self):
        statuses = {}
        for name in ["gemini", "groq", "ollama"]:
            enabled = getattr(settings, f"{name.upper()}_ENABLED", False)
            configured = bool(
                getattr(settings, f"{name.upper()}_API_KEY", None)
                or getattr(settings, f"{name.upper()}_URL", None)
            )
            statuses[name] = {
                "enabled": enabled,
                "configured": configured,
                "active": self.provider == name,
                "preferred": name in self.default_provider_order
            }
        return statuses

    def generate(self, prompt: str) -> str:
        """
        Try to generate a response using the selected provider.
        On failure, attempt other configured providers in order.
        If all providers fail, raise LLMProviderError with per-provider errors.
        """
        attempts: dict = {}
        self.last_requested_provider = self.provider
        self.last_successful_provider = None
        self.provider_used = None
        self.provider_fallbacks = []
        self.provider_latency_ms = {}

        # Order: try selected provider first, then others
        order = [self.provider] + [p for p in self.default_provider_order if p != self.provider]

        for prov in order:
            provider_impl = self.providers.get(prov)
            if not provider_impl:
                attempts[prov] = "not_available"
                continue

            start = perf_counter()

            try:
                resp = provider_impl.generate(prompt)
                elapsed_ms = int((perf_counter() - start) * 1000)
                self.provider_latency_ms[prov] = elapsed_ms
                self.provider = prov
                self.last_successful_provider = prov
                self.provider_used = prov
                self.provider_fallbacks = [prev for prev in order if prev != prov and prev in attempts]
                self.last_attempts = attempts
                
                if self.provider_fallbacks:
                    logger.info(f"LLM generation successful using fallback provider '{prov}'. Failed providers: {self.provider_fallbacks}")
                else:
                    logger.debug(f"LLM generation successful using '{prov}'. Latency: {elapsed_ms}ms")
                    
                return resp
            except Exception as e:
                elapsed_ms = int((perf_counter() - start) * 1000)
                self.provider_latency_ms[prov] = elapsed_ms
                attempts[prov] = str(e)
                logger.warning(f"LLM provider '{prov}' failed after {elapsed_ms}ms: {e}. Trying next provider.")
                # try next provider
                continue

        # If we reach here, all providers failed
        self.last_attempts = attempts
        self.provider_used = None
        self.provider_fallbacks = order
        logger.error(f"All LLM providers failed to generate a response. Attempts: {attempts}")
        raise LLMProviderError("All LLM providers failed to generate a response.", attempts=attempts)
