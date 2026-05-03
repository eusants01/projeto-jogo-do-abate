import random
import discord
from discord import app_commands
from discord.ext import commands

from utils.db import (
    registrar_jogador,
    buscar_jogador,
    listar_ranking,
)

COR_ROXA = 0x7B2CFF
COR_VERMELHA = 0xE63946
COR_VERDE = 0x2ECC71
COR_DOURADA = 0xF1C40F

VIDAS_MAXIMAS = 20

GUILD_ID = 1480334256763961465
CANAL_ABATE_ID = 1500151299209957376
BANNER_URL = "https://i.imgur.com/28Oo2ln.png"


def gerar_barra_vidas(vidas: int):
    vidas = max(0, min(VIDAS_MAXIMAS, vidas))
    coracoes_cheios = round((vidas / VIDAS_MAXIMAS) * 10)
    coracoes_vazios = 10 - coracoes_cheios
    return "❤️" * coracoes_cheios + "🖤" * coracoes_vazios


def formatar_status(status: str):
    if status == "vivo":
        return "🟢 VIVO"
    if status == "eliminado":
        return "💀 ELIMINADO"
    return status.upper()


class PainelAbate(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Entrar no Ritual",
        emoji="🩸",
        style=discord.ButtonStyle.danger,
        custom_id="abate_entrar"
    )
    async def entrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogador = buscar_jogador(interaction.user.id)

        if jogador:
            await interaction.response.send_message(
                "Você já está no ritual.",
                ephemeral=True
            )
            return

        registrar_jogador(interaction.user.id, interaction.user.name)

        embed = discord.Embed(
            title="🩸 REGISTRO CRIADO",
            description=(
                f"{interaction.user.mention} entrou no ritual.\n\n"
                f"❤️ Vidas: **{VIDAS_MAXIMAS}**\n"
                "⚔️ Abates: 0"
            ),
            color=COR_ROXA
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Meu Registro",
        emoji="👁️",
        style=discord.ButtonStyle.secondary,
        custom_id="abate_perfil"
    )
    async def perfil(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogador = buscar_jogador(interaction.user.id)

        if not jogador:
            await interaction.response.send_message(
                "Você não está no ritual.",
                ephemeral=True
            )
            return

        user_id, username, vidas, abates, contratos, status, alvo_id, familia = jogador

        embed = discord.Embed(
            title="👁️ SEU REGISTRO",
            description=f"Participante: {interaction.user.mention}\nStatus: **{formatar_status(status)}**",
            color=COR_ROXA if status == "vivo" else COR_VERMELHA
        )

        embed.add_field(
            name="❤️ Vida",
            value=f"{gerar_barra_vidas(vidas)} `({vidas}/{VIDAS_MAXIMAS})`",
            inline=False
        )
        embed.add_field(name="⚔️ Abates", value=str(abates), inline=True)
        embed.add_field(name="📜 Contratos", value=str(contratos), inline=True)
        embed.add_field(name="🏯 Família", value=familia, inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Ranking",
        emoji="📊",
        style=discord.ButtonStyle.primary,
        custom_id="abate_ranking"
    )
    async def ranking(self, interaction: discord.Interaction, button: discord.ui.Button):
        ranking = listar_ranking()

        if not ranking:
            await interaction.response.send_message("Sem dados.", ephemeral=True)
            return

        texto = ""
        medalhas = ["🥇", "🥈", "🥉"]

        for pos, jogador in enumerate(ranking, start=1):
            user_id, username, vidas, abates, contratos, status, familia = jogador
            simbolo = medalhas[pos - 1] if pos <= 3 else f"`#{pos}`"

            texto += (
                f"{simbolo} <@{user_id}>\n"
                f"⚔️ **{abates}** abates • 📜 **{contratos}** contratos • "
                f"❤️ **{vidas}/{VIDAS_MAXIMAS}** • {formatar_status(status)}\n\n"
            )

        embed = discord.Embed(
            title="📊 RANKING DO ABATE",
            description=texto,
            color=COR_DOURADA
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


class Abate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(PainelAbate(bot))

    @commands.command(name="painel_abate")
    @commands.has_permissions(administrator=True)
    async def painel(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        embed = discord.Embed(
            title="🩸 JOGO DO ABATE",
            description=(
                f"❤️ Cada jogador possui **{VIDAS_MAXIMAS} vidas**\n"
                "⚔️ Sobreviva e elimine\n"
                "💀 O ritual começou"
            ),
            color=COR_ROXA
        )

        if BANNER_URL:
            embed.set_image(url=BANNER_URL)

        await ctx.send(embed=embed, view=PainelAbate(self.bot))


async def setup(bot):
    await bot.add_cog(Abate(bot))