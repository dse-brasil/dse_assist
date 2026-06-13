import os
import re
import sys
import asyncio
import discord
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config.prompts import (
    SYSTEM_PROMPT,
    EXPLAIN_PROMPT,
    CODE_PROMPT,
    DATASET_PROMPT,
    ROADMAP_PROMPT,
    QUIZ_PROMPT,
)
from cogs.utils import check_rate_limit

# ─── Utilitários de Formatação e Regex ────────────────────────────────────────

def format_tg_markdown(text: str) -> str:
    """
    Adapta o Markdown padrão gerado pelo LLM para o formato compatível
    com o parse_mode='Markdown' do Telegram.
    """
    # Substitui **negrito** por *negrito*
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
    # Substitui marcadores de lista '*' por '•' para evitar conflito com negrito
    if text.startswith("* "):
        text = "• " + text[2:]
    text = text.replace("\n* ", "\n• ")
    return text


def parse_quiz_response(response: str) -> tuple[str, str]:
    """
    Divide a resposta gerada pelo QUIZ_PROMPT em duas partes:
    1. A pergunta com suas alternativas (A, B, C, D)
    2. A resposta e explicação detalhada contida nas tags de spoiler ||...||
    """
    match = re.search(r'\|\|(.*?)\|\|', response, re.DOTALL)
    if match:
        question_part = response.replace(match.group(0), "").strip()
        answer_part = match.group(1).strip()
        # Remove eventuais marcações de spoiler duplicadas
        answer_part = answer_part.replace("||", "")
        return question_part, answer_part
    return response, "Não foi possível carregar a explicação da resposta automaticamente."


def format_tg_error_message(e: Exception) -> str:
    """
    Retorna uma mensagem de erro amigável para o Telegram,
    formatando erros de cota (429) de forma clara.
    """
    err_str = str(e)
    if '429' in err_str or 'quota' in err_str.lower():
        wait = 60
        match = re.search(r'retry.*?(\d+)s', err_str, re.IGNORECASE)
        if match:
            wait = int(match.group(1)) + 5
        return (
            f"⏳ **Limite de requisições atingido:** A IA atingiu o limite gratuito temporário de requisições por minuto.\n"
            f"Por favor, aguarde **{wait} segundos** e tente novamente."
        )
    return f"❌ Ocorreu um erro ao processar sua requisição: {err_str[:200]}"


# ─── Verificação de Rate Limit ───────────────────────────────────────────────

async def is_rate_limited(update: Update) -> bool:
    """Valida se o usuário do Telegram estourou a cota de requisições."""
    user_id = update.effective_user.id
    is_limited, wait = check_rate_limit(user_id)
    if is_limited:
        await update.message.reply_text(
            f"⏳ **Calma aí!** Você enviou muitas requisições.\n"
            f"Aguarde **{wait} segundos** e tente novamente.",
            parse_mode="Markdown"
        )
        return True
    return False


# ─── Executor Central de IA (RAG + Segurança) ─────────────────────────────────

async def run_ai_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    system_prompt: str,
    command_name: str,
    query: str = "",
):
    """
    Executa a requisição de IA acoplando o provedor de IA ativo do bot Discord.
    Herda automaticamente o RAG, auditoria criptográfica e prevenção de Prompt Injection.
    """
    if await is_rate_limited(update):
        return

    # Extrai o prompt se não foi fornecido diretamente
    if not query and update.message:
        text = update.message.text
        if text.startswith("/"):
            parts = text.split(maxsplit=1)
            query = parts[1].strip() if len(parts) > 1 else ""

    if not query:
        await update.message.reply_text("❌ Por favor, digite sua pergunta ou conceito após o comando!")
        return

    # Envia indicador visual de digitação
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    discord_bot = context.bot_data["discord_bot"]
    ai = discord_bot.ai_provider

    if not ai:
        await update.message.reply_text("❌ Serviço de inteligência artificial temporariamente indisponível.")
        return

    try:
        user_input = f"<user_input>\n{query}\n</user_input>"
        
        # Gera a resposta passando pelos RAG e filtros de segurança ativos
        response = await ai.generate(
            user_input,
            system_prompt,
            user_id=update.effective_user.id,
            username=update.effective_user.username or update.effective_user.first_name,
            channel=update.effective_chat.title or "Telegram Direct",
            command=command_name,
        )

        formatted_response = format_tg_markdown(response)
        footer = f"\n\n*Pedido por {update.effective_user.first_name} • Powered by {ai.name}*"

        try:
            await update.message.reply_text(
                formatted_response + footer,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        except Exception as e:
            # Resubmissão em texto plano caso ocorra erro no parser de Markdown
            print(f"[TELEGRAM WARNING] Erro ao enviar Markdown: {e}. Reenviando em texto plano...")
            await update.message.reply_text(
                response + f"\n\nPedido por {update.effective_user.first_name} • Powered by {ai.name}",
                disable_web_page_preview=True
            )

    except Exception as e:
        print(f"[TELEGRAM ERRO] Falha no comando {command_name}: {e}")
        await update.message.reply_text(format_tg_error_message(e), parse_mode="Markdown")


# ─── Comando Handlers ─────────────────────────────────────────────────────────

async def cmd_ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retorna a lista de ajuda dos comandos do Telegram."""
    help_text = (
        "🤖 **DSE.Assist — Menu de Ajuda no Telegram**\n\n"
        "Olá! Sou o assistente de IA da comunidade **Data Science Enthusiasts (DSE)**. "
        "Estou pronto para ajudar você em seus estudos de dados!\n\n"
        "🛠️ **Comandos Disponíveis:**\n"
        "• `/ask [pergunta]` — Tira dúvidas técnicas sobre dados, ML e Python.\n"
        "• `/explain [conceito]` — Explicação didática detalhada com analogias.\n"
        "• `/code [pedido]` — Gera scripts Python comentados e formatados.\n"
        "• `/dataset [tema]` — Indica datasets de qualidade para praticar.\n"
        "• `/quiz` — Pergunta técnica com botões inline para testar seu conhecimento.\n"
        "• `/roadmap` — Menu interativo para obter plano de estudos personalizado.\n"
        "• `/ajuda` — Exibe este menu de ajuda.\n\n"
        "💬 **Interação em Grupo:**\n"
        "Você também pode interagir comigo no grupo me marcando (ex: `@nome_do_bot`) ou respondendo a uma mensagem minha."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def cmd_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_ai_command(update, context, SYSTEM_PROMPT, "/ask")


async def cmd_explain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_ai_command(update, context, EXPLAIN_PROMPT, "/explain")


async def cmd_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_ai_command(update, context, CODE_PROMPT, "/code")


async def cmd_dataset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_ai_command(update, context, DATASET_PROMPT, "/dataset")


async def cmd_roadmap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando de Roadmap com interface interativa de botões inline."""
    text = update.message.text
    parts = text.split(maxsplit=1)
    nivel = parts[1].strip().lower() if len(parts) > 1 else ""

    # Se o nível foi digitado direto no comando, processa
    if nivel in ["iniciante", "intermediario", "avancado", "intermediário", "avançado"]:
        # Normalização de acentos
        if nivel == "intermediário": nivel = "intermediario"
        if nivel == "avançado": nivel = "avancado"
        await run_ai_command(update, context, ROADMAP_PROMPT, "/roadmap", query=nivel)
        return

    # Caso contrário, monta o teclado de seleção
    keyboard = [
        [
            InlineKeyboardButton("🌱 Iniciante", callback_data="roadmap_iniciante"),
            InlineKeyboardButton("🌿 Intermediário", callback_data="roadmap_intermediario"),
        ],
        [
            InlineKeyboardButton("🌳 Avançado", callback_data="roadmap_avancado")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🗺️ **Roadmap de Estudos Personalizado**\n"
        "Selecione o seu nível de estudos abaixo para gerar o roadmap:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def cmd_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gera um quiz técnico e acopla a resposta em um callback seguro."""
    if await is_rate_limited(update):
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    discord_bot = context.bot_data["discord_bot"]
    ai = discord_bot.ai_provider

    if not ai:
        await update.message.reply_text("❌ Serviço de inteligência artificial indisponível.")
        return

    try:
        prompt = "Gere uma pergunta de quiz aleatória e desafiadora sobre qualquer área, ferramenta, tecnologia ou profissão do universo de dados."
        user_input = f"<user_input>\n{prompt}\n</user_input>"

        response = await ai.generate(
            user_input,
            QUIZ_PROMPT,
            user_id=update.effective_user.id,
            username=update.effective_user.username or update.effective_user.first_name,
            channel=update.effective_chat.title or "Telegram Direct",
            command="/quiz",
        )

        question, answer = parse_quiz_response(response)
        formatted_question = format_tg_markdown(question)
        
        # Teclado inline para revelar a resposta explicada
        keyboard = [[InlineKeyboardButton("👁️ Revelar Resposta", callback_data="reveal_answer")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        footer = f"\n\n*Gerado por {ai.name}*"

        msg = await update.message.reply_text(
            formatted_question + footer,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

        # Registra a resposta em cache usando o ID único da mensagem
        key = f"{update.effective_chat.id}_{msg.message_id}"
        context.bot_data["quiz_answers"][key] = answer

    except Exception as e:
        print(f"[TELEGRAM ERRO] Falha ao gerar quiz: {e}")
        await update.message.reply_text(format_tg_error_message(e), parse_mode="Markdown")


# ─── Callback Handler (Botões Inline) ────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Controla as ações de cliques nos botões inline de Roadmap e Quiz."""
    query = update.callback_query
    await query.answer()

    data = query.data
    chat_id = query.message.chat.id
    message_id = query.message.message_id

    # 1. Trata Cliques do Roadmap
    if data.startswith("roadmap_"):
        nivel = data.split("_")[1]
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        discord_bot = context.bot_data["discord_bot"]
        ai = discord_bot.ai_provider

        try:
            emojis = {"iniciante": "🌱", "intermediario": "🌿", "avancado": "🌳"}
            emoji = emojis.get(nivel, "🗺️")
            
            await query.edit_message_text(
                f"{emoji} **Roadmap — Nível {nivel.capitalize()} selecionado**\n"
                f"Gerando seu plano de estudos personalizado com a IA...",
                parse_mode="Markdown"
            )

            user_input = f"<user_input>\nNível do aluno: {nivel}\n</user_input>"
            response = await ai.generate(
                user_input,
                ROADMAP_PROMPT,
                user_id=query.from_user.id,
                username=query.from_user.username or query.from_user.first_name,
                channel=query.message.chat.title or "Telegram Private",
                command=f"/roadmap {nivel}",
            )

            formatted = format_tg_markdown(response)
            footer = f"\n\n*Pedido por {query.from_user.first_name} • Powered by {ai.name}*"

            await context.bot.send_message(
                chat_id=chat_id,
                text=formatted + footer,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        except Exception as e:
            print(f"[TELEGRAM ERRO] Callback roadmap: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=format_tg_error_message(e),
                parse_mode="Markdown"
            )

    # 2. Trata Cliques do Quiz
    elif data == "reveal_answer":
        key = f"{chat_id}_{message_id}"
        answer = context.bot_data["quiz_answers"].get(key)

        if not answer:
            await query.answer("Este quiz expirou. Por favor, gere um novo usando /quiz!", show_alert=True)
            return

        orig_text = query.message.text
        formatted_answer = format_tg_markdown(answer)
        
        new_text = (
            f"{orig_text}\n\n"
            f"💡 **Resposta Revelada:**\n"
            f"{formatted_answer}"
        )

        try:
            await query.edit_message_text(new_text, parse_mode="Markdown")
        except Exception as e:
            print(f"[TELEGRAM WARNING] Erro ao editar quiz markdown: {e}")
            # Fallback para texto plano se falhar
            await query.edit_message_text(
                orig_text + f"\n\n💡 Resposta Revelada:\n{answer}"
            )

        # Limpa cache para liberar memória
        context.bot_data["quiz_answers"].pop(key, None)


# ─── Message Handler (Escuta Ativa / Chat Livre) ─────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Monitora conversas em grupo e privadas.
    Em grupos, responde apenas quando o bot é mencionado ou respondido.
    """
    message = update.message
    if not message or not message.text:
        return

    is_private = update.effective_chat.type == "private"
    is_mentioned = False
    bot_username = context.bot.username

    # Verifica menção explícita
    if f"@{bot_username}" in message.text:
        is_mentioned = True

    # Verifica se responderam a uma mensagem enviada pelo bot
    if message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id:
        is_mentioned = True

    # Ignora se for grupo e não houver menção/reply
    if not is_private and not is_mentioned:
        return

    # Limpa a menção da query para não influenciar a IA
    query = message.text.replace(f"@{bot_username}", "").strip()
    if not query:
        return

    # Trata a mensagem livre como um ask padrão
    await run_ai_command(
        update,
        context,
        SYSTEM_PROMPT,
        "Conversa Livre",
        query=query
    )


# ─── Inicialização do Bot (Async Runner) ──────────────────────────────────────

async def start_telegram_bot(discord_bot: discord.Client):
    """
    Carrega o Token do Telegram e acopla a escuta assíncrona
    ao loop de eventos em andamento.
    """
    token = os.getenv("TELEGRAM_TOKEN")
    if not token or token == "seu_token_telegram_aqui":
        print("[TELEGRAM] TELEGRAM_TOKEN nao configurado ou padrao. Ignorando startup do Telegram.")
        return

    print("[TELEGRAM] Inicializando bot do Telegram...")
    
    # Constrói o Application
    application = ApplicationBuilder().token(token).build()

    # Passa as instâncias necessárias no bot_data
    application.bot_data["discord_bot"] = discord_bot
    application.bot_data["quiz_answers"] = {}

    # Registra Handlers de Comandos
    application.add_handler(CommandHandler("start", cmd_ajuda))
    application.add_handler(CommandHandler("ajuda", cmd_ajuda))
    application.add_handler(CommandHandler("ask", cmd_ask))
    application.add_handler(CommandHandler("explain", cmd_explain))
    application.add_handler(CommandHandler("code", cmd_code))
    application.add_handler(CommandHandler("dataset", cmd_dataset))
    application.add_handler(CommandHandler("roadmap", cmd_roadmap))
    application.add_handler(CommandHandler("quiz", cmd_quiz))

    # Registra Handlers de Cliques Inline
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Registra Handler de Conversas Gerais
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Inicializa e liga o Updater por polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Salva referência no objeto discord para finalização limpa no close()
    discord_bot.telegram_app = application
    print("[TELEGRAM] Bot iniciado com sucesso e ouvindo atualizacoes!")
