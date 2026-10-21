"""📢 Anúncios — envio de embeds (também usado pelo painel)."""

from __future__ import annotations

import discord
from discord.ext import commands


class Announcements(commands.Cog):
    """Sistema de anúncios em embed."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="anunciar")
    @commands.has_permissions(manage_messages=True)
    async def anunciar(self, ctx: commands.Context, *, texto: str):
        """Envia um anúncio em embed. Uso: !anunciar Título | Descrição"""
        if "|" in texto:
            titulo, descricao = (parte.strip() for parte in texto.split("|", 1))
        else:
            titulo, descricao = "📢 Anúncio", texto.strip()
        embed = discord.Embed(
            title=titulo, description=descricao, color=discord.Color.from_str("#39c5bb")
        )
        embed.set_footer(text="Hatsune Miku Bot 🎤")
        await ctx.send(embed=embed)
        await self.bot.storage.log(f"Anúncio enviado por {ctx.author} em {ctx.guild.name}")
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass


async def setup(bot):
    await bot.add_cog(Announcements(bot))
