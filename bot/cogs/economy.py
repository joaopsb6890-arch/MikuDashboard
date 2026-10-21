"""💰 Economia — moedas da Miku (daily, saldo). O painel mostra o ranking."""

from __future__ import annotations

import random
import time

import discord
from discord.ext import commands


class Economy(commands.Cog):
    """Sistema de economia simples."""

    def __init__(self, bot):
        self.bot = bot
        self._daily: dict[tuple[int, int], float] = {}

    @commands.command(name="daily")
    async def daily(self, ctx: commands.Context):
        """Recebe a tua recompensa diária de moedas."""
        chave = (ctx.guild.id, ctx.author.id)
        agora = time.time()
        if agora - self._daily.get(chave, 0) < 86400:
            restante = int(86400 - (agora - self._daily[chave]))
            horas, minutos = divmod(restante // 60, 60)
            await ctx.send(f"⏳ Já recebeste hoje! Volta dentro de **{horas}h {minutos}m**.")
            return
        self._daily[chave] = agora
        ganho = random.randint(50, 150)
        registo = self.bot.storage.add_saldo(
            ctx.guild.id, ctx.author.id, ctx.author.display_name, ganho
        )
        await self.bot.storage.gravar()
        await ctx.send(f"💰 Recebeste **{ganho} moedas**! Saldo: **{registo['saldo']}** 🎶")

    @commands.command(name="saldo", aliases=["carteira", "coins"])
    async def saldo(self, ctx: commands.Context, membro: discord.Member | None = None):
        """Mostra o teu saldo. Uso: !saldo [@membro]"""
        membro = membro or ctx.author
        registo = self.bot.storage.economia(ctx.guild.id).get(str(membro.id), {"saldo": 0})
        await ctx.send(f"💰 **{membro.display_name}** tem **{registo.get('saldo', 0)} moedas**.")


async def setup(bot):
    await bot.add_cog(Economy(bot))
