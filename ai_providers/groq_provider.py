from groq import AsyncGroq
from .base import BaseAIProvider


class GroqProvider(BaseAIProvider):
    """Provedor para Groq (Llama, Mixtral — gratuito e muito rápido)."""

    def __init__(self, api_key: str, model: str = "llama-3.1-70b-versatile"):
        self.client = AsyncGroq(api_key=api_key)
        self.model_name = model

    @property
    def name(self) -> str:
        return f"Groq ({self.model_name})"

    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=1500,
        )
        return response.choices[0].message.content
