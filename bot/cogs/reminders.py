"""⏰ Lembretes — agenda um aviso para daqui a N minutos."""

from __future__ import annotations

import asyncio

import discord
from discord.ext import commands


class Reminders(commands.Cog):
    """Sistema de lembretes agendados."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lembrar")
    async def lembrar(self, ctx: commands.Context, minutos: int, *, texto: str):
        """Uso: !lembrar 30 Hora do evento!"""
        minutos = max(1, min(1440, minutos))

        async def _disparar():
            await asyncio.sleep(minutos * 60)
            embed = discord.Embed(
                title="⏰ Lembrete!", description=texto, color=discord.Color.from_str("#57e6ff")
            )
            try:
                await ctx.send(content=ctx.author.mention, embed=embed)
                await self.bot.storage.log(f"Lembrete disparado em #{ctx.channel.name}")
            except discord.HTTPException:
                pass

        asyncio.create_task(_disparar())
        await ctx.send(f"⏰ Ok! Vou lembrar-te daqui a **{minutos} min**.")
        await self.bot.storage.log(f"Lembrete agendado ({minutos} min) por {ctx.author}")


async def setup(bot):
    await bot.add_cog(Reminders(bot))
