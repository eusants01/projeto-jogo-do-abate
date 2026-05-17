import os
import random
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord import app_commands

from utils.cassino_db import (
    obter_usuario,
    obter_saldo,
    adicionar_moedas,
    transferir_moedas,
    atualizar_daily,
    ranking_ricos
)

GUILD_ID = int(os.getenv("GUILD_ID", "0"))

COR_CASSINO = 0x8B0000
COR_DOURADO = 0xD4AF37


class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="saldo", description="Veja seu saldo de Moedas do Diabo.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def saldo(self, interaction: discord.Interaction, membro: discord.Member = None):
        membro = membro or interaction.user
        dados = obter_usuario(membro.id)

        moedas = dados[1]
        total_ganho = dados[2]
        total_perdido = dados[3]

        embed = discord.Embed(
            title="🪙 Saldo do Cassino",
            description=f"> “A casa registrou sua fortuna.”\n\n"
                        f"👤 Membro: {membro.mention}\n"
                        f"🪙 Moedas do Diabo: **{moedas:,}**\n"
                        f"📈 Total ganho: **{total_ganho:,}**\n"
                        f"📉 Total perdido: **{total_perdido:,}**",
            color=COR_DOURADO
        )

        embed.set_footer(text="👁️ Cassino do Diabo • A casa sempre observa")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Receba sua recompensa diária do Cassino.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def daily(self, interaction: discord.Interaction):
        dados = obter_usuario(interaction.user.id)
        ultima_daily = dados[4]

        agora = datetime.utcnow()

        if ultima_daily:
            ultima = datetime.fromisoformat(ultima_daily)
            proximo = ultima + timedelta(hours=24)

            if agora < proximo:
                restante = proximo - agora
                horas = int(restante.total_seconds() // 3600)
                minutos = int((restante.total_seconds() % 3600) // 60)

                embed = discord.Embed(
                    title="⏳ Recompensa Indisponível",
                    description=f"> “A casa ainda não liberou sua próxima recompensa.”\n\n"
                                f"Volte em **{horas}h {minutos}min**.",
                    color=COR_CASSINO
                )
                embed.set_footer(text="👁️ Cassino do Diabo • Paciência também é aposta")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        recompensa = random.randint(200, 500)
        adicionar_moedas(interaction.user.id, recompensa)
        atualizar_daily(interaction.user.id)

        embed = discord.Embed(
            title="🎁 Recompensa Diária",
            description=f"> “O Dealer liberou sua recompensa diária.”\n\n"
                        f"🪙 Você recebeu **{recompensa} Moedas do Diabo**.",
            color=COR_DOURADO
        )

        embed.set_footer(text="👁️ Cassino do Diabo • Retorne amanhã")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pay", description="Envie Moedas do Diabo para outro membro.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def pay(self, interaction: discord.Interaction, membro: discord.Member, quantidade: int):
        if membro.bot:
            await interaction.response.send_message("❌ Você não pode enviar moedas para bots.", ephemeral=True)
            return

        if membro.id == interaction.user.id:
            await interaction.response.send_message("❌ Você não pode enviar moedas para si mesmo.", ephemeral=True)
            return

        if quantidade <= 0:
            await interaction.response.send_message("❌ Informe uma quantidade válida.", ephemeral=True)
            return

        sucesso = transferir_moedas(interaction.user.id, membro.id, quantidade)

        if not sucesso:
            await interaction.response.send_message("❌ Você não possui Moedas do Diabo suficientes.", ephemeral=True)
            return

        embed = discord.Embed(
            title="💸 Transferência Registrada",
            description=f"> “O cassino observou a movimentação.”\n\n"
                        f"{interaction.user.mention} enviou **{quantidade:,} Moedas do Diabo** para {membro.mention}.",
            color=COR_DOURADO
        )

        embed.set_footer(text="👁️ Cassino do Diabo • Toda dívida deixa rastros")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ranking", description="Veja os membros mais ricos do Cassino.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ranking(self, interaction: discord.Interaction):
        dados = ranking_ricos(10)

        if not dados:
            await interaction.response.send_message("Ainda não há jogadores no ranking.", ephemeral=True)
            return

        descricao = ""

        for pos, (user_id, moedas) in enumerate(dados, start=1):
            membro = interaction.guild.get_member(user_id)
            nome = membro.mention if membro else f"`{user_id}`"

            medalha = "👑" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else "🔸"
            descricao += f"{medalha} **{pos}.** {nome} — 🪙 **{moedas:,}**\n"

        embed = discord.Embed(
            title="🏆 Ranking das Moedas do Diabo",
            description=descricao,
            color=COR_DOURADO
        )

        embed.set_footer(text="👁️ Cassino do Diabo • Riqueza, poder e corrupção")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Economia(bot))