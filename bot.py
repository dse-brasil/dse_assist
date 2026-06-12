## Bot DSE — Data Science Enthusiasts
## Invite: https://discord.com/oauth2/authorize?client_id=1502761905054421242&permissions=2147568640&integration_type=0&scope=bot

import os
import sys
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from ai_providers import get_provider
from ai_providers.rag_provider import wrap_with_rag

# Corrige encoding no terminal Windows para suportar acentos e emojis
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─── Configuração ─────────────────────────────────────────────────────────────

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
AI_CHANNEL = os.getenv("AI_CHANNEL_NAME", "ia-comunidade")

if not TOKEN:
    raise ValueError("DISCORD_TOKEN nao configurado no .env")

COGS = [
    "cogs.ai_commands",
    "cogs.community",
]

# ─── Intents ──────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

# ─── Bot ──────────────────────────────────────────────────────────────────────

bot = commands.Bot(command_prefix="!", intents=intents)
bot.ai_provider = None


# ─── Eventos ──────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    provider_info = bot.ai_provider.name if bot.ai_provider else "Nenhum"
    print(f"[OK] Bot conectado como {bot.user} (ID: {bot.user.id})")
    print(f"[IA] Provedor: {provider_info}")
    print("-" * 40)
    if bot.guilds:
        print(f"[INFO] Bot presente em {len(bot.guilds)} servidor(es):")
        for g in bot.guilds:
            canais = [c.name for c in g.text_channels]
            print(f"  -> Servidor: '{g.name}' (ID: {g.id})")
            print(f"     Canais: {canais}")
    else:
        print("[AVISO] Bot NAO esta em nenhum servidor!")
        print(f"  Link: https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=2147568640&scope=bot")
    print("-" * 40)
    try:
        synced = await bot.tree.sync()
        print(f"[OK] {len(synced)} comandos slash sincronizados.")
    except Exception as e:
        print(f"[ERRO] Ao sincronizar comandos: {e}")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    print(f"[MSG] #{message.channel.name} | {message.author}: {message.content[:80]}")
    if message.content.lower() == "ping":
        await message.channel.send("Pong!")
    await bot.process_commands(message)


# ─── Slash Commands Globais ───────────────────────────────────────────────────

@bot.tree.command(name="hello", description="Apresenta o DSE Bot")
async def hello(interaction: discord.Interaction):
    provider_info = bot.ai_provider.name if bot.ai_provider else "Nao configurado"
    embed = discord.Embed(
        title="Ola! Eu sou o DSE Bot!",
        description=(
            "Assistente oficial da comunidade **Data Science Enthusiasts**!\n\n"
            "Use `/ajuda` para ver todos os comandos detalhados.\n\n"
            f"Ou va direto ao canal `#{AI_CHANNEL}` e fale comigo livremente!"
        ),
        color=discord.Color.from_rgb(88, 101, 242),
    )
    embed.set_footer(text=f"Powered by {provider_info} | Data Science Enthusiasts")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ajuda", description="Mostra o guia completo de uso do DSE Bot")
async def ajuda(interaction: discord.Interaction):
    """Posta 4 embeds com instrucoes completas de uso."""

    provider_info = bot.ai_provider.name if bot.ai_provider else "IA"

    # ── Embed 1: Apresentacao ─────────────────────────────────────────────────
    e1 = discord.Embed(
        title="🤖 DSE Bot — Guia de Uso",
        description=(
            "Ola! Sou o assistente oficial da comunidade **Data Science Enthusiasts**.\n"
            "Estou aqui para ajudar voce a aprender DS, ML, Python e Estatistica!\n\n"
            f"**Tecnologia:** {provider_info}\n"
            f"**Canal livre:** `#{AI_CHANNEL}`\n"
            "**Prefixo dos comandos:** `/`"
        ),
        color=discord.Color.from_rgb(88, 101, 242),
    )
    e1.set_footer(text="Data Science Enthusiasts • Use /ajuda para ver este guia novamente")

    # ── Embed 2: Canal livre ──────────────────────────────────────────────────
    e2 = discord.Embed(
        title=f"💬 Canal #{AI_CHANNEL} — Conversa Livre com IA",
        description=(
            f"No canal **#{AI_CHANNEL}** voce nao precisa de nenhum comando!\n"
            "Apenas escreva sua mensagem normalmente e eu respondo.\n\n"
            "**Exemplos do que voce pode perguntar:**\n"
            "```\n"
            "O que e machine learning?\n"
            "Como funciona o Random Forest?\n"
            "Qual a diferenca entre overfitting e underfitting?\n"
            "Me sugira um projeto para iniciantes em DS\n"
            "O que estudar primeiro: Python ou estatistica?\n"
            "```\n"
            "⚠️ **Limite gratuito:** Se receber aviso de espera, aguarde alguns segundos."
        ),
        color=discord.Color.from_rgb(87, 242, 135),
    )

    # ── Embed 3: Slash commands ───────────────────────────────────────────────
    e3 = discord.Embed(
        title="⚡ Comandos Slash Disponíveis",
        color=discord.Color.from_rgb(254, 231, 92),
    )
    e3.add_field(
        name="🤖  /ask [pergunta]",
        value=(
            "Faca qualquer pergunta sobre DS, ML, Python ou Estatistica.\n"
            "> Ex: `/ask Como funciona o gradient descent?`"
        ),
        inline=False,
    )
    e3.add_field(
        name="📚  /explain [conceito]",
        value=(
            "Explicacao didatica com analogias e exemplos praticos.\n"
            "> Ex: `/explain p-valor`  ou  `/explain redes neurais`"
        ),
        inline=False,
    )
    e3.add_field(
        name="💻  /code [pedido]",
        value=(
            "Gere codigo Python comentado para tarefas de Data Science.\n"
            "> Ex: `/code modelo de classificacao com sklearn e matrix de confusao`"
        ),
        inline=False,
    )
    e3.add_field(
        name="📊  /dataset [tema]",
        value=(
            "Descubra datasets publicos no Kaggle, UCI e HuggingFace.\n"
            "> Ex: `/dataset analise de sentimentos`  ou  `/dataset fraude financeira`"
        ),
        inline=False,
    )
    e3.add_field(
        name="🎯  /quiz",
        value=(
            "Quiz de multipla escolha sobre DS/ML para testar seu conhecimento.\n"
            "> A resposta fica como spoiler — tente antes de revelar!"
        ),
        inline=False,
    )
    e3.add_field(
        name="🗺️  /roadmap [nivel]",
        value=(
            "Plano de estudos personalizado para o seu nivel atual.\n"
            "> Opcoes: `Iniciante`  |  `Intermediario`  |  `Avancado`"
        ),
        inline=False,
    )

    # ── Embed 4: Dicas ────────────────────────────────────────────────────────
    e4 = discord.Embed(
        title="💡 Dicas para Melhores Respostas",
        description=(
            "**Seja especifico nas perguntas:**\n"
            "❌  `me explica ML`\n"
            "✅  `me explica como o Random Forest escolhe as variaveis em cada arvore`\n\n"
            "**Para codigo, descreva bem o objetivo:**\n"
            "❌  `codigo para ML`\n"
            "✅  `codigo Python para regressao linear com sklearn, plot dos residuos e R2`\n\n"
            "**Jornada recomendada para iniciantes:**\n"
            "```\n"
            "1. /roadmap Iniciante  → obtenha seu plano de estudos\n"
            "2. /explain [conceito] → entenda cada topico do roadmap\n"
            "3. /code [exercicio]   → pratique com codigo real\n"
            "4. /quiz               → teste o que aprendeu\n"
            "5. /dataset [tema]     → encontre dados para seu projeto\n"
            "```\n"
            f"**Canal livre:** Va ao `#{AI_CHANNEL}` e converse sem precisar de comandos!"
        ),
        color=discord.Color.from_rgb(235, 69, 158),
    )
    e4.set_footer(text=f"Powered by {provider_info} | Data Science Enthusiasts")

    await interaction.response.send_message(embeds=[e1, e2, e3, e4])


# ─── Inicialização ────────────────────────────────────────────────────────────

async def main():
    try:
        base_provider = get_provider()
        print(f"[IA] Provedor base: {base_provider.name}")
        # Envolve com RAG se CHROMA_API_KEY estiver configurada
        bot.ai_provider = wrap_with_rag(base_provider)
        print(f"[IA] Provider ativo: {bot.ai_provider.name}")
    except ValueError as e:
        print(f"[AVISO] {e}")
        print("[AVISO] O bot iniciara SEM funcionalidades de IA.")

    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"[OK] Cog carregado: {cog}")
        except Exception as e:
            print(f"[ERRO] Ao carregar cog '{cog}': {e}")

    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())