import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from groq import Groq

from backend.config.settings import settings


class GroqProvider:

    def __init__(self):

        self.client = Groq(
            api_key=settings.GROQ_API_KEY
        )

    def generate(
        self,
        prompt
    ):

        model_name = getattr(settings, "GROQ_MODEL", "llama3-70b")

        response = self.client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Gracefully handle different response shapes
        try:
            return response.choices[0].message.content
        except Exception:
            # Fallback to raw string conversion
            return str(response)


class GeminiProvider:

    def __init__(self):

        from google import genai

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        self.model_name = getattr(settings, "GEMINI_MODEL", "gemini-pro")

    def generate(
        self,
        prompt
    ):

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )

        return response.text


class OllamaProvider:

    def __init__(self):
        self.base_url = getattr(settings, "OLLAMA_URL", "http://localhost:11434").rstrip("/")
        self.model = getattr(settings, "OLLAMA_MODEL", "llama3")
        self.timeout = getattr(settings, "OLLAMA_TIMEOUT", 300)

    def generate(
        self,
        prompt
    ):
        endpoint = f"{self.base_url}/api/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.load(response)
        except HTTPError as e:
            raise RuntimeError(f"Ollama request failed with status {e.code}: {e.reason}") from e
        except URLError as e:
            raise RuntimeError(f"Ollama request failed: {e.reason}") from e

        message = None
        if isinstance(data, dict):
            if "choices" in data and data["choices"]:
                choice = data["choices"][0]
                if isinstance(choice, dict):
                    message = (
                        choice.get("message", {}).get("content")
                        or choice.get("text")
                        or choice.get("completion")
                    )
            if message is None:
                message = data.get("response") or data.get("completion") or data.get("text")

        return message if message is not None else json.dumps(data)