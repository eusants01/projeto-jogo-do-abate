import discord
from discord import app_commands
from discord.ext import commands

from utils.db import (
    registrar_jogador,
    buscar_jogador,
    listar_ranking,
    adicionar_abate,
    remover_vida,
    resetar_jogo,
)

# =========================
# CONFIGURAÇÕES VISUAIS
# =========================

COR_ROXA = 0x7B2CFF
COR_VERMELHA = 0xE63946
COR_VERDE = 0x2ECC71
COR_DOURADA = 0xF1C40F

GUILD_ID = 1480334256763961465  # Troque se mudar de servidor

# Opcional: coloque aqui o link direto do banner hospedado.
# Exemplo: https://i.imgur.com/SEU_BANNER.png
BANNER_URL = ""
THUMB_URL = ""


def avatar_bot(bot: commands.Bot):
    if bot.user and bot.user.avatar:
        return bot.user.avatar.url
    return None


def gerar_barra_vidas(vidas: int):
    vidas = max(0, min(3, vidas))
    return "❤️" * vidas + "🖤" * (3 - vidas)


def formatar_status(status: str):
    if status == "vivo":
        return "🟢 VIVO"
    if status == "eliminado":
        return "💀 ELIMINADO"
    return status.upper()


# =========================
# VIEW PRINCIPAL
# =========================

class PainelAbate(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Entrar no Ritual",
        emoji="🩸",
        style=discord.ButtonStyle.danger,
        custom_id="abate_entrar"
    )
    async def entrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogador_existente = buscar_jogador(interaction.user.id)

        if jogador_existente:
            embed = discord.Embed(
                title="🩸 Você já está dentro do ritual",
                description=(
                    f"{interaction.user.mention}, seu registro já existe no **Jogo do Abate**.\n\n"
                    "A partir daqui, não existe retorno.\n"
                    "> **Sobreviva. Cumpra. Elimine.**"
                ),
                color=COR_ROXA
            )
            embed.set_footer(text="Família Sant's • RitualBot")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        registrar_jogador(interaction.user.id, interaction.user.name)

        embed = discord.Embed(
            title="🩸 REGISTRO CRIADO — ENTRADA CONFIRMADA",
            description=(
                f"{interaction.user.mention}, você foi oficialmente registrado no **Jogo do Abate**.\n\n"
                "```ansi\n"
                "\u001b[35mSTATUS: PARTICIPANTE ATIVO\u001b[0m\n"
                "```\n"
                "❤️ **Vidas iniciais:** 3\n"
                "⚔️ **Abates:** 0\n"
                "📜 **Contratos:** 0\n"
                "🎯 **Alvo atual:** ainda não definido\n\n"
                "> **O ritual não perdoa escolhas ruins.**"
            ),
            color=COR_ROXA
        )
        embed.set_thumbnail(url=avatar_bot(self.bot))
        embed.set_footer(text="Família Sant's • RitualBot")

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
            embed = discord.Embed(
                title="❌ Registro não encontrado",
                description=(
                    "Você ainda não entrou no **Jogo do Abate**.\n\n"
                    "Clique em **Entrar no Ritual** para criar seu registro."
                ),
                color=COR_VERMELHA
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        user_id, username, vidas, abates, contratos, status, alvo_id, familia = jogador

        embed = discord.Embed(
            title=f"👁️ REGISTRO DO PARTICIPANTE",
            description=(
                f"Participante: {interaction.user.mention}\n"
                f"Status atual: **{formatar_status(status)}**\n\n"
                "> Cada registro conta uma história. Alguns terminam cedo."
            ),
            color=COR_ROXA if status == "vivo" else COR_VERMELHA
        )

        embed.add_field(name="❤️ Vidas", value=f"{gerar_barra_vidas(vidas)} `({vidas}/3)`", inline=False)
        embed.add_field(name="⚔️ Abates", value=str(abates), inline=True)
        embed.add_field(name="📜 Contratos", value=str(contratos), inline=True)
        embed.add_field(name="🏯 Família", value=familia, inline=True)
        embed.add_field(
            name="🎯 Alvo Atual",
            value=f"<@{alvo_id}>" if alvo_id else "`Aguardando marcação...`",
            inline=False
        )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Família Sant's • Registro do Ritual")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Ranking",
        emoji="📊",
        style=discord.ButtonStyle.primary,
        custom_id="abate_ranking"
    )
    async def ranking(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogadores = listar_ranking()

        if not jogadores:
            embed = discord.Embed(
                title="📊 Ranking vazio",
                description="Nenhum participante entrou no ritual ainda.",
                color=COR_ROXA
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        descricao = ""

        medalhas = ["🥇", "🥈", "🥉"]

        for pos, jogador in enumerate(jogadores, start=1):
            user_id, username, vidas, abates, contratos, status, familia = jogador
            simbolo = medalhas[pos - 1] if pos <= 3 else f"`#{pos}`"

            descricao += (
                f"{simbolo} <@{user_id}>\n"
                f"⚔️ **{abates}** abates • 📜 **{contratos}** contratos • "
                f"❤️ **{vidas}** vidas • {formatar_status(status)}\n\n"
            )

        embed = discord.Embed(
            title="📊 RANKING DO ABATE",
            description=descricao,
            color=COR_DOURADA
        )
        embed.set_footer(text="Atualizado em tempo real • RitualBot")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Regras",
        emoji="📜",
        style=discord.ButtonStyle.secondary,
        custom_id="abate_regras"
    )
    async def regras(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📜 REGULAMENTO DO RITUAL",
            description=(
                "**Art. 1º — Da Entrada**\n"
                "Todo participante inicia com **3 vidas**.\n\n"

                "**Art. 2º — Dos Abates**\n"
                "Um abate só será válido quando registrado pela staff.\n\n"

                "**Art. 3º — Da Perda de Vida**\n"
                "Ao perder um desafio válido, o participante perde **1 vida**.\n\n"

                "**Art. 4º — Da Eliminação**\n"
                "Ao atingir **0 vidas**, o participante será eliminado.\n\n"

                "**Art. 5º — Dos Contratos**\n"
                "Contratos podem ser públicos, secretos ou especiais.\n\n"

                "**Art. 6º — Do Ritual**\n"
                "A staff pode iniciar eventos especiais que alteram regras temporariamente.\n\n"

                "> **Sobreviva. Cumpra. Elimine.**"
            ),
            color=COR_ROXA
        )
        embed.set_thumbnail(url=avatar_bot(self.bot))
        embed.set_footer(text="Família Sant's • Leis do Ritual")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Status do Ritual",
        emoji="🧿",
        style=discord.ButtonStyle.success,
        custom_id="abate_status"
    )
    async def status_ritual(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogadores = listar_ranking()
        vivos = sum(1 for j in jogadores if j[5] == "vivo")
        eliminados = sum(1 for j in jogadores if j[5] == "eliminado")

        embed = discord.Embed(
            title="🧿 STATUS DO RITUAL",
            description=(
                "```ansi\n"
                "\u001b[35mO sistema está ativo.\u001b[0m\n"
                "```\n"
                f"👥 **Participantes registrados:** {len(jogadores)}\n"
                f"🟢 **Vivos no ranking:** {vivos}\n"
                f"💀 **Eliminados no ranking:** {eliminados}\n\n"
                "🎯 **Alvos secretos:** em preparação\n"
                "📜 **Contratos:** em preparação\n"
                "🧩 **Fragmentos:** em preparação\n\n"
                "> O plano ainda está incompleto."
            ),
            color=COR_ROXA
        )
        embed.set_footer(text="RitualBot • Sistema do Abate")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# =========================
# COG PRINCIPAL
# =========================

class Abate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(PainelAbate(bot))

    @app_commands.command(
        name="painel_abate",
        description="Envia o painel principal do Jogo do Abate."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_abate(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🩸 JOGO DO ABATE — RITUAL PRINCIPAL",
            description=(
                "```ansi\n"
                "\u001b[35mO ritual foi iniciado.\u001b[0m\n"
                "```\n"
                "A partir deste momento, cada escolha pode definir seu destino.\n\n"
                "🎯 **Alvos serão marcados**\n"
                "📜 **Contratos serão liberados**\n"
                "❤️ **Cada participante possui 3 vidas**\n"
                "💀 **0 vidas = eliminação**\n"
                "📊 **Ranking atualizado em tempo real**\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "### 🧿 SISTEMA ATIVO\n"
                "Use os botões abaixo para entrar, consultar seu registro ou acompanhar o ranking.\n\n"
                "> **Sobreviva. Cumpra. Elimine.**"
            ),
            color=COR_ROXA
        )

        embed.add_field(
            name="⚔️ Como funciona?",
            value=(
                "Entre no ritual, vença desafios, conclua contratos e acumule abates. "
                "Cada derrota pode custar uma vida."
            ),
            inline=False
        )

        embed.add_field(
            name="⚠️ Aviso",
            value="Alguns nomes serão marcados. Nem todos permanecerão de pé.",
            inline=False
        )

        thumb = avatar_bot(self.bot)
        if thumb:
            embed.set_thumbnail(url=thumb)

        if BANNER_URL:
            embed.set_image(url=BANNER_URL)

        embed.set_footer(text="Família Sant's • RitualBot • O plano segue em andamento")

        await interaction.response.send_message(embed=embed, view=PainelAbate(self.bot))

    @app_commands.command(
        name="registrar_abate",
        description="Registra um abate e remove 1 vida do perdedor."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.checks.has_permissions(administrator=True)
    async def registrar_abate_cmd(
        self,
        interaction: discord.Interaction,
        vencedor: discord.Member,
        perdedor: discord.Member,
        motivo: str = "Abate registrado pela staff"
    ):
        registrar_jogador(vencedor.id, vencedor.name)
        registrar_jogador(perdedor.id, perdedor.name)

        adicionar_abate(vencedor.id)
        jogador_perdedor = remover_vida(perdedor.id)

        vidas = jogador_perdedor[2]
        status = jogador_perdedor[5]

        embed = discord.Embed(
            title="⚔️ ABATE REGISTRADO",
            description=(
                "```ansi\n"
                "\u001b[31mUM NOME FOI MARCADO.\u001b[0m\n"
                "```\n"
                f"🏆 **Vencedor:** {vencedor.mention}\n"
                f"🩸 **Perdedor:** {perdedor.mention}\n"
                f"📌 **Motivo:** {motivo}\n\n"
                f"❤️ **Vidas restantes do perdedor:** {gerar_barra_vidas(vidas)} `({vidas}/3)`"
            ),
            color=COR_VERMELHA
        )

        if status == "eliminado":
            embed.add_field(
                name="💀 ELIMINAÇÃO CONFIRMADA",
                value=(
                    f"{perdedor.mention} foi eliminado do **Jogo do Abate**.\n"
                    "> O ritual cobrou seu preço."
                ),
                inline=False
            )

        embed.set_thumbnail(url=perdedor.display_avatar.url)
        embed.set_footer(text="RitualBot • Registro oficial de abate")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="perfil_abate",
        description="Mostra o perfil de um participante."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def perfil_abate(
        self,
        interaction: discord.Interaction,
        membro: discord.Member | None = None
    ):
        membro = membro or interaction.user
        jogador = buscar_jogador(membro.id)

        if not jogador:
            await interaction.response.send_message(
                f"{membro.mention} ainda não entrou no Jogo do Abate.",
                ephemeral=True
            )
            return

        user_id, username, vidas, abates, contratos, status, alvo_id, familia = jogador

        embed = discord.Embed(
            title="👁️ REGISTRO DO RITUAL",
            description=f"Participante: {membro.mention}\nStatus: **{formatar_status(status)}**",
            color=COR_ROXA if status == "vivo" else COR_VERMELHA
        )
        embed.add_field(name="❤️ Vidas", value=f"{gerar_barra_vidas(vidas)} `({vidas}/3)`", inline=False)
        embed.add_field(name="⚔️ Abates", value=str(abates), inline=True)
        embed.add_field(name="📜 Contratos", value=str(contratos), inline=True)
        embed.add_field(name="🏯 Família", value=familia, inline=True)
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_footer(text="Família Sant's • RitualBot")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="ranking_abate",
        description="Mostra o ranking geral do Jogo do Abate."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ranking_abate(self, interaction: discord.Interaction):
        jogadores = listar_ranking()

        if not jogadores:
            await interaction.response.send_message("Ainda não há jogadores no ranking.")
            return

        descricao = ""
        medalhas = ["🥇", "🥈", "🥉"]

        for pos, jogador in enumerate(jogadores, start=1):
            user_id, username, vidas, abates, contratos, status, familia = jogador
            simbolo = medalhas[pos - 1] if pos <= 3 else f"`#{pos}`"
            descricao += (
                f"{simbolo} <@{user_id}> — "
                f"⚔️ **{abates}** | 📜 **{contratos}** | ❤️ **{vidas}** | {formatar_status(status)}\n"
            )

        embed = discord.Embed(
            title="📊 RANKING DO ABATE",
            description=descricao,
            color=COR_DOURADA
        )
        embed.set_footer(text="RitualBot • Ranking oficial")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="resetar_abate",
        description="Reseta todos os dados do Jogo do Abate."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.checks.has_permissions(administrator=True)
    async def resetar_abate_cmd(self, interaction: discord.Interaction):
        resetar_jogo()

        embed = discord.Embed(
            title="🩸 RITUAL RESETADO",
            description=(
                "Todos os registros do **Jogo do Abate** foram apagados.\n\n"
                "> Um novo ciclo poderá começar."
            ),
            color=COR_VERMELHA
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Abate(bot))
