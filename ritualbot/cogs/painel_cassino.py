import os
import discord
from discord.ext import commands
from discord import app_commands

GUILD_ID = int(os.getenv("GUILD_ID", "0"))

COR_CASSINO = 0x8B0000
COR_DOURADO = 0xD4AF37

BANNER_CASSINO = "https://i.imgur.com/udSDcgc.png"

CANAL_CASSINO_ID = 1502025561445240982
CANAL_PACTOS_ID = 1502025492818300928


class PainelCassinoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Comandos",
        emoji="🎲",
        style=discord.ButtonStyle.danger,
        custom_id="cassino_comandos"
    )
    async def comandos(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎲 Comandos do Cassino",
            description=(
                "`/saldo` — Veja suas Moedas do Diabo\n"
                "`/daily` — Receba sua recompensa diária\n"
                "`/pay` — Envie moedas para outro membro\n"
                "`/ranking` — Veja os mais ricos\n"
                "`/roleta` — Gire a Roleta Amaldiçoada"
            ),
            color=COR_CASSINO
        )
        embed.set_footer(text="👁️ Cassino do Diabo • A casa sempre observa")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Cassino",
        emoji="🎰",
        style=discord.ButtonStyle.secondary,
        custom_id="cassino_canal"
    )
    async def cassino(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"🎰 Acesse o canal principal do cassino: <#{CANAL_CASSINO_ID}>",
            ephemeral=True
        )

    @discord.ui.button(
        label="Pactos",
        emoji="✍️",
        style=discord.ButtonStyle.secondary,
        custom_id="cassino_pactos"
    )
    async def pactos(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"✍️ Acesse a sala dos pactos: <#{CANAL_PACTOS_ID}>",
            ephemeral=True
        )

    @discord.ui.button(
        label="Moedas do Diabo",
        emoji="🪙",
        style=discord.ButtonStyle.success,
        custom_id="cassino_moedas"
    )
    async def moedas(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🪙 Moedas do Diabo",
            description=(
                "As **Moedas do Diabo** são a economia oficial permanente da Família Sant’s.\n\n"
                "Elas poderão ser usadas para:\n\n"
                "🎲 Girar a roleta\n"
                "🃏 Participar de apostas\n"
                "✍️ Firmar pactos\n"
                "👹 Participar de bosses\n"
                "🎁 Comprar recompensas futuras\n\n"
                "> Toda fortuna possui um preço."
            ),
            color=COR_DOURADO
        )
        embed.set_footer(text="👁️ Cassino do Diabo • Riqueza, risco e consequência")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class PainelCassino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(PainelCassinoView())

    @app_commands.command(
        name="painel_cassino",
        description="Envia o painel principal do Cassino do Diabo."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_cassino(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎰 Cassino do Diabo",
            description=(
                "Bem-vindo ao sistema permanente do **Cassino do Diabo**.\n\n"
                "Aqui, membros poderão conquistar **🪙 Moedas do Diabo**, girar a roleta, "
                "participar de pactos, enfrentar eventos especiais e disputar rankings dentro da Família Sant’s.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🎲 **Roleta Amaldiçoada**\n"
                "Teste sua sorte a cada 2 minutos.\n\n"
                "🪙 **Economia Permanente**\n"
                "Acumule moedas, transfira para outros membros e suba no ranking.\n\n"
                "✍️ **Pactos**\n"
                "Contratos especiais serão revelados futuramente.\n\n"
                "👹 **Eventos do Cassino**\n"
                "Bosses, apostas, desafios e sistemas exclusivos serão ativados com o tempo.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "> A casa permite que você jogue...\n"
                "> mas nunca esquece quem sentou à mesa."
            ),
            color=COR_CASSINO
        )

        embed.set_image(url=BANNER_CASSINO)
        embed.set_footer(text="👁️ Cassino do Diabo • A casa sempre observa")

        await interaction.response.defer(ephemeral=True)

        await interaction.channel.send(
            embed=embed,
            view=PainelCassinoView()
        )


async def setup(bot):
    await bot.add_cog(PainelCassino(bot))