"""🎤 bot.py — o cliente Discord da Miku."""

from __future__ import annotations

import time

import discord
from discord.ext import commands

from .cogs import EXTENSOES


class MikuBot(commands.Bot):
    def __init__(self, storage, config):
        intents = discord.Intents.none()
        intents.guilds = True
        intents.members = config.intent_members
        intents.message_content = config.intent_message_content
        intents.presences = config.intent_presences

        super().__init__(
            command_prefix=config.command_prefix,
            intents=intents,
            help_command=None,
        )
        self.storage = storage
        self.config = config
        self.launch_time = time.time()

    async def setup_hook(self):
        for extensao in EXTENSOES:
            try:
                await self.load_extension(extensao)
            except Exception as erro:  # noqa: BLE001
                print(f"⚠️  Não consegui carregar {extensao}: {erro}")

    async def on_ready(self):
        print(f"✅ Miku online como {self.user} (id {self.user.id})")
        print(f"   Servidores: {len(self.guilds)}")
        await self.storage.log(f"Miku online como {self.user}")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Não tens permissão para isso.")
            return
        await ctx.send(f"⚠️ Erro: {error}")
