from app.ai.gemini.gemini_client import get_gemini_client
from app.core.config import settings


class GeminiService:
    def __init__(self):
        self.client = get_gemini_client()
        self.model = settings.GEMINI_MODEL

    def ask(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        return response.text or "Sin respuesta"