"""✅ Verificação — botão que atribui o cargo e continua a funcionar após reiniciar."""

from __future__ import annotations

import discord
from discord.ext import commands


class VerificacaoView(discord.ui.View):
    """View persistente (timeout=None + custom_id) para sobreviver a reinícios."""

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Verificar-me",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="miku:verificar",
    )
    async def verificar(self, interaction: discord.Interaction, _botao: discord.ui.Button):
        guild = interaction.guild
        cfg = self.bot.storage.verificacao(guild.id)
        cargo_id = cfg.get("cargo_id")
        if not cargo_id:
            await interaction.response.send_message(
                "⚠️ A verificação ainda não está configurada.", ephemeral=True
            )
            return
        cargo = guild.get_role(int(cargo_id))
        if cargo is None:
            await interaction.response.send_message(
                "⚠️ O cargo configurado já não existe.", ephemeral=True
            )
            return
        try:
            await interaction.user.add_roles(cargo, reason="Verificação")
            await interaction.response.send_message(
                f"✅ Verificado! Recebeste o cargo **{cargo.name}**. Bem-vinda(o)! 💙",
                ephemeral=True,
            )
            await self.bot.storage.log(f"{interaction.user} verificado em {guild.name}")
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Não tenho permissão para te dar o cargo.", ephemeral=True
            )


class Verification(commands.Cog):
    """Sistema de verificação por botão."""

    def __init__(self, bot):
        self.bot = bot
        self.view = VerificacaoView(bot)
        bot.verificacao_view = self.view
        bot.add_view(self.view)  # regista a view persistente


async def setup(bot):
    await bot.add_cog(Verification(bot))
