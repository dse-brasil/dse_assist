import google.generativeai as genai
from .base import BaseAIProvider


class GeminiProvider(BaseAIProvider):
    """Provedor para Google Gemini (gratuito via AI Studio)."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model_name = model
        self._model = genai.GenerativeModel(model)

    @property
    def name(self) -> str:
        return f"Google Gemini ({self.model_name})"

    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = await self._model.generate_content_async(full_prompt)
        return response.text
