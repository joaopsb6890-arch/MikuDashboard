"""📊 Contadores ao vivo — canais de voz que se renomeiam sozinhos."""

from __future__ import annotations

import discord
from discord.ext import commands, tasks


def render(modelo: str, guild: discord.Guild) -> str:
    humanos = sum(1 for m in guild.members if not m.bot)
    bots = sum(1 for m in guild.members if m.bot)
    online = sum(1 for m in guild.members if m.status != discord.Status.offline)
    texto = (
        modelo.replace("{total}", str(guild.member_count or 0))
        .replace("{humanos}", str(humanos))
        .replace("{bots}", str(bots))
        .replace("{online}", str(online))
        .replace("{cargos}", str(max(0, len(guild.roles) - 1)))
    )
    return texto[:100]


class Counters(commands.Cog):
    """Mantém os canais-contador sincronizados com os números do servidor."""

    def __init__(self, bot):
        self.bot = bot
        self.atualizar.start()

    def cog_unload(self):
        self.atualizar.cancel()

    @tasks.loop(minutes=5)
    async def atualizar(self):
        for guild in self.bot.guilds:
            for contador in list(self.bot.storage.contadores(guild.id)):
                try:
                    canal = guild.get_channel(int(contador["canal_id"]))
                except (TypeError, ValueError):
                    canal = None
                if canal is None:
                    continue
                novo = render(contador.get("modelo", ""), guild)
                if canal.name != novo:
                    try:
                        await canal.edit(name=novo, reason="Contador automático")
                    except (discord.Forbidden, discord.HTTPException):
                        pass

    @atualizar.before_loop
    async def antes(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Counters(bot))
