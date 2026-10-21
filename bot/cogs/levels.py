"""📈 Níveis — ganha XP a conversar; o painel mostra o ranking."""

from __future__ import annotations

import random
import time

import discord
from discord.ext import commands


class Levels(commands.Cog):
    """Sistema de XP / níveis."""

    def __init__(self, bot):
        self.bot = bot
        self._cooldown: dict[tuple[int, int], float] = {}

    @commands.Cog.listener()
    async def on_message(self, mensagem: discord.Message):
        if mensagem.author.bot or not mensagem.guild:
            return
        chave = (mensagem.guild.id, mensagem.author.id)
        agora = time.time()
        if agora - self._cooldown.get(chave, 0) < 60:  # 1 XP por minuto por utilizador
            return
        self._cooldown[chave] = agora
        registo = self.bot.storage.add_xp(
            mensagem.guild.id, mensagem.author.id, mensagem.author.display_name, random.randint(5, 15)
        )
        await self.bot.storage.gravar()
        # anúncio de subida de nível simples
        if registo["nivel"] > 0 and registo["xp"] % 100 < 15:
            try:
                await mensagem.channel.send(
                    f"🎉 {mensagem.author.mention} subiu para o **nível {registo['nivel']}**!",
                    delete_after=8,
                )
            except discord.HTTPException:
                pass

    @commands.command(name="rank", aliases=["nivel"])
    async def rank(self, ctx: commands.Context, membro: discord.Member | None = None):
        """Mostra o teu nível. Uso: !rank [@membro]"""
        membro = membro or ctx.author
        registo = self.bot.storage.xp(ctx.guild.id).get(str(membro.id), {"xp": 0, "nivel": 0})
        embed = discord.Embed(
            title=f"📈 {membro.display_name}",
            description=f"Nível **{registo.get('nivel', 0)}** • {registo.get('xp', 0)} XP",
            color=discord.Color.from_str("#4af0c0"),
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Levels(bot))
