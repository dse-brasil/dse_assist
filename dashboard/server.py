import os
import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
from aiohttp import web
from dotenv import load_dotenv
import dotenv

from ai_providers.security_logger import verify_audit_trail, AUDIT_LOG_FILE

# Host e Porta do dashboard configuráveis pelo .env
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "127.0.0.1")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "5000"))

# Lista de variáveis confidenciais que serão mascaradas
SENSITIVE_KEYS = ["DISCORD_TOKEN", "AI_API_KEY", "CHROMA_API_KEY"]


def mask_value(key: str, val: str) -> str:
    """Retorna a chave mascarada mostrando apenas os primeiros e últimos 4 caracteres."""
    if not val or val.strip() == "":
        return ""
    # Se for um valor com placeholder padrão, não mascara
    if "sua_chave" in val or "seu_token" in val or "seu_tenant" in val:
        return val
    
    val = val.strip()
    if len(val) <= 8:
        return "••••"
    return f"{val[:4]}...{val[-4:]}"


def _get_chroma_counts() -> Dict[str, int]:
    """Retorna a contagem de itens nas coleções do Chroma Cloud."""
    counts = {"knowledge_base": 0, "discord_history": 0}
    try:
        from ai_providers.chroma_client import get_client, COLLECTION_KNOWLEDGE, COLLECTION_DISCORD
        # Apenas tenta conectar se a chave de API estiver configurada
        api_key = os.getenv("CHROMA_API_KEY", "").strip()
        if api_key and api_key != "sua_api_key_aqui":
            client = get_client()
            # dse_knowledge_base
            try:
                col_kb = client.get_collection(COLLECTION_KNOWLEDGE)
                counts["knowledge_base"] = col_kb.count()
            except Exception:
                pass
            
            # dse_discord_history
            try:
                col_dh = client.get_collection(COLLECTION_DISCORD)
                counts["discord_history"] = col_dh.count()
            except Exception:
                pass
    except Exception as e:
        print(f"[DASHBOARD] Erro ao obter contagens do Chroma: {e}")
    return counts


class DashboardServer:
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        self.runner = None
        self.setup_routes()

    def setup_routes(self):
        # Rotas da SPA e estáticos
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_static('/static/', path='dashboard/static', name='static')

        # API Endpoints
        self.app.router.add_get('/api/status', self.handle_status)
        self.app.router.add_get('/api/config', self.handle_get_config)
        self.app.router.add_post('/api/config', self.handle_post_config)
        self.app.router.add_get('/api/stats', self.handle_stats)
        self.app.router.add_get('/api/logs', self.handle_logs)
        self.app.router.add_post('/api/verify', self.handle_verify)

    # ── Helpers SPA ───────────────────────────────────────────────────────────

    async def handle_index(self, request):
        index_path = os.path.join("dashboard", "static", "index.html")
        if not os.path.exists(index_path):
            return web.Response(text="index.html não encontrado no diretório dashboard/static.", status=404)
        return web.FileResponse(index_path)

    # ── API Handlers ──────────────────────────────────────────────────────────

    async def handle_status(self, request):
        """Retorna o estado atual do bot e conexões."""
        uptime_str = "-"
        if hasattr(self.bot, 'start_time') and self.bot.start_time:
            delta = datetime.now(timezone.utc) - self.bot.start_time
            # Formata duração de forma legível
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            uptime_parts = []
            if days > 0:
                uptime_parts.append(f"{days}d")
            if hours > 0:
                uptime_parts.append(f"{hours}h")
            if minutes > 0:
                uptime_parts.append(f"{minutes}m")
            uptime_parts.append(f"{seconds}s")
            uptime_str = " ".join(uptime_parts)

        latency = self.bot.latency * 1000 if hasattr(self.bot, 'latency') and self.bot.latency else 0
        ai_provider_name = self.bot.ai_provider.name if getattr(self.bot, 'ai_provider', None) else "Nenhum"

        # Executa contagem do Chroma em pool de threads para evitar bloqueios de rede
        loop = asyncio.get_event_loop()
        chroma_counts = await loop.run_in_executor(None, _get_chroma_counts)

        telegram_status = "OFFLINE"
        telegram_bot_name = "-"
        if hasattr(self.bot, "telegram_app") and self.bot.telegram_app:
            if self.bot.telegram_app.updater and self.bot.telegram_app.updater.running:
                telegram_status = "ONLINE"
            else:
                telegram_status = "INITIALIZED"
            if self.bot.telegram_app.bot:
                try:
                    telegram_bot_name = f"@{self.bot.telegram_app.bot.username}"
                except Exception:
                    pass

        status_data = {
            "bot_name": str(self.bot.user) if self.bot.user else "Carregando...",
            "bot_status": "ONLINE" if self.bot.is_ready() else "OFFLINE",
            "latency": latency,
            "guild_count": len(self.bot.guilds) if hasattr(self.bot, 'guilds') else 0,
            "uptime": uptime_str,
            "ai_provider": ai_provider_name,
            "chroma_kb_count": chroma_counts["knowledge_base"],
            "chroma_dh_count": chroma_counts["discord_history"],
            "telegram_status": telegram_status,
            "telegram_bot_name": telegram_bot_name,
        }
        return web.json_response(status_data)

    async def handle_get_config(self, request):
        """Lê variáveis do .env e envia mascarado."""
        dotenv_path = ".env"
        if not os.path.exists(dotenv_path):
            return web.json_response({})

        # Carrega os valores brutos do arquivo .env
        config = dotenv.dotenv_values(dotenv_path)
        
        masked_config = {}
        for k, v in config.items():
            if k in SENSITIVE_KEYS:
                # Retorna chave com sufixo _MASKED e oculta o original
                masked_config[f"{k}_MASKED"] = mask_value(k, v)
            else:
                masked_config[k] = v

        return web.json_response(masked_config)

    async def handle_post_config(self, request):
        """Atualiza o .env e faz o Hot Reload do provedor de IA."""
        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"error": "Payload JSON inválido"}, status=400)

        dotenv_path = ".env"
        
        # Lê configurações brutas atuais
        current_config = dotenv.dotenv_values(dotenv_path) if os.path.exists(dotenv_path) else {}

        # Grava os novos valores no arquivo .env
        for k, v in payload.items():
            # Se a chave for sensitiva e o usuário enviou string vazia ou bolinhas,
            # significa que ele manteve a chave antiga (não alterou). Ignora.
            if k in SENSITIVE_KEYS and (not v or v.strip() == "" or v.startswith("••")):
                continue
            
            # Converte valores booleanos para strings
            if isinstance(v, bool):
                v_str = "true" if v else "false"
            else:
                v_str = str(v).strip()
            
            try:
                dotenv.set_key(dotenv_path, k, v_str)
            except Exception as e:
                return web.json_response({"error": f"Erro ao escrever .env para {k}: {e}"}, status=500)

        # Recarrega as variáveis de ambiente no processo Python
        load_dotenv(dotenv_path, override=True)

        # ─── HOT RELOAD DA IA ──────────────────────────────────────────────────
        try:
            from ai_providers import get_provider
            from ai_providers.rag_provider import wrap_with_rag

            # Factory do provedor de IA base
            base_provider = get_provider()
            # Envolve com RAG
            new_provider = wrap_with_rag(base_provider)
            
            # Atualiza a referência no bot globalmente!
            self.bot.ai_provider = new_provider
            print(f"[HOT RELOAD] IA reinicializada com sucesso: {new_provider.name}")
        except Exception as e:
            print(f"[HOT RELOAD ERROR] Falha ao reconfigurar provedor de IA: {e}")
            # Retorna o erro amigável ao usuário para ele saber que a chave/modelo está errada
            return web.json_response({"error": f"IA salva no arquivo .env, mas falhou ao inicializar: {e}"}, status=400)

        return web.json_response({"success": True})

    async def handle_stats(self, request):
        """Analisa o security_audit.jsonl e calcula volumetria de indicadores."""
        stats = {
            "total_req": 0,
            "approved_req": 0,
            "rejected_req": 0,
            "error_req": 0,
            "top_users": [],
            "top_commands": [],
            "daily_data": []
        }

        if not os.path.exists(AUDIT_LOG_FILE):
            return web.json_response(stats)

        user_counts = {}
        cmd_counts = {}
        daily_series = {}

        try:
            # Executa leitura assíncrona não bloqueante
            loop = asyncio.get_event_loop()
            lines = await loop.run_in_executor(None, self._read_log_lines)
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                stats["total_req"] += 1
                status = data.get("status", "ERROR").upper()
                
                if status == "APPROVED":
                    stats["approved_req"] += 1
                elif status == "REJECTED":
                    stats["rejected_req"] += 1
                else:
                    stats["error_req"] += 1

                # Contagem de Usuários
                username = data.get("username", "desconhecido")
                platform = data.get("platform", "discord").lower()
                user_key = f"{username} ({platform.capitalize()})"
                user_counts[user_key] = user_counts.get(user_key, 0) + 1

                # Contagem de Comandos
                cmd = data.get("command", "desconhecido")
                cmd_key = f"{cmd} ({platform.capitalize()})"
                cmd_counts[cmd_key] = cmd_counts.get(cmd_key, 0) + 1

                # Série Temporal Diária
                ts_str = data.get("timestamp", "")
                if ts_str:
                    try:
                        # Extrai a data YYYY-MM-DD
                        date_key = ts_str.split("T")[0]
                        if date_key not in daily_series:
                            daily_series[date_key] = {"approved": 0, "rejected": 0, "errors": 0}
                        
                        if status == "APPROVED":
                            daily_series[date_key]["approved"] += 1
                        elif status == "REJECTED":
                            daily_series[date_key]["rejected"] += 1
                        else:
                            daily_series[date_key]["errors"] += 1
                    except Exception:
                        pass

            # Ordena e seleciona os Top 5 Usuários
            sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            stats["top_users"] = [{"username": k, "count": v} for k, v in sorted_users]

            # Ordena e seleciona os Top 5 Comandos
            sorted_cmds = sorted(cmd_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            stats["top_commands"] = [{"command": k, "count": v} for k, v in sorted_cmds]

            # Formata série diária ordenada por data (últimos 14 dias)
            sorted_dates = sorted(daily_series.keys())[-14:]
            stats["daily_data"] = [
                {
                    "date": d,
                    "approved": daily_series[d]["approved"],
                    "rejected": daily_series[d]["rejected"],
                    "errors": daily_series[d]["errors"]
                }
                for d in sorted_dates
            ]

        except Exception as e:
            print(f"[DASHBOARD] Erro ao processar estatísticas: {e}")

        return web.json_response(stats)

    async def handle_logs(self, request):
        """Retorna os últimos 100 logs registrados no ledger de auditoria."""
        logs = []
        if not os.path.exists(AUDIT_LOG_FILE):
            return web.json_response(logs)

        try:
            loop = asyncio.get_event_loop()
            lines = await loop.run_in_executor(None, self._read_log_lines)
            
            # Pega as últimas 100 linhas e inverte para ordem cronológica reversa
            for line in reversed(lines[-100:]):
                line = line.strip()
                if not line:
                    continue
                try:
                    logs.append(json.loads(line))
                except Exception:
                    continue
        except Exception as e:
            print(f"[DASHBOARD] Erro ao ler logs do ledger: {e}")

        return web.json_response(logs)

    async def handle_verify(self, request):
        """Verifica a integridade criptográfica da cadeia de hashes do ledger."""
        loop = asyncio.get_event_loop()
        is_valid = await loop.run_in_executor(None, verify_audit_trail)
        return web.json_response({"valid": is_valid})

    # ── Métodos Auxiliares Síncronos para Thread Pool ────────────────────────

    def _read_log_lines(self) -> List[str]:
        """Lê todas as linhas do arquivo de log de segurança de forma síncrona."""
        if not os.path.exists(AUDIT_LOG_FILE):
            return []
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            return f.readlines()


# ─── Inicializador do Servidor Web ────────────────────────────────────────────

async def start_dashboard(bot):
    """Inicializa e inicia o servidor web na porta e host definidos."""
    server = DashboardServer(bot)
    
    # Configura o Runner do aiohttp
    runner = web.AppRunner(server.app)
    server.runner = runner
    await runner.setup()
    
    # Associa a porta e host
    site = web.TCPSite(runner, DASHBOARD_HOST, DASHBOARD_PORT)
    await site.start()
    
    # Salva a referência do site e runner no bot para encerramento limpo
    bot.dashboard_runner = runner
    print(f"[DASHBOARD] Painel Web rodando em http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
