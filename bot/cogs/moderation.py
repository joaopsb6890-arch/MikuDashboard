"""🧹 Moderação — limpeza rápida de mensagens."""

from __future__ import annotations

import discord
from discord.ext import commands


class Moderation(commands.Cog):
    """Sistema de moderação rápida."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="limpar", aliases=["clear", "purge"])
    @commands.has_permissions(manage_messages=True)
    async def limpar(self, ctx: commands.Context, quantidade: int = 10):
        """Apaga N mensagens (1–100). Uso: !limpar 20"""
        quantidade = max(1, min(100, quantidade))
        apagadas = await ctx.channel.purge(limit=quantidade + 1)
        aviso = await ctx.send(f"🧹 {len(apagadas) - 1} mensagens apagadas.")
        await self.bot.storage.log(
            f"{len(apagadas) - 1} mensagens apagadas por {ctx.author} em #{ctx.channel.name}"
        )
        try:
            await aviso.delete(delay=4)
        except discord.Forbidden:
            pass


async def setup(bot):
    await bot.add_cog(Moderation(bot))
