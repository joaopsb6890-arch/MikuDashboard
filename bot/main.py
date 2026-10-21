"""
🚀 main.py — arranca tudo com um único comando.

    python -m bot.main

Faz três coisas ao mesmo tempo:
  1. Liga o bot ao Discord com o teu Bot Token (Developer Portal).
  2. Sobe o servidor web que serve o PAINEL.
  3. Serve a API e AUTO-CONECTA o painel (o bot é reconhecido sozinho).

Depois é só abrir o endereço mostrado no terminal. 💙
"""

from __future__ import annotations

import asyncio
import sys

from aiohttp import web

from .bot import MikuBot
from .config import Config
from .storage import Storage
from .web import criar_app


def _banner(config: Config) -> None:
    resumo = Config.resumo()
    print("\n" + "═" * 62)
    print("  🎤  HATSUNE MIKU BOT — Painel + API + Discord")
    print("═" * 62)
    print(f"  Application ID : {resumo['application_id']}")
    print(f"  Client ID      : {resumo['client_id']}")
    print(f"  Public Key     : {resumo['public_key']}")
    print(f"  Bot Token      : {resumo['bot_token']}")
    print(f"  Client Secret  : {resumo['client_secret']}")
    print(f"  Token do painel: {resumo['dashboard_token']}")
    print(f"  Auto-conectar  : {resumo['auto_connect']}")
    print("─" * 62)
    print(f"  🌐 Abre o painel em:  http://localhost:{config.web_port}")
    print("═" * 62 + "\n")


async def main() -> None:
    config = Config.load()
    _banner(config)

    if not config.bot_token:
        print("❌ Falta o DISCORD_BOT_TOKEN no ficheiro .env.")
        print("   Vai a https://discord.com/developers/applications → Bot → Reset Token")
        print("   e cola-o no .env. Depois volta a correr: python -m bot.main")
        sys.exit(1)

    storage = Storage(config.data_dir / "miku.json")
    bot = MikuBot(storage, config)

    app = criar_app(bot, storage)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.web_host, config.web_port)
    await site.start()
    print(f"🌐 Servidor web no ar em http://{config.web_host}:{config.web_port}")

    try:
        await bot.start(config.bot_token)
    finally:
        await runner.cleanup()


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Até à próxima!")


if __name__ == "__main__":
    run()
