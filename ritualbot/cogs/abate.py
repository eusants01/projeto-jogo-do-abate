import random
import discord
from discord import app_commands
from discord.ext import commands

from utils.db import (
    registrar_jogador,
    buscar_jogador,
    listar_jogadores_vivos,
    listar_ranking,
    definir_alvo,
    limpar_alvos,
    adicionar_abate,
    remover_vida,
    resetar_jogo,
    criar_evento,
    listar_eventos,
    ativar_evento,
    encerrar_eventos,
    buscar_evento_ativo,
)

# =========================
# CONFIGURAÇÕES
# =========================

COR_ROXA = 0x7B2CFF
COR_VERMELHA = 0xE63946
COR_VERDE = 0x2ECC71
COR_DOURADA = 0xF1C40F

VIDAS_MAXIMAS = 20  # 🔥 ALTERADO

GUILD_ID = 1480334256763961465
CANAL_ABATE_ID = 1500151299209957376
CANAL_LOGS_ID = 1500386205160833115
CANAL_EVENTOS_ID = 1500386762210672680

BANNER_URL = "https://i.imgur.com/28Oo2ln.png"


def canal_valido(interaction: discord.Interaction):
    return interaction.channel_id == CANAL_ABATE_ID


def avatar_bot(bot: commands.Bot):
    if bot.user and bot.user.avatar:
        return bot.user.avatar.url
    return None


# 🔥 NOVA BARRA DE VIDA
def gerar_barra_vidas(vidas: int):
    vidas = max(0, min(VIDAS_MAXIMAS, vidas))

    coracoes_cheios = round((vidas / VIDAS_MAXIMAS) * 10)
    coracoes_vazios = 10 - coracoes_cheios

    return "❤️" * coracoes_cheios + "🖤" * coracoes_vazios


def formatar_status(status: str):
    return "🟢 VIVO" if status == "vivo" else "💀 ELIMINADO"


class PainelAbate(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Entrar no Ritual", style=discord.ButtonStyle.danger)
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

    @discord.ui.button(label="Meu Registro", style=discord.ButtonStyle.secondary)
    async def perfil(self, interaction: discord.Interaction, button: discord.ui.Button):

        jogador = buscar_jogador(interaction.user.id)

        if not jogador:
            await interaction.response.send_message("Você não está no ritual.", ephemeral=True)
            return

        user_id, username, vidas, abates, contratos, status, alvo_id, familia = jogador

        embed = discord.Embed(
            title="👁️ SEU REGISTRO",
            color=COR_ROXA
        )

        embed.add_field(
            name="❤️ Vida",
            value=f"{gerar_barra_vidas(vidas)} ({vidas}/{VIDAS_MAXIMAS})",
            inline=False
        )

        embed.add_field(name="⚔️ Abates", value=abates)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Ranking", style=discord.ButtonStyle.primary)
    async def ranking(self, interaction: discord.Interaction, button: discord.ui.Button):

        ranking = listar_ranking()

        if not ranking:
            await interaction.response.send_message("Sem dados.", ephemeral=True)
            return

        texto = ""

        for i, jogador in enumerate(ranking, 1):
            uid, nome, vidas, abates, *_ = jogador
            texto += f"{i}º <@{uid}> — ⚔️ {abates} | ❤️ {vidas}\n"

        await interaction.response.send_message(texto, ephemeral=True)


class Abate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(PainelAbate(bot))

    @commands.command(name="painel_abate")
    async def painel(self, ctx):

        embed = discord.Embed(
            title="🩸 JOGO DO ABATE",
            description=(
                f"❤️ Cada jogador possui **{VIDAS_MAXIMAS} vidas**\n"
                "⚔️ Sobreviva e elimine\n"
                "💀 O ritual começou"
            ),
            color=COR_ROXA
        )

        await ctx.send(embed=embed, view=PainelAbate(self.bot))


async def setup(bot):
    await bot.add_cog(Abate(bot))