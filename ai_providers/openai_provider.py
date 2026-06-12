from openai import AsyncOpenAI
from .base import BaseAIProvider


class OpenAIProvider(BaseAIProvider):
    """Provedor para OpenAI (GPT-4o, GPT-4o-mini, etc.)."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model_name = model

    @property
    def name(self) -> str:
        return f"OpenAI ({self.model_name})"

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
