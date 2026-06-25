from pydantic_settings import (
    BaseSettings
)

from dotenv import load_dotenv

# =================================================
# LOAD ENV
# =================================================

load_dotenv()

# =================================================
# SETTINGS
# =================================================

class Settings(BaseSettings):

    # ---------------------------------------------
    # GITHUB
    # ---------------------------------------------

    GITHUB_TOKEN: str = ""

    GITHUB_PAT: str = ""

    # ---------------------------------------------
    # AI PROVIDERS
    # ---------------------------------------------

    GROQ_API_KEY: str = ""

    GEMINI_API_KEY: str = ""

    OPENAI_API_KEY: str = ""

    # ---------------------------------------------
    # PROVIDERS
    # ---------------------------------------------

    LLM_PROVIDER: str = "gemini"

    EMBEDDING_PROVIDER: str = "local"

    # Provider feature flags
    GEMINI_ENABLED: bool = True
    GROQ_ENABLED: bool = True
    OLLAMA_ENABLED: bool = False
    HEURISTIC_PARSER_ENABLED: bool = True
    # Project Coherence
    ENABLE_PROJECT_COHERENCE: bool = False
    
    # Identity Resolution Engine
    ENABLE_IDENTITY_RESOLUTION: bool = False

    # Preferred model names (can be overridden via .env)
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_MODEL: str = "gemini-pro"

    # Ollama configuration
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_TIMEOUT: int = 300

    # ---------------------------------------------
    # CONFIG
    # ---------------------------------------------

    class Config:

        env_file = ".env"

    # ---------------------------------------------
    # CUSTOM SETTINGS
    # ---------------------------------------------
    # Low‑confidence threshold for semantic matching (0.75 as requested)
    LOW_CONFIDENCE_THRESHOLD: float = 0.75

    # JWT Authentication
    JWT_SECRET: str = ""


# =================================================
# INSTANCE
# =================================================

settings = Settings()