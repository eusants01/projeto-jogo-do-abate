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

GUILD_ID = 1480334256763961465

# 📢 Canal onde os comandos do Jogo do Abate podem ser usados
CANAL_ABATE_ID = 1500151299209957376

# 📜 Canal de logs automáticos
CANAL_LOGS_ID = 1500386205160833115

# 💀 Canal de anúncios/eventos
CANAL_EVENTOS_ID = 1500386762210672680

# Banner do painel
BANNER_URL = "https://i.imgur.com/28Oo2ln.png"


def canal_valido(interaction: discord.Interaction):
    return interaction.channel_id == CANAL_ABATE_ID


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


def embaralhar_alvos(jogadores):
    ids = [j[0] for j in jogadores]

    if len(ids) < 2:
        return {}

    alvos = ids.copy()

    for _ in range(50):
        random.shuffle(alvos)
        if all(jogador_id != alvo_id for jogador_id, alvo_id in zip(ids, alvos)):
            return dict(zip(ids, alvos))

    alvos = ids[1:] + ids[:1]
    return dict(zip(ids, alvos))


async def enviar_log(guild: discord.Guild, embed: discord.Embed):
    if not guild:
        return

    canal = guild.get_channel(CANAL_LOGS_ID)
    if canal:
        await canal.send(embed=embed)


async def anunciar_evento(guild: discord.Guild, embed: discord.Embed | None = None, mensagem: str | None = None):
    if not guild:
        return

    canal = guild.get_channel(CANAL_EVENTOS_ID)
    if canal:
        if embed:
            await canal.send(embed=embed)
        elif mensagem:
            await canal.send(mensagem)


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
        if not canal_valido(interaction):
            await interaction.response.send_message(
                "🚫 Use este painel apenas no canal do **Jogo do Abate**.",
                ephemeral=True
            )
            return

        jogador_existente = buscar_jogador(interaction.user.id)

        if jogador_existente:
            embed = discord.Embed(
                title="🩸 Você já está dentro do ritual",
                description=(
                    f"{interaction.user.mention}, seu registro já existe.\n\n"
                    "> **Sobreviva. Cumpra. Elimine.**"
                ),
                color=COR_ROXA
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        registrar_jogador(interaction.user.id, interaction.user.name)

        embed = discord.Embed(
            title="🩸 REGISTRO CRIADO",
            description=(
                f"{interaction.user.mention}, você entrou no **Jogo do Abate**.\n\n"
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

        log = discord.Embed(
            title="📜 NOVO PARTICIPANTE",
            description=f"{interaction.user.mention} entrou no **Jogo do Abate**.",
            color=COR_VERDE
        )
        log.set_thumbnail(url=interaction.user.display_avatar.url)
        await enviar_log(interaction.guild, log)

    @discord.ui.button(
        label="Meu Registro",
        emoji="👁️",
        style=discord.ButtonStyle.secondary,
        custom_id="abate_perfil"
    )
    async def perfil(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not canal_valido(interaction):
            await interaction.response.send_message(
                "🚫 Use este painel apenas no canal do **Jogo do Abate**.",
                ephemeral=True
            )
            return

        jogador = buscar_jogador(interaction.user.id)

        if not jogador:
            await interaction.response.send_message(
                "Você ainda não entrou no Jogo do Abate.",
                ephemeral=True
            )
            return

        user_id, username, vidas, abates, contratos, status, alvo_id, familia = jogador

        embed = discord.Embed(
            title="👁️ REGISTRO DO PARTICIPANTE",
            description=f"Participante: {interaction.user.mention}\nStatus: **{formatar_status(status)}**",
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

        evento = buscar_evento_ativo()
        if evento:
            _, nome, descricao, multiplicador, dano_extra, ativo = evento
            embed.add_field(
                name="💀 Evento Ativo",
                value=f"**{nome}**\n{descricao}",
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
        if not canal_valido(interaction):
            await interaction.response.send_message(
                "🚫 Use este painel apenas no canal do **Jogo do Abate**.",
                ephemeral=True
            )
            return

        jogadores = listar_ranking()

        if not jogadores:
            await interaction.response.send_message("Nenhum participante entrou ainda.", ephemeral=True)
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
        if not canal_valido(interaction):
            await interaction.response.send_message(
                "🚫 Use este painel apenas no canal do **Jogo do Abate**.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📜 REGULAMENTO DO RITUAL",
            description=(
                "**Art. 1º — Da Entrada**\n"
                "Todo participante inicia com **3 vidas**.\n\n"
                "**Art. 2º — Dos Abates**\n"
                "Um abate só será válido quando registrado pela staff.\n\n"
                "**Art. 3º — Dos Alvos Secretos**\n"
                "A staff pode sortear alvos privados. Cada participante recebe seu alvo por DM.\n\n"
                "**Art. 4º — Dos Eventos Especiais**\n"
                "Eventos podem dobrar abates, aumentar dano ou alterar a dinâmica do jogo.\n\n"
                "**Art. 5º — Da Eliminação**\n"
                "Ao atingir **0 vidas**, o participante será eliminado.\n\n"
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
        if not canal_valido(interaction):
            await interaction.response.send_message(
                "🚫 Use este painel apenas no canal do **Jogo do Abate**.",
                ephemeral=True
            )
            return

        jogadores = listar_jogadores_vivos()
        evento = buscar_evento_ativo()

        embed = discord.Embed(
            title="🧿 STATUS DO RITUAL",
            description=(
                f"👥 **Participantes vivos:** {len(jogadores)}\n"
                f"💀 **Evento ativo:** {evento[1] if evento else 'Nenhum'}\n\n"
                "🎯 **Alvos secretos:** disponíveis\n"
                "💀 **Eventos especiais:** disponíveis\n\n"
                "> O plano segue em andamento."
            ),
            color=COR_ROXA
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class Abate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(PainelAbate(bot))

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            mensagem = "🚫 Use este comando apenas no canal do **Jogo do Abate** ou verifique suas permissões."
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(mensagem, ephemeral=True)
                else:
                    await interaction.response.send_message(mensagem, ephemeral=True)
            except Exception:
                pass
            return

        raise error

    @app_commands.command(
        name="painel_abate",
        description="Envia o painel principal do Jogo do Abate."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.check(canal_valido)
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_abate(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🩸 JOGO DO ABATE — RITUAL PRINCIPAL",
            description=(
                "```ansi\n"
                "\u001b[35mO ritual foi iniciado.\u001b[0m\n"
                "```\n"
                "A partir deste momento, cada escolha pode definir seu destino.\n\n"
                "🎯 **Alvos secretos por DM**\n"
                "📜 **Contratos e desafios**\n"
                "❤️ **Cada participante possui 3 vidas**\n"
                "💀 **Eventos especiais podem alterar o jogo**\n"
                "📊 **Ranking atualizado em tempo real**\n\n"
                "> **Sobreviva. Cumpra. Elimine.**"
            ),
            color=COR_ROXA
        )

        embed.add_field(
            name="⚠️ Aviso",
            value="Alguns nomes serão marcados. Nem todos permanecerão de pé.",
            inline=False
        )

        if avatar_bot(self.bot):
            embed.set_thumbnail(url=avatar_bot(self.bot))

        if BANNER_URL:
            embed.set_image(url=BANNER_URL)

        embed.set_footer(text="Família Sant's • RitualBot • O plano segue em andamento")

        # Resposta privada: evita aparecer publicamente "usou /painel_abate".
        await interaction.response.defer(ephemeral=True)

        await interaction.channel.send(
            embed=embed,
            view=PainelAbate(self.bot)
        )

        await interaction.followup.send(
            "✅ Painel enviado com sucesso.",
            ephemeral=True
        )

    @app_commands.command(
        name="sortear_alvos",
        description="Sorteia alvos secretos entre todos os jogadores vivos e envia por DM."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.check(canal_valido)
    @app_commands.checks.has_permissions(administrator=True)
    async def sortear_alvos(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        jogadores = listar_jogadores_vivos()

        if len(jogadores) < 2:
            await interaction.followup.send(
                "É necessário ter pelo menos **2 jogadores vivos** para sortear alvos.",
                ephemeral=True
            )
            return

        mapa_alvos = embaralhar_alvos(jogadores)
        enviados = 0
        falhas = 0

        for jogador_id, alvo_id in mapa_alvos.items():
            definir_alvo(jogador_id, alvo_id)

            jogador = interaction.guild.get_member(jogador_id)
            alvo = interaction.guild.get_member(alvo_id)

            if not jogador or not alvo:
                falhas += 1
                continue

            embed_dm = discord.Embed(
                title="🎯 ALVO SECRETO DEFINIDO",
                description=(
                    "Você recebeu um alvo dentro do **Jogo do Abate**.\n\n"
                    f"🎯 **Seu alvo:** {alvo.mention}\n\n"
                    "Elimine seu alvo em um desafio válido para receber reconhecimento no ritual.\n\n"
                    "> **Não revele seu alvo. O plano depende do silêncio.**"
                ),
                color=COR_ROXA
            )
            embed_dm.set_thumbnail(url=alvo.display_avatar.url)
            embed_dm.set_footer(text="RitualBot • Alvo secreto")

            try:
                await jogador.send(embed=embed_dm)
                enviados += 1
            except discord.Forbidden:
                falhas += 1

        embed = discord.Embed(
            title="🎯 ALVOS SECRETOS SORTEADOS",
            description=(
                f"✅ **DMs enviadas:** {enviados}\n"
                f"⚠️ **Falhas:** {falhas}\n\n"
                "Os participantes vivos receberam seus alvos por mensagem privada."
            ),
            color=COR_VERDE
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

        anuncio = discord.Embed(
            title="🎯 NOVOS ALVOS DEFINIDOS",
            description=(
                "Os alvos secretos foram sorteados.\n\n"
                "Verifique sua DM.\n"
                "> O plano depende do silêncio."
            ),
            color=COR_ROXA
        )
        await anunciar_evento(interaction.guild, embed=anuncio)

        log = discord.Embed(
            title="📜 LOG — ALVOS SORTEADOS",
            description=(
                f"✅ DMs enviadas: **{enviados}**\n"
                f"⚠️ Falhas: **{falhas}**\n"
                f"👤 Responsável: {interaction.user.mention}"
            ),
            color=COR_VERDE
        )
        await enviar_log(interaction.guild, log)

    @app_commands.command(
        name="limpar_alvos",
        description="Remove todos os alvos atuais dos jogadores."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.check(canal_valido)
    @app_commands.checks.has_permissions(administrator=True)
    async def limpar_alvos_cmd(self, interaction: discord.Interaction):
        limpar_alvos()

        await interaction.response.send_message(
            "🎯 Todos os alvos secretos foram removidos.",
            ephemeral=True
        )

        log = discord.Embed(
            title="📜 LOG — ALVOS LIMPOS",
            description=f"Todos os alvos foram removidos por {interaction.user.mention}.",
            color=COR_ROXA
        )
        await enviar_log(interaction.guild, log)

    @app_commands.command(
        name="meu_alvo",
        description="Mostra seu alvo secreto atual."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.check(canal_valido)
    async def meu_alvo(self, interaction: discord.Interaction):
        jogador = buscar_jogador(interaction.user.id)

        if not jogador:
            await interaction.response.send_message(
                "Você ainda não entrou no Jogo do Abate.",
                ephemeral=True
            )
            return

        alvo_id = jogador[6]

        if not alvo_id:
            await interaction.response.send_message(
                "Você ainda não possui alvo definido.",
                ephemeral=True
            )
            return

        alvo = interaction.guild.get_member(alvo_id)

        embed = discord.Embed(
            title="🎯 SEU ALVO SECRETO",
            description=(
                f"🎯 **Alvo:** {alvo.mention if alvo else f'<@{alvo_id}>'}\n\n"
                "> O silêncio mantém o plano vivo."
            ),
            color=COR_ROXA
        )

        if alvo:
            embed.set_thumbnail(url=alvo.display_avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="criar_evento_abate",
        description="Cria um evento especial para o Jogo do Abate."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.check(canal_valido)
    @app_commands.checks.has_permissions(administrator=True)
    async def criar_evento_abate(
        self,
        interaction: discord.Interaction,
        nome: str,
        descricao: str,
        multiplicador_abate: app_commands.Range[int, 1, 5] = 1,
        dano_extra: app_commands.Range[int, 0, 3] = 0
    ):
        criar_evento(nome, descricao, multiplicador_abate, dano_extra)

        embed = discord.Embed(
            title="💀 EVENTO ESPECIAL CRIADO",
            description=(
                f"**Nome:** {nome}\n"
                f"**Descrição:** {descricao}\n"
                f"**Multiplicador de abate:** x{multiplicador_abate}\n"
                f"**Dano extra:** +{dano_extra}\n\n"
                "Use `/listar_eventos_abate` para ver o ID e ativar."
            ),
            color=COR_ROXA
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        log = discord.Embed(
            title="📜 LOG — EVENTO CRIADO",
            description=(
                f"**Nome:** {nome}\n"
                f"**Multiplicador:** x{multiplicador_abate}\n"
                f"**Dano extra:** +{dano_extra}\n"
                f"**Criado por:** {interaction.user.mention}"
            ),
            color=COR_ROXA
        )
        await enviar_log(interaction.guild, log)

    @app_commands.command(
        name="listar_eventos_abate",
        description="Lista os eventos especiais criados."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.check(canal_valido)
    @app_commands.checks.has_permissions(administrator=True)
    async def listar_eventos_abate(self, interaction: discord.Interaction):
        eventos = listar_eventos()

        if not eventos:
            await interaction.response.send_message("Nenhum evento criado ainda.", ephemeral=True)
            return

        descricao = ""

        for evento in eventos[:10]:
            evento_id, nome, desc, mult, dano, ativo = evento
            status = "🟢 ATIVO" if ativo else "⚫ INATIVO"
            descricao += (
                f"`ID {evento_id}` — **{nome}** {status}\n"
                f"↳ x{mult} abate • +{dano} dano\n"
                f"↳ {desc}\n\n"
            )

        embed = discord.Embed(
            title="💀 EVENTOS DO ABATE",
            description=descricao,
            color=COR_ROXA
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="ativar_evento_abate",
        description="Ativa um evento especial pelo ID."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.check(canal_valido)
    @app_commands.checks.has_permissions(administrator=True)
    async def ativar_evento_abate(self, interaction: discord.Interaction, evento_id: int):
        ativar_evento(evento_id)
        evento = buscar_evento_ativo()

        if not evento:
            await interaction.response.send_message("Evento não encontrado.", ephemeral=True)
            return

        _, nome, descricao, multiplicador, dano_extra, ativo = evento

        embed = discord.Embed(
            title="💀 EVENTO ESPECIAL ATIVADO",
            description=(
                f"## {nome}\n"
                f"{descricao}\n\n"
                f"⚔️ **Abates:** x{multiplicador}\n"
                f"🩸 **Dano extra:** +{dano_extra}\n\n"
                "> As regras do ritual foram alteradas."
            ),
            color=COR_VERMELHA
        )

        await interaction.response.send_message(embed=embed)
        await anunciar_evento(interaction.guild, embed=embed)

        log = discord.Embed(
            title="📜 LOG — EVENTO ATIVADO",
            description=(
                f"**Evento:** {nome}\n"
                f"**ID:** {evento_id}\n"
                f"**Ativado por:** {interaction.user.mention}"
            ),
            color=COR_VERMELHA
        )
        await enviar_log(interaction.guild, log)

    @app_commands.command(
        name="encerrar_evento_abate",
        description="Encerra qualquer evento especial ativo."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.check(canal_valido)
    @app_commands.checks.has_permissions(administrator=True)
    async def encerrar_evento_abate(self, interaction: discord.Interaction):
        encerrar_eventos()

        embed = discord.Embed(
            title="🧿 EVENTO ENCERRADO",
            description="As regras especiais foram removidas. O ritual voltou ao estado normal.",
            color=COR_ROXA
        )

        await interaction.response.send_message(embed=embed)
        await anunciar_evento(interaction.guild, embed=embed)

        log = discord.Embed(
            title="📜 LOG — EVENTO ENCERRADO",
            description=f"Evento encerrado por {interaction.user.mention}.",
            color=COR_ROXA
        )
        await enviar_log(interaction.guild, log)

    @app_commands.command(
        name="registrar_abate",
        description="Registra um abate e remove vida do perdedor."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.check(canal_valido)
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

        evento = buscar_evento_ativo()

        multiplicador = 1
        dano_total = 1
        evento_nome = None

        if evento:
            _, evento_nome, descricao, multiplicador, dano_extra, ativo = evento
            dano_total += dano_extra

        adicionar_abate(vencedor.id, quantidade=multiplicador)
        jogador_perdedor = remover_vida(perdedor.id, quantidade=dano_total)

        vidas = jogador_perdedor[2]
        status = jogador_perdedor[5]

        jogador_vencedor = buscar_jogador(vencedor.id)
        alvo_do_vencedor = jogador_vencedor[6] if jogador_vencedor else None
        era_alvo = alvo_do_vencedor == perdedor.id

        if era_alvo:
            definir_alvo(vencedor.id, None)

        embed = discord.Embed(
            title="⚔️ ABATE REGISTRADO",
            description=(
                f"🏆 **Vencedor:** {vencedor.mention}\n"
                f"🩸 **Perdedor:** {perdedor.mention}\n"
                f"📌 **Motivo:** {motivo}\n\n"
                f"⚔️ **Abates recebidos:** +{multiplicador}\n"
                f"🩸 **Dano aplicado:** -{dano_total} vida(s)\n"
                f"❤️ **Vidas restantes:** {gerar_barra_vidas(vidas)} `({vidas}/3)`"
            ),
            color=COR_VERMELHA
        )

        if evento_nome:
            embed.add_field(
                name="💀 Evento Ativo",
                value=f"Este abate foi afetado por **{evento_nome}**.",
                inline=False
            )

        if era_alvo:
            embed.add_field(
                name="🎯 ALVO CONCLUÍDO",
                value=f"{vencedor.mention} eliminou seu alvo secreto.",
                inline=False
            )

        if status == "eliminado":
            embed.add_field(
                name="💀 ELIMINAÇÃO CONFIRMADA",
                value=f"{perdedor.mention} foi eliminado do **Jogo do Abate**.",
                inline=False
            )

        embed.set_thumbnail(url=perdedor.display_avatar.url)
        embed.set_footer(text="RitualBot • Registro oficial de abate")

        await interaction.response.send_message(embed=embed)

        log = discord.Embed(
            title="📜 LOG — ABATE REGISTRADO",
            description=(
                f"🏆 **Vencedor:** {vencedor.mention}\n"
                f"🩸 **Perdedor:** {perdedor.mention}\n"
                f"📌 **Motivo:** {motivo}\n"
                f"⚔️ **Abates recebidos:** +{multiplicador}\n"
                f"🩸 **Dano aplicado:** -{dano_total}\n"
                f"❤️ **Vidas restantes:** {vidas}\n"
                f"👤 **Registrado por:** {interaction.user.mention}"
            ),
            color=COR_VERDE
        )

        if era_alvo:
            log.add_field(
                name="🎯 Alvo secreto concluído",
                value=f"{vencedor.mention} concluiu o alvo contra {perdedor.mention}.",
                inline=False
            )

        if status == "eliminado":
            log.add_field(
                name="💀 Eliminação",
                value=f"{perdedor.mention} foi eliminado do ritual.",
                inline=False
            )

            anuncio_eliminacao = discord.Embed(
                title="💀 ELIMINAÇÃO CONFIRMADA",
                description=(
                    f"{perdedor.mention} foi eliminado do **Jogo do Abate**.\n\n"
                    "> O ritual cobrou seu preço."
                ),
                color=COR_VERMELHA
            )
            anuncio_eliminacao.set_thumbnail(url=perdedor.display_avatar.url)
            await anunciar_evento(interaction.guild, embed=anuncio_eliminacao)

        await enviar_log(interaction.guild, log)

    @app_commands.command(
        name="ranking_abate",
        description="Mostra o ranking geral do Jogo do Abate."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.check(canal_valido)
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
    @app_commands.check(canal_valido)
    @app_commands.checks.has_permissions(administrator=True)
    async def resetar_abate_cmd(self, interaction: discord.Interaction):
        resetar_jogo()

        embed = discord.Embed(
            title="🩸 RITUAL RESETADO",
            description="Todos os registros do **Jogo do Abate** foram apagados.",
            color=COR_VERMELHA
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        log = discord.Embed(
            title="📜 LOG — RITUAL RESETADO",
            description=f"O Jogo do Abate foi resetado por {interaction.user.mention}.",
            color=COR_VERMELHA
        )
        await enviar_log(interaction.guild, log)

    # =========================================
    # COMANDO PREFIXO — PAINEL LIMPO
    # Use: !painel_abate
    # O bot apaga a mensagem e envia apenas o painel.
    # =========================================

    @commands.command(name="painel_abate")
    @commands.has_permissions(administrator=True)
    async def painel_abate_prefix(self, ctx: commands.Context):
        if ctx.channel.id != CANAL_ABATE_ID:
            return

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

        embed = discord.Embed(
            title="🩸 JOGO DO ABATE — RITUAL PRINCIPAL",
            description=(
                "```ansi\n"
                "\u001b[35mO ritual foi iniciado.\u001b[0m\n"
                "```\n"
                "A partir deste momento, cada escolha pode definir seu destino.\n\n"
                "🎯 **Alvos secretos por DM**\n"
                "📜 **Contratos e desafios**\n"
                "❤️ **Cada participante possui 3 vidas**\n"
                "💀 **Eventos especiais podem alterar o jogo**\n"
                "📊 **Ranking atualizado em tempo real**\n\n"
                "> **Sobreviva. Cumpra. Elimine.**"
            ),
            color=COR_ROXA
        )

        embed.add_field(
            name="⚠️ Aviso",
            value="Alguns nomes serão marcados. Nem todos permanecerão de pé.",
            inline=False
        )

        if avatar_bot(self.bot):
            embed.set_thumbnail(url=avatar_bot(self.bot))

        if BANNER_URL:
            embed.set_image(url=BANNER_URL)

        embed.set_footer(text="Família Sant's • RitualBot • O plano segue em andamento")

        await ctx.send(embed=embed, view=PainelAbate(self.bot))


async def setup(bot: commands.Bot):
    await bot.add_cog(Abate(bot))
