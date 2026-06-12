"""
Cog: AI Commands
Slash commands que integram IA para a comunidade Data Science Enthusiasts.

Comandos:
  /ask       — Pergunta livre para a IA
  /explain   — Explicação didática de um conceito
  /code      — Geração de código Python para DS
  /dataset   — Sugestão de datasets públicos
  /quiz      — Quiz de múltipla escolha
  /roadmap   — Roadmap de estudos personalizado
"""

import re
import discord
from discord import app_commands
from discord.ext import commands

from config.prompts import (
    SYSTEM_PROMPT,
    EXPLAIN_PROMPT,
    CODE_PROMPT,
    QUIZ_PROMPT,
    DATASET_PROMPT,
    ROADMAP_PROMPT,
)
from cogs.utils import (
    check_rate_limit,
    build_ai_embed,
    build_error_embed,
    build_rate_limit_embed,
)

# Cores por comando (RGB)
COLOR_ASK = discord.Color.from_rgb(88, 101, 242)    # Blurple
COLOR_EXPLAIN = discord.Color.from_rgb(87, 242, 135)  # Verde
COLOR_CODE = discord.Color.from_rgb(254, 231, 92)   # Amarelo
COLOR_DATASET = discord.Color.from_rgb(235, 69, 158)  # Rosa
COLOR_QUIZ = discord.Color.from_rgb(255, 140, 0)    # Laranja
COLOR_ROADMAP = discord.Color.from_rgb(100, 200, 150)  # Verde-água


class AICommands(commands.Cog):
    """Comandos slash de IA para Data Science."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def ai(self):
        return self.bot.ai_provider

    def _quota_embed(self, err_str: str) -> discord.Embed:
        """Retorna embed amigavel para erro 429 (quota excedida)."""
        wait = 60
        match = re.search(r'retry.*?(\d+)s', err_str, re.IGNORECASE)
        if match:
            wait = int(match.group(1)) + 5
        return discord.Embed(
            title="Limite de requisicoes atingido",
            description=(
                f"A IA atingiu o limite gratuito de requisicoes por minuto.\n"
                f"Aguarde **{wait} segundos** e tente novamente."
            ),
            color=discord.Color.orange(),
        )

    async def _send_error(self, interaction: discord.Interaction, e: Exception):
        """Envia embed de erro adequado (429 vs erro generico)."""
        err_str = str(e)
        if '429' in err_str or 'quota' in err_str.lower():
            embed = self._quota_embed(err_str)
        else:
            embed = build_error_embed(err_str[:400])
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /ask ──────────────────────────────────────────────────────────────────

    @app_commands.command(
        name="ask",
        description="🤖 Faça uma pergunta sobre Data Science, ML, Python ou estatística"
    )
    @app_commands.describe(pergunta="Sua dúvida (ex: Como funciona o gradient descent?)")
    async def ask(self, interaction: discord.Interaction, pergunta: str):
        is_limited, wait = check_rate_limit(interaction.user.id)
        if is_limited:
            await interaction.response.send_message(
                embed=build_rate_limit_embed(wait), ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)
        try:
            user_input = f"<user_input>\n{pergunta}\n</user_input>"
            response = await self.ai.generate(
                user_input,
                SYSTEM_PROMPT,
                user_id=interaction.user.id,
                username=interaction.user.name,
                channel=interaction.channel.name if interaction.channel else "Direct Message",
                command="/ask",
            )
            title = f"🤖 {pergunta[:80]}{'...' if len(pergunta) > 80 else ''}"
            embeds = build_ai_embed(title, response, interaction.user, self.ai.name, COLOR_ASK)
            await interaction.followup.send(embeds=embeds)
        except Exception as e:
            await self._send_error(interaction, e)

    # ── /explain ──────────────────────────────────────────────────────────────

    @app_commands.command(
        name="explain",
        description="📚 Explique um conceito de DS/ML de forma simples e didática"
    )
    @app_commands.describe(conceito="Conceito a explicar (ex: overfitting, p-valor, Random Forest...)")
    async def explain(self, interaction: discord.Interaction, conceito: str):
        is_limited, wait = check_rate_limit(interaction.user.id)
        if is_limited:
            await interaction.response.send_message(
                embed=build_rate_limit_embed(wait), ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)
        try:
            prompt = f"Explique o seguinte conceito de Data Science: **{conceito}**"
            user_input = f"<user_input>\n{prompt}\n</user_input>"
            response = await self.ai.generate(
                user_input,
                EXPLAIN_PROMPT,
                user_id=interaction.user.id,
                username=interaction.user.name,
                channel=interaction.channel.name if interaction.channel else "Direct Message",
                command="/explain",
            )
            embeds = build_ai_embed(
                f"📚 {conceito}", response, interaction.user, self.ai.name, COLOR_EXPLAIN
            )
            await interaction.followup.send(embeds=embeds)
        except Exception as e:
            await self._send_error(interaction, e)

    # ── /code ─────────────────────────────────────────────────────────────────

    @app_commands.command(
        name="code",
        description="💻 Gere código Python para tarefas de Data Science"
    )
    @app_commands.describe(pedido="O que o código deve fazer (ex: treinar um modelo de regressão linear)")
    async def code(self, interaction: discord.Interaction, pedido: str):
        is_limited, wait = check_rate_limit(interaction.user.id)
        if is_limited:
            await interaction.response.send_message(
                embed=build_rate_limit_embed(wait), ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)
        try:
            user_input = f"<user_input>\n{pedido}\n</user_input>"
            response = await self.ai.generate(
                user_input,
                CODE_PROMPT,
                user_id=interaction.user.id,
                username=interaction.user.name,
                channel=interaction.channel.name if interaction.channel else "Direct Message",
                command="/code",
            )
            title = f"💻 {pedido[:60]}{'...' if len(pedido) > 60 else ''}"
            embeds = build_ai_embed(title, response, interaction.user, self.ai.name, COLOR_CODE)
            await interaction.followup.send(embeds=embeds)
        except Exception as e:
            await self._send_error(interaction, e)

    # ── /dataset ──────────────────────────────────────────────────────────────

    @app_commands.command(
        name="dataset",
        description="📊 Encontre datasets públicos para praticar"
    )
    @app_commands.describe(tema="Tema ou problema (ex: análise de sentimentos, previsão de vendas)")
    async def dataset(self, interaction: discord.Interaction, tema: str):
        is_limited, wait = check_rate_limit(interaction.user.id)
        if is_limited:
            await interaction.response.send_message(
                embed=build_rate_limit_embed(wait), ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)
        try:
            prompt = f"Tema: {tema}"
            user_input = f"<user_input>\n{prompt}\n</user_input>"
            response = await self.ai.generate(
                user_input,
                DATASET_PROMPT,
                user_id=interaction.user.id,
                username=interaction.user.name,
                channel=interaction.channel.name if interaction.channel else "Direct Message",
                command="/dataset",
            )
            embeds = build_ai_embed(
                f"📊 Datasets para: {tema}", response, interaction.user, self.ai.name, COLOR_DATASET
            )
            await interaction.followup.send(embeds=embeds)
        except Exception as e:
            await self._send_error(interaction, e)

    # ── /quiz ─────────────────────────────────────────────────────────────────

    @app_commands.command(
        name="quiz",
        description="🎯 Gere um quiz desafiador sobre qualquer área, tecnologia ou profissão de dados"
    )
    async def quiz(self, interaction: discord.Interaction):
        is_limited, wait = check_rate_limit(interaction.user.id)
        if is_limited:
            await interaction.response.send_message(
                embed=build_rate_limit_embed(wait), ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)
        try:
            prompt = "Gere uma pergunta de quiz aleatória e desafiadora sobre qualquer área, ferramenta, tecnologia ou profissão do universo de dados."
            user_input = f"<user_input>\n{prompt}\n</user_input>"
            response = await self.ai.generate(
                user_input,
                QUIZ_PROMPT,
                user_id=interaction.user.id,
                username=interaction.user.name,
                channel=interaction.channel.name if interaction.channel else "Direct Message",
                command="/quiz",
            )
            embeds = build_ai_embed(
                "🎯 Quiz do Universo de Dados — DSE",
                response,
                interaction.user,
                self.ai.name,
                COLOR_QUIZ,
            )
            await interaction.followup.send(embeds=embeds)
        except Exception as e:
            await self._send_error(interaction, e)

    # ── /roadmap ──────────────────────────────────────────────────────────────

    @app_commands.command(
        name="roadmap",
        description="🗺️ Veja um roadmap de estudos personalizado para o seu nível"
    )
    @app_commands.describe(nivel="Seu nível atual em Data Science")
    @app_commands.choices(nivel=[
        app_commands.Choice(name="🌱 Iniciante — Estou começando agora", value="iniciante"),
        app_commands.Choice(name="🌿 Intermediário — Sei o básico, quero evoluir", value="intermediario"),
        app_commands.Choice(name="🌳 Avançado — Quero especializar e trabalhar com MLOps/DL", value="avancado"),
    ])
    async def roadmap(self, interaction: discord.Interaction, nivel: str):
        is_limited, wait = check_rate_limit(interaction.user.id)
        if is_limited:
            await interaction.response.send_message(
                embed=build_rate_limit_embed(wait), ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)
        try:
            prompt = f"Nível do aluno: {nivel}"
            user_input = f"<user_input>\n{prompt}\n</user_input>"
            response = await self.ai.generate(
                user_input,
                ROADMAP_PROMPT,
                user_id=interaction.user.id,
                username=interaction.user.name,
                channel=interaction.channel.name if interaction.channel else "Direct Message",
                command="/roadmap",
            )
            emojis = {"iniciante": "🌱", "intermediario": "🌿", "avancado": "🌳"}
            emoji = emojis.get(nivel, "🗺️")
            embeds = build_ai_embed(
                f"{emoji} Roadmap — Nível {nivel.capitalize()}",
                response,
                interaction.user,
                self.ai.name,
                COLOR_ROADMAP,
            )
            await interaction.followup.send(embeds=embeds)
        except Exception as e:
            await self._send_error(interaction, e)


async def setup(bot: commands.Bot):
    await bot.add_cog(AICommands(bot))
