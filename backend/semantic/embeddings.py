from sentence_transformers import (
    SentenceTransformer
)
import functools
from backend.observability.structured_logger import get_logger

logger = get_logger(__name__)

# =================================================
# SINGLETON MODEL INSTANCE
# =================================================
# The SentenceTransformer model is loaded once per
# worker process at first use. All subsequent
# EmbeddingEngine instances reuse the same model
# object, eliminating repeated HuggingFace network
# checks and model-load overhead per audit task.

_model_instance: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:

    global _model_instance

    if _model_instance is None:
        logger.info("loading_sentence_transformer_model", cache_folder="/app/data/hf_cache")

        _model_instance = SentenceTransformer(
            "all-MiniLM-L6-v2",
            cache_folder="/app/data/hf_cache"
        )

        logger.info("sentence_transformer_model_ready")

    return _model_instance


class EmbeddingEngine:

    def __init__(self):

        # Reuse the process-level singleton — no reload
        self.model = _get_model()

    @functools.lru_cache(maxsize=10000)
    def _cached_embedding(self, text: str) -> list:
        return self.model.encode(text).tolist()

    def generate_embedding(
        self,
        text
    ):
        return self._cached_embedding(text)