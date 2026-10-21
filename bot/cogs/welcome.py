"""🎶 Boas-vindas — dá as boas-vindas a quem entra e atribui o cargo automático."""

from __future__ import annotations

import discord
from discord.ext import commands


def montar_embed(guild: discord.Guild, membro: discord.Member, cfg: dict) -> discord.Embed:
    mensagem = cfg.get("mensagem") or "🎶 {membro} entrou no palco! O show vai começar! 💙"
    total = guild.member_count or 0
    texto = (
        mensagem.replace("{membro}", membro.mention)
        .replace("{nome}", str(membro))
        .replace("{servidor}", guild.name)
        .replace("{total}", str(total))
    )
    embed = discord.Embed(description=texto, color=discord.Color.from_str("#39c5bb"))
    if cfg.get("imagem", True):
        embed.set_thumbnail(url=membro.display_avatar.url)
    embed.set_footer(text=f"{guild.name} • membro nº {total}")
    return embed


class Welcome(commands.Cog):
    """Sistema de boas-vindas."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, membro: discord.Member):
        guild = membro.guild
        cfg = self.bot.storage.boasvindas(guild.id)

        # cargo automático (por nome, como no painel)
        nome_cargo = (cfg.get("cargo") or "").strip()
        if nome_cargo:
            cargo = discord.utils.get(guild.roles, name=nome_cargo)
            if cargo is not None:
                try:
                    await membro.add_roles(cargo, reason="Cargo automático de boas-vindas")
                except discord.Forbidden:
                    pass

        canal = None
        if cfg.get("canal_id"):
            try:
                canal = guild.get_channel(int(cfg["canal_id"]))
            except (TypeError, ValueError):
                canal = None
        if canal is not None:
            try:
                await canal.send(embed=montar_embed(guild, membro, cfg))
                await self.bot.storage.log(f"Boas-vindas enviadas a {membro} em {guild.name}")
            except discord.Forbidden:
                pass


async def setup(bot):
    await bot.add_cog(Welcome(bot))
