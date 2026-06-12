"""
AI Providers — Factory de provedores de IA.

Para trocar de IA, altere no .env:
  AI_PROVIDER=gemini   → Google Gemini (padrão)
  AI_PROVIDER=openai   → OpenAI GPT
  AI_PROVIDER=groq     → Groq (Llama, Mixtral)

Para adicionar um novo provedor:
  1. Crie ai_providers/meu_provider.py herdando de BaseAIProvider
  2. Adicione o elif abaixo em get_provider()
  3. Configure AI_PROVIDER=meu_provider no .env
"""

import os
from .base import BaseAIProvider


SUPPORTED_PROVIDERS = {
    "gemini": "google-generativeai",
    "openai": "openai",
    "groq": "groq",
}


def get_provider() -> BaseAIProvider:
    """
    Retorna o provedor de IA configurado no .env.

    Variáveis de ambiente necessárias:
        AI_PROVIDER: Nome do provedor (gemini, openai, groq)
        AI_API_KEY:  Chave da API
        AI_MODEL:    Modelo (opcional — usa padrão do provedor)
    """
    provider_name = os.getenv("AI_PROVIDER", "gemini").lower().strip()
    api_key = os.getenv("AI_API_KEY", "").strip()
    model = os.getenv("AI_MODEL", "").strip()

    if not api_key:
        raise ValueError(
            "❌ AI_API_KEY não configurada no .env\n"
            f"   Obtenha sua chave em: https://aistudio.google.com/app/apikey (Gemini)"
        )

    if provider_name == "gemini":
        from .gemini import GeminiProvider
        return GeminiProvider(api_key, model or "gemini-1.5-flash")

    elif provider_name == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(api_key, model or "gpt-4o-mini")

    elif provider_name == "groq":
        from .groq_provider import GroqProvider
        return GroqProvider(api_key, model or "llama-3.1-70b-versatile")

    else:
        supported = ", ".join(SUPPORTED_PROVIDERS.keys())
        raise ValueError(
            f"❌ Provedor '{provider_name}' não suportado.\n"
            f"   Provedores disponíveis: {supported}"
        )


__all__ = ["get_provider", "BaseAIProvider"]
