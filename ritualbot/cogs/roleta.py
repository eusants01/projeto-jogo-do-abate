import os
import random
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord import app_commands

from utils.cassino_db import (
    obter_usuario,
    adicionar_moedas,
    remover_moedas,
    atualizar_roleta
)

GUILD_ID = int(os.getenv("GUILD_ID", "0"))

COR_CASSINO = 0x8B0000
COR_DOURADO = 0xD4AF37
COOLDOWN_ROLETA_MINUTOS = 30


RESULTADOS_ROLETA = [
    {
        "nome": "Fortuna Pequena",
        "raridade": "⚪ Comum",
        "tipo": "ganho",
        "valor": 100,
        "peso": 25,
        "frase": "A casa permitiu uma pequena vitória."
    },
    {
        "nome": "Sorte Passageira",
        "raridade": "⚪ Comum",
        "tipo": "ganho",
        "valor": 150,
        "peso": 20,
        "frase": "Sua sorte ainda respira."
    },
    {
        "nome": "Bolsa de Moedas",
        "raridade": "🟢 Incomum",
        "tipo": "ganho",
        "valor": 300,
        "peso": 15,
        "frase": "O Dealer sorriu brevemente."
    },
    {
        "nome": "Aposta Favorável",
        "raridade": "🟢 Incomum",
        "tipo": "ganho",
        "valor": 500,
        "peso": 10,
        "frase": "A roleta caiu ao seu favor."
    },
    {
        "nome": "Prêmio Proibido",
        "raridade": "🔵 Raro",
        "tipo": "ganho",
        "valor": 1000,
        "peso": 6,
        "frase": "O cassino ficou em silêncio por um instante."
    },
    {
        "nome": "Jackpot Sombrio",
        "raridade": "🔴 Lendário",
        "tipo": "ganho",
        "valor": 2500,
        "peso": 2,
        "frase": "O Dealer marcou seu nome."
    },
    {
        "nome": "Taxa da Casa",
        "raridade": "🟣 Amaldiçoado",
        "tipo": "perda",
        "valor": 100,
        "peso": 12,
        "frase": "A casa recolheu sua parte."
    },
    {
        "nome": "Dívida Pequena",
        "raridade": "🟣 Amaldiçoado",
        "tipo": "perda",
        "valor": 250,
        "peso": 7,
        "frase": "Toda fortuna exige um preço."
    },
    {
        "nome": "A Casa Sempre Ganha",
        "raridade": "💀 Maldição",
        "tipo": "perda",
        "valor": 500,
        "peso": 3,
        "frase": "Nem toda aposta termina em vitória."
    },
]


class Roleta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def sortear_resultado(self):
        pesos = [resultado["peso"] for resultado in RESULTADOS_ROLETA]
        return random.choices(RESULTADOS_ROLETA, weights=pesos, k=1)[0]

    @app_commands.command(name="roleta", description="Gire a Roleta Amaldiçoada do Cassino do Diabo.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def roleta(self, interaction: discord.Interaction):
        dados = obter_usuario(interaction.user.id)
        ultima_roleta = dados[5]

        agora = datetime.utcnow()

        if ultima_roleta:
            ultima = datetime.fromisoformat(ultima_roleta)
            proximo = ultima + timedelta(minutes=COOLDOWN_ROLETA_MINUTOS)

            if agora < proximo:
                restante = proximo - agora
                minutos = int(restante.total_seconds() // 60)
                segundos = int(restante.total_seconds() % 60)

                embed = discord.Embed(
                    title="⏳ Roleta em Recarga",
                    description=f"> “A roleta ainda não aceita uma nova aposta.”\n\n"
                                f"Volte em **{minutos}min {segundos}s**.",
                    color=COR_CASSINO
                )

                embed.set_footer(text="👁️ Cassino do Diabo • A pressa cobra caro")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        resultado = self.sortear_resultado()
        atualizar_roleta(interaction.user.id)

        if resultado["tipo"] == "ganho":
            adicionar_moedas(interaction.user.id, resultado["valor"])
            sinal = "+"
            cor = COR_DOURADO
        else:
            remover_moedas(interaction.user.id, resultado["valor"])
            sinal = "-"
            cor = COR_CASSINO

        embed = discord.Embed(
            title="🎰 Roleta Amaldiçoada",
            description=f"> “A roleta gira lentamente... O Dealer observa.”\n\n"
                        f"🎲 **Resultado:** {resultado['raridade']} **{resultado['nome']}**\n\n"
                        f"🪙 **{sinal}{resultado['valor']:,} Moedas do Diabo**\n\n"
                        f"*{resultado['frase']}*",
            color=cor
        )

        embed.set_footer(text=f"👁️ Cassino do Diabo • Retorne em {COOLDOWN_ROLETA_MINUTOS} minutos")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Roleta(bot))