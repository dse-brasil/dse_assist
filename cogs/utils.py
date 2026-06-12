"""
Utilitários compartilhados entre os cogs.
- Rate limiting por usuário
- Construção de embeds padronizados
"""

import time
import discord
from collections import defaultdict

# ─── Rate Limiting ────────────────────────────────────────────────────────────

RATE_LIMIT_MAX = 10     # máximo de requisições por janela
RATE_LIMIT_WINDOW = 60  # janela em segundos (1 minuto)

_rate_tracker: dict[int, list[float]] = defaultdict(list)


def check_rate_limit(user_id: int) -> tuple[bool, int]:
    """
    Verifica se o usuário excedeu o rate limit.

    Returns:
        (is_limited, seconds_to_wait)
        is_limited=True significa que o usuário deve aguardar.
    """
    now = time.time()

    # Remove timestamps fora da janela
    _rate_tracker[user_id] = [
        t for t in _rate_tracker[user_id]
        if now - t < RATE_LIMIT_WINDOW
    ]

    if len(_rate_tracker[user_id]) >= RATE_LIMIT_MAX:
        oldest = _rate_tracker[user_id][0]
        wait = int(RATE_LIMIT_WINDOW - (now - oldest)) + 1
        return True, wait

    _rate_tracker[user_id].append(now)
    return False, 0


# ─── Embed Builders ───────────────────────────────────────────────────────────

MAX_EMBED_DESC = 4000  # limite do Discord por embed


def build_ai_embed(
    title: str,
    content: str,
    user: discord.User | discord.Member,
    provider_name: str = "IA",
    color: discord.Color = discord.Color.blurple(),
) -> list[discord.Embed]:
    """
    Cria um ou mais embeds com a resposta da IA.
    Divide automaticamente se o conteúdo ultrapassar o limite do Discord.
    """
    chunks = [
        content[i:i + MAX_EMBED_DESC]
        for i in range(0, len(content), MAX_EMBED_DESC)
    ]
    embeds = []

    for i, chunk in enumerate(chunks):
        embed = discord.Embed(color=color)

        if i == 0:
            embed.title = title

        embed.description = chunk

        if i == len(chunks) - 1:
            embed.set_footer(
                text=f"Pedido por {user.display_name} • Powered by {provider_name}",
                icon_url=user.display_avatar.url,
            )

        embeds.append(embed)

    return embeds


def build_error_embed(message: str) -> discord.Embed:
    """Embed de erro padronizado."""
    return discord.Embed(
        title="❌ Algo deu errado",
        description=message,
        color=discord.Color.red(),
    )


def build_rate_limit_embed(seconds: int) -> discord.Embed:
    """Embed de rate limit padronizado."""
    return discord.Embed(
        title="⏳ Calma aí!",
        description=(
            f"Você enviou muitas requisições.\n"
            f"Aguarde **{seconds} segundo{'s' if seconds != 1 else ''}** e tente novamente."
        ),
        color=discord.Color.orange(),
    )
