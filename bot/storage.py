"""
💾 storage.py — persistência simples em JSON.

Guarda tudo o que o painel configura: boas-vindas, verificação, contadores,
XP, economia e os registos (logs). É seguro para uso assíncrono (lock) e
grava de forma atómica para não corromper o ficheiro.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any


def _guild_padrao() -> dict[str, Any]:
    return {
        "boasvindas": {"canal_id": "", "mensagem": "", "cargo": "", "imagem": True},
        "verificacao": {"cargo_id": "", "canal_id": "", "mensagem_id": ""},
        "contadores": [],  # [{canal_id, modelo, nome}]
        "xp": {},          # {user_id: {xp, nivel, nome}}
        "economia": {},    # {user_id: {saldo, nome}}
    }


class Storage:
    def __init__(self, caminho: Path):
        self.caminho = Path(caminho)
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self.dados: dict[str, Any] = {"guilds": {}, "logs": []}
        self._carregar()

    # ── ficheiro ──────────────────────────────────────────────────────────
    def _carregar(self) -> None:
        if self.caminho.exists():
            try:
                self.dados = json.loads(self.caminho.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self.dados = {"guilds": {}, "logs": []}
        self.dados.setdefault("guilds", {})
        self.dados.setdefault("logs", [])

    def _gravar_sync(self) -> None:
        tmp = self.caminho.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(self.dados, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        tmp.replace(self.caminho)

    async def gravar(self) -> None:
        async with self._lock:
            self._gravar_sync()

    # ── guildas ───────────────────────────────────────────────────────────
    def guild(self, guild_id: int | str) -> dict[str, Any]:
        gid = str(guild_id)
        g = self.dados["guilds"].setdefault(gid, _guild_padrao())
        # garante chaves novas em bases antigas
        base = _guild_padrao()
        for chave, valor in base.items():
            g.setdefault(chave, valor)
        return g

    # ── logs ──────────────────────────────────────────────────────────────
    async def log(self, mensagem: str) -> None:
        carimbo = time.strftime("%H:%M:%S")
        self.dados["logs"].append(f"[{carimbo}] {mensagem}")
        # mantém só os últimos 200 registos
        self.dados["logs"] = self.dados["logs"][-200:]
        await self.gravar()

    def logs(self) -> list[str]:
        return list(self.dados["logs"])

    # ── boas-vindas ───────────────────────────────────────────────────────
    def boasvindas(self, guild_id: int | str) -> dict[str, Any]:
        return self.guild(guild_id)["boasvindas"]

    # ── verificação ───────────────────────────────────────────────────────
    def verificacao(self, guild_id: int | str) -> dict[str, Any]:
        return self.guild(guild_id)["verificacao"]

    # ── contadores ────────────────────────────────────────────────────────
    def contadores(self, guild_id: int | str) -> list[dict[str, Any]]:
        return self.guild(guild_id)["contadores"]

    # ── XP / níveis ───────────────────────────────────────────────────────
    def xp(self, guild_id: int | str) -> dict[str, Any]:
        return self.guild(guild_id)["xp"]

    def add_xp(self, guild_id: int | str, user_id: int, nome: str, quantidade: int) -> dict:
        registo = self.xp(guild_id).setdefault(str(user_id), {"xp": 0, "nivel": 0, "nome": nome})
        registo["nome"] = nome
        registo["xp"] += quantidade
        registo["nivel"] = int((registo["xp"] // 100) ** 0.5)
        return registo

    def leaderboard_xp(self, guild_id: int | str, limite: int = 10) -> list[dict]:
        itens = list(self.xp(guild_id).values())
        itens.sort(key=lambda r: r.get("xp", 0), reverse=True)
        return itens[:limite]

    # ── economia ──────────────────────────────────────────────────────────
    def economia(self, guild_id: int | str) -> dict[str, Any]:
        return self.guild(guild_id)["economia"]

    def add_saldo(self, guild_id: int | str, user_id: int, nome: str, quantidade: int) -> dict:
        registo = self.economia(guild_id).setdefault(str(user_id), {"saldo": 0, "nome": nome})
        registo["nome"] = nome
        registo["saldo"] = max(0, registo["saldo"] + quantidade)
        return registo

    def leaderboard_economia(self, guild_id: int | str, limite: int = 10) -> list[dict]:
        itens = list(self.economia(guild_id).values())
        itens.sort(key=lambda r: r.get("saldo", 0), reverse=True)
        return itens[:limite]
