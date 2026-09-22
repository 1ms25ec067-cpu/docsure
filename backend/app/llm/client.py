import os

from dotenv import load_dotenv


load_dotenv()


class LLMClient:

    def __init__(self):
        self.api_key = os.getenv(
            "GEMINI_API_KEY"
        )

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate(
        self,
        prompt: str,
    ):
        if not self.is_configured():
            return {
                "status": "NOT_CONFIGURED",
                "message": "Gemini API key is not configured.",
            }

        return {
            "status": "READY",
            "message": "Gemini client is configured.",
            "prompt": prompt,
        }