"""
Security Logger — Auditoria Imutável (WORM) para o DSE Bot.

Registra cada prompt enviado, contexto recuperado e resposta em um ledger local.
Cada entrada possui um hash SHA-256 calculado sobre os dados da entrada e o hash anterior.
Qualquer tentativa de alterar registros retroativamente invalidará a cadeia de hashes.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, List

AUDIT_LOG_FILE = "security_audit.jsonl"


def get_last_entry_hash(filepath: str = AUDIT_LOG_FILE) -> str:
    """Retorna o hash do último registro inserido ou 64 zeros se for o primeiro."""
    if not os.path.exists(filepath):
        return "0" * 64
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return "0" * 64
            # Busca a última linha não vazia
            for line in reversed(lines):
                line = line.strip()
                if line:
                    data = json.loads(line)
                    return data.get("hash", "0" * 64)
    except Exception as e:
        print(f"[SECURITY] Erro ao ler último hash: {e}")
    return "0" * 64


def log_interaction(
    user_id: int,
    username: str,
    channel: str,
    command: str,
    prompt: str,
    retrieved_sources: List[str],
    response: str,
    status: str,
    filepath: str = AUDIT_LOG_FILE,
    platform: str = "discord",
) -> str:
    """
    Grava uma entrada no log de auditoria conectada por hash ao registro anterior.
    Retorna o hash gerado para esta entrada.
    """
    prev_hash = get_last_entry_hash(filepath)
    timestamp = datetime.now(timezone.utc).isoformat()

    # Prepara o dicionário de campos estáveis (exclui o campo 'hash')
    entry = {
        "timestamp": timestamp,
        "user_id": user_id,
        "username": username,
        "channel": channel,
        "command": command,
        "prompt": prompt,
        "retrieved_sources": retrieved_sources,
        "response": response,
        "status": status,
        "platform": platform,
        "prev_hash": prev_hash,
    }

    # Serializa de forma ordenada para consistência do hash
    serialized = json.dumps(entry, sort_keys=True, ensure_ascii=False)
    entry_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    entry["hash"] = entry_hash

    try:
        # Garante a escrita imediata em modo append
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[SECURITY] Erro crítico ao salvar log de auditoria: {e}")

    return entry_hash


def verify_audit_trail(filepath: str = AUDIT_LOG_FILE) -> bool:
    """
    Verifica se a integridade de toda a cadeia de logs foi mantida.
    Retorna True se todos os hashes baterem, False caso contrário.
    """
    if not os.path.exists(filepath):
        return True

    expected_prev_hash = "0" * 64
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                
                # Armazena o hash registrado
                recorded_hash = data.get("hash")
                recorded_prev_hash = data.get("prev_hash")
                
                # Valida se o prev_hash bate com o hash esperado do registro anterior
                if recorded_prev_hash != expected_prev_hash:
                    print(f"[SECURITY] Quebra de cadeia no registro {idx}: prev_hash inconsistente.")
                    return False
                
                # Recalcula o hash da entrada
                entry_data = {k: v for k, v in data.items() if k != "hash"}
                serialized = json.dumps(entry_data, sort_keys=True, ensure_ascii=False)
                calculated_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
                
                if calculated_hash != recorded_hash:
                    print(f"[SECURITY] Quebra de cadeia no registro {idx}: hash recalculado não bate.")
                    return False
                
                expected_prev_hash = recorded_hash
        return True
    except Exception as e:
        print(f"[SECURITY] Falha na validação do log: {e}")
        return False
