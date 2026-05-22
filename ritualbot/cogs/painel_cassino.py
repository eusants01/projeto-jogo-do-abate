import os
import discord
from discord.ext import commands
from discord import app_commands

from utils.cassino_db import obter_saldo, ranking_ricos

GUILD_ID = int(os.getenv("GUILD_ID", "0"))

COR_CASSINO = 0x8B0000
COR_DOURADO = 0xD4AF37
COR_VERDE   = 0x2ECC71
COR_ROXO    = 0x9B59B6

BANNER_CASSINO  = "https://i.imgur.com/udSDcgc.png"
IMAGEM_PACTOS   = "https://i.imgur.com/MX7rQpp.png"

CANAL_CASSINO_ID = 1502025561445240982
CANAL_PACTOS_ID  = 1502025492818300928

SEPARADOR = "```\n ─────────────────────────── \n```"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                  VIEWS DO PAINEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PainelCassinoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # ── 🎲 Comandos ──────────────────────────────

    @discord.ui.button(
        label="Comandos",
        emoji="🎲",
        style=discord.ButtonStyle.danger,
        custom_id="cassino_comandos",
        row=0
    )
    async def comandos(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎲  Comandos do Cassino",
            description=(
                f"-# *\"Conheça as regras antes de sentar à mesa.\"*\n\n"
                f"{SEPARADOR}"
                "**💰 Economia**\n"
                "> `/saldo` — Veja suas Moedas do Diabo\n"
                "> `/daily` — Recompensa diária (com streak)\n"
                "> `/pay` — Envie moedas para outro membro\n"
                "> `/ranking` — Os mais ricos do Cassino\n\n"
                "**🎰 Jogos**\n"
                "> `/roleta` — Gire a Roleta Amaldiçoada\n\n"
                "**✍️ Pactos**\n"
                "> `!meus_pactos` — Histórico de pactos\n"
                "> `!ranking_pactos` — Top pactuantes\n"
                "> `!seguro @cargo` — Proteja um cargo\n\n"
                f"{SEPARADOR}"
                "> *A casa conhece todas as jogadas.*"
            ),
            color=COR_CASSINO
        )
        embed.set_footer(text="👁️ Cassino do Diabo  •  A casa sempre observa")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── 🎰 Cassino ───────────────────────────────

    @discord.ui.button(
        label="Cassino",
        emoji="🎰",
        style=discord.ButtonStyle.secondary,
        custom_id="cassino_canal",
        row=0
    )
    async def cassino(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎰  Canal do Cassino",
            description=(
                f"O Cassino do Diabo aguarda sua aposta.\n\n"
                f"➡️ Acesse: <#{CANAL_CASSINO_ID}>\n\n"
                f"> *Entre. A casa já sabe o que você quer.*"
            ),
            color=COR_CASSINO
        )
        embed.set_footer(text="👁️ Cassino do Diabo  •  Entre por sua conta e risco")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── ✍️ Pactos ────────────────────────────────

    @discord.ui.button(
        label="Pactos",
        emoji="✍️",
        style=discord.ButtonStyle.secondary,
        custom_id="cassino_pactos",
        row=0
    )
    async def pactos(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="✍️  Sala dos Pactos",
            description=(
                f"Contratos proibidos são firmados nas sombras.\n\n"
                f"➡️ Acesse: <#{CANAL_PACTOS_ID}>\n\n"
                f"{SEPARADOR}"
                "**Raridades disponíveis:**\n"
                "⚪ Comum — Baixo risco, baixa recompensa\n"
                "🔵 Raro — Risco moderado\n"
                "🟣 Épico — Alto risco, alta recompensa\n"
                "🟡 Lendário — Poucos recebem. Menos ainda sobrevivem.\n\n"
                "> *Toda fortuna exige um sacrifício.*"
            ),
            color=COR_ROXO
        )
        embed.set_image(url=IMAGEM_PACTOS)
        embed.set_footer(text="👁️ Cassino do Diabo  •  Pactos Proibidos")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── 🪙 Moedas ────────────────────────────────

    @discord.ui.button(
        label="Moedas do Diabo",
        emoji="🪙",
        style=discord.ButtonStyle.success,
        custom_id="cassino_moedas",
        row=1
    )
    async def moedas(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🪙  Moedas do Diabo",
            description=(
                f"-# *\"Toda riqueza tem um dono. Até a sua.\"*\n\n"
                "As **Moedas do Diabo** são a moeda oficial permanente da **Família Sant's**.\n\n"
                f"{SEPARADOR}"
                "**Como ganhar:**\n"
                "> 🎁 `/daily` — Recompensa diária\n"
                "> 🎰 `/roleta` — Apostar na roleta\n"
                "> ✍️ Pactos — Aceitar contratos\n"
                "> 💸 `/pay` — Receber de outros membros\n\n"
                "**Como usar:**\n"
                "> 🎲 Apostas e jogos\n"
                "> ✍️ Firmar pactos\n"
                "> 👹 Participar de bosses\n"
                "> 🛡️ Seguros de cargo (`!seguro`)\n"
                "> 🎁 Recompensas futuras\n\n"
                f"{SEPARADOR}"
                "> *Toda fortuna possui um preço.*"
            ),
            color=COR_DOURADO
        )
        embed.set_footer(text="👁️ Cassino do Diabo  •  Riqueza, risco e consequência")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── 🏆 Ranking ───────────────────────────────

    @discord.ui.button(
        label="Ranking",
        emoji="🏆",
        style=discord.ButtonStyle.primary,
        custom_id="cassino_ranking",
        row=1
    )
    async def ranking(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            dados = ranking_ricos(5)
        except Exception:
            dados = []

        if not dados:
            return await interaction.response.send_message(
                "📊 Ainda não há jogadores no ranking.", ephemeral=True)

        medalhas = ["👑", "🥈", "🥉", "🔸", "🔸"]
        linhas   = []

        for pos, (user_id, moedas) in enumerate(dados):
            alvo  = interaction.guild.get_member(user_id)
            nome  = alvo.display_name if alvo else f"ID {user_id}"
            medal = medalhas[pos] if pos < len(medalhas) else "🔸"
            linhas.append(f"{medal} **{pos+1}.** {nome} — 🪙 **{moedas:,}**")

        embed = discord.Embed(
            title="🏆  Top 5 — Moedas do Diabo",
            description=(
                f"-# *\"Riqueza, poder e corrupção.\"*\n\n"
                f"{SEPARADOR}"
                + "\n".join(linhas) + f"\n\n{SEPARADOR}"
                "> *Use `/ranking` para ver o top completo.*"
            ),
            color=COR_DOURADO
        )
        embed.set_footer(text="👁️ Cassino do Diabo  •  Os mais ricos da mesa")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── ❓ Sobre ─────────────────────────────────

    @discord.ui.button(
        label="Sobre o Cassino",
        emoji="👁️",
        style=discord.ButtonStyle.secondary,
        custom_id="cassino_sobre",
        row=1
    )
    async def sobre(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👁️  Sobre o Cassino do Diabo",
            description=(
                f"-# *\"A casa permite que você jogue...\"*\n\n"
                "O **Cassino do Diabo** é o sistema econômico permanente "
                "da **Família Sant's**.\n\n"
                f"{SEPARADOR}"
                "**🎰 Jogos disponíveis:**\n"
                "> Roleta Amaldiçoada\n\n"
                "**✍️ Sistema de Pactos:**\n"
                "> Contratos proibidos com recompensas e riscos reais.\n"
                "> Cargos, moedas e posições em jogo.\n\n"
                "**🏆 Rankings permanentes:**\n"
                "> Sua posição na Família é visível a todos.\n\n"
                "**👹 Em breve:**\n"
                "> Bosses, apostas, leilões e eventos especiais.\n\n"
                f"{SEPARADOR}"
                "> *...mas nunca esquece quem sentou à mesa.*"
            ),
            color=COR_CASSINO
        )
        embed.set_image(url=BANNER_CASSINO)
        embed.set_footer(text="👁️ Cassino do Diabo  •  Est. Família Sant's")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                    COG PRINCIPAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
            title="🎰  Cassino do Diabo",
            description=(
                f"-# *\"A casa permite que você jogue...\"*\n\n"
                "Bem-vindo ao sistema permanente do **Cassino do Diabo**.\n\n"
                "Aqui, membros conquistam **🪙 Moedas do Diabo**, giram a roleta, "
                "firmam pactos proibidos, enfrentam bosses e disputam o ranking "
                "da **Família Sant's**.\n\n"
                f"{SEPARADOR}"
                "🎲 **Roleta Amaldiçoada**\n"
                "> Teste sua sorte. A cada rodada, o Cassino decide.\n\n"
                "🪙 **Economia Permanente**\n"
                "> Acumule moedas, suba no ranking, transfira para aliados.\n\n"
                "✍️ **Pactos Proibidos**\n"
                "> Contratos com recompensas altas e consequências reais.\n"
                "> Cargos, moedas e posições em risco a cada assinatura.\n\n"
                "👹 **Eventos Especiais**\n"
                "> Bosses, apostas coletivas e desafios serão ativados com o tempo.\n\n"
                f"{SEPARADOR}"
                "> *...mas nunca esquece quem sentou à mesa.*"
            ),
            color=COR_CASSINO
        )
        embed.set_image(url=BANNER_CASSINO)
        embed.set_footer(text="👁️ Cassino do Diabo  •  A casa sempre observa")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.defer(ephemeral=True)
        await interaction.channel.send(embed=embed, view=PainelCassinoView())


async def setup(bot):
    await bot.add_cog(PainelCassino(bot))