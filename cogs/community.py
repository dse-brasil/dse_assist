"""
Cog: Community
Funcionalidades voltadas para a comunidade DSE:
  - Boas-vindas automáticas para novos membros
  - Canal de IA livre: responde qualquer mensagem no canal configurado
"""

import os
import re
import discord
from discord.ext import commands

from config.prompts import FREE_CHANNEL_PROMPT
from cogs.utils import (
    check_rate_limit,
    build_ai_embed,
    build_error_embed,
    build_rate_limit_embed,
)

# Lê configurações do .env (com fallbacks razoáveis)
AI_CHANNEL_NAME: str = os.getenv("AI_CHANNEL_NAME", "ia-comunidade")
WELCOME_CHANNEL_NAME: str = os.getenv("WELCOME_CHANNEL_NAME", "geral")

# Comprimento mínimo de mensagem para acionar a IA no canal livre
MIN_MESSAGE_LEN = 5


class Community(commands.Cog):
    """Eventos de comunidade e canal de IA livre."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def ai(self):
        return self.bot.ai_provider

    # ── Boas-vindas ───────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Envia mensagem de boas-vindas quando um novo membro entra no servidor."""
        channel = discord.utils.get(
            member.guild.text_channels, name=WELCOME_CHANNEL_NAME
        )
        if not channel:
            return

        embed = discord.Embed(
            title=f"👋 Bem-vindo(a), {member.display_name}!",
            description=(
                f"É um prazer ter você na comunidade **Data Science Enthusiasts**, {member.mention}! 🎉\n\n"
                "**Por onde começar:**\n"
                f"🤖 `#{AI_CHANNEL_NAME}` — Converse com a IA livremente sobre DS\n"
                "📋 `/ask` — Tire dúvidas técnicas de DS/ML/Python\n"
                "📚 `/explain` — Entenda conceitos com explicações didáticas\n"
                "🗺️ `/roadmap` — Descubra seu caminho de estudos\n"
                "🎯 `/quiz` — Teste seus conhecimentos com quizzes\n\n"
                "_Seja curioso, colabore e divirta-se aprendendo!_ 🚀"
            ),
            color=discord.Color.from_rgb(88, 101, 242),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(
            text=f"Data Science Enthusiasts • {member.guild.member_count} membros"
        )
        await channel.send(embed=embed)

    # ── Canal de IA Livre ─────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Responde com IA qualquer mensagem enviada no canal de IA livre."""
        # Ignora mensagens do próprio bot
        if message.author.bot:
            return

        # Só processa mensagens no canal de IA configurado
        if message.channel.name != AI_CHANNEL_NAME:
            return

        # Ignora mensagens muito curtas (emojis, "ok", "oi", etc.)
        if len(message.content.strip()) < MIN_MESSAGE_LEN:
            return

        # Verifica rate limit
        is_limited, wait = check_rate_limit(message.author.id)
        if is_limited:
            await message.reply(
                embed=build_rate_limit_embed(wait), mention_author=False
            )
            return

        async with message.channel.typing():
            try:
                user_input = f"<user_input>\n{message.content}\n</user_input>"
                response = await self.ai.generate(
                    user_input,
                    FREE_CHANNEL_PROMPT,
                    user_id=message.author.id,
                    username=message.author.name,
                    channel=message.channel.name,
                    command="message",
                )

                # Resposta curta -> texto simples (mais natural no chat)
                # Resposta longa -> embed formatado
                if len(response) <= 1800:
                    await message.reply(response, mention_author=False)
                else:
                    embeds = build_ai_embed(
                        title="Resposta",
                        content=response,
                        user=message.author,
                        provider_name=self.ai.name,
                        color=discord.Color.from_rgb(88, 101, 242),
                    )
                    await message.reply(embeds=embeds, mention_author=False)

            except Exception as e:
                err_str = str(e)
                # Trata quota excedida (429) com mensagem amigavel
                if '429' in err_str or 'quota' in err_str.lower():
                    wait = 60
                    match = re.search(r'retry.*?(\d+)s', err_str, re.IGNORECASE)
                    if match:
                        wait = int(match.group(1)) + 5
                    embed = discord.Embed(
                        title="Limite de requisicoes atingido",
                        description=(
                            f"A IA atingiu o limite de requisicoes gratuitas por minuto.\n"
                            f"Aguarde **{wait} segundos** e tente novamente."
                        ),
                        color=discord.Color.orange(),
                    )
                    await message.reply(embed=embed, mention_author=False)
                else:
                    await message.reply(
                        embed=build_error_embed(f"Erro ao processar sua mensagem:\n```{err_str[:300]}```"),
                        mention_author=False,
                    )


async def setup(bot: commands.Bot):
    await bot.add_cog(Community(bot))
