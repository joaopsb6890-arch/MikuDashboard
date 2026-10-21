"""
⚙️  config.py — carrega as credenciais do Discord Developer Portal.

Todas as informações que o painel precisa para "reconhecer o bot" vêm daqui,
lidas do ficheiro `.env` (ver `.env.example`).

Preenche o `.env` com o que encontras em https://discord.com/developers/applications
  • General Information  → Application ID, Public Key
  • OAuth2               → Client ID, Client Secret
  • Bot                  → Token (Reset Token)
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv é opcional
    def load_dotenv(*_args, **_kwargs):
        return False


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# Carrega o .env que estiver na pasta do bot ou na raiz do projeto.
for _candidate in (BASE_DIR / ".env", ROOT_DIR / ".env"):
    if _candidate.exists():
        load_dotenv(_candidate)
        break
else:
    load_dotenv()  # tenta o .env do diretório atual


def _bool(valor: str | None, default: bool = False) -> bool:
    if valor is None:
        return default
    return valor.strip().lower() in {"1", "true", "yes", "sim", "on", "y"}


class Config:
    """Todas as credenciais e definições do bot/painel."""

    # ── Discord Developer Portal ──────────────────────────────────────────
    application_id: str = os.getenv("DISCORD_APPLICATION_ID", "").strip()
    public_key: str = os.getenv("DISCORD_PUBLIC_KEY", "").strip()
    bot_token: str = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    client_id: str = os.getenv("DISCORD_CLIENT_ID", "").strip()
    client_secret: str = os.getenv("DISCORD_CLIENT_SECRET", "").strip()

    # ── Painel web ────────────────────────────────────────────────────────
    dashboard_token: str = os.getenv("DASHBOARD_TOKEN", "").strip()
    web_host: str = os.getenv("WEB_HOST", "0.0.0.0").strip()
    web_port: int = int(os.getenv("WEB_PORT", "8787") or "8787")
    auto_connect: bool = _bool(os.getenv("AUTO_CONNECT"), True)
    data_dir: Path = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data"))).expanduser()

    # ── Prefixo de comandos de chat ───────────────────────────────────────
    command_prefix: str = os.getenv("COMMAND_PREFIX", "!").strip() or "!"

    # ── Intents (têm de estar ligados no Developer Portal → Bot) ──────────
    intent_members: bool = _bool(os.getenv("INTENT_MEMBERS"), True)
    intent_message_content: bool = _bool(os.getenv("INTENT_MESSAGE_CONTENT"), True)
    intent_presences: bool = _bool(os.getenv("INTENT_PRESENCES"), False)

    @classmethod
    def load(cls) -> "Config":
        """Valida e finaliza a configuração. Gera um token de painel se faltar."""
        if not cls.dashboard_token:
            cls.dashboard_token = secrets.token_urlsafe(24)
        # O Client ID do OAuth pode ser o próprio Application ID.
        if not cls.client_id and cls.application_id:
            cls.client_id = cls.application_id
        cls.data_dir.mkdir(parents=True, exist_ok=True)
        return cls

    @classmethod
    def resumo(cls) -> dict:
        """Resumo seguro (sem segredos) para mostrar no arranque."""
        return {
            "application_id": cls.application_id or "(não definido)",
            "client_id": cls.client_id or "(não definido)",
            "public_key": "definida" if cls.public_key else "(não definida)",
            "bot_token": "definida" if cls.bot_token else "(NÃO DEFINIDA)",
            "client_secret": "definido" if cls.client_secret else "(não definido)",
            "dashboard_token": cls.dashboard_token,
            "web": f"http://{cls.web_host}:{cls.web_port}",
            "auto_connect": cls.auto_connect,
        }
