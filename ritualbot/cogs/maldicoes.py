import random
import asyncio
import sqlite3
import datetime
import discord
from discord.ext import commands
from discord import app_commands

COR_ROXA_JUJUTSU = 0x6A00FF

CANAL_MALDICOES_ID = 1499600179244830730
CANAL_LOG_MALDICOES_ID = 1500543560834089272

DB_MALDICOES = "maldicoes.db"

# Tempo normal
TEMPO_MINIMO = 600      # 10 minutos
TEMPO_MAXIMO = 2700     # 45 minutos

# Tempo de madrugada
TEMPO_MADRUGADA_MIN = 300    # 5 minutos
TEMPO_MADRUGADA_MAX = 1200   # 20 minutos

TEMPO_EXPIRACAO = 300  # 5 minutos

CARGOS_PROGRESSAO = [
    (50, 1500547442003673220),
    (30, 1500545859643768882),
    (15, 1500545858247332000),
    (5, 1500545862743621782),
]

MALDICOES = [
    {
        "nome": "Mahito",
        "descricao": "A alma foi tocada... uma presença distorcida surgiu no domínio.",
        "imagem": "https://media.tenor.com/rzLycKqpA_EAAAAd/mahito-domain-expansion.gif",
        "chance": 20,
        "cargo_id": 123456789012345678,
        "rara": False,
    },
    {
        "nome": "Mahoraga",
        "descricao": "A roda começou a girar... adapte-se ou seja destruído.",
        "imagem": "https://media.tenor.com/1qESUcxlIRMAAAAC/mahoraga-then-shadows.gif",
        "chance": 6,
        "cargo_id": 123456789012345678,
        "rara": True,
    },
    {
        "nome": "Sukuna",
        "descricao": "O Rei das Maldições despertou. O domínio foi aberto.",
        "imagem": "https://media.tenor.com/RAp5YpmEH5EAAAAd/jujutsu-kaisen-shibuya-arc-sukuna-shibuya-arc.gif",
        "chance": 3,
        "cargo_id": 123456789012345678,
        "rara": True,
    },
    {
        "nome": "Maldição Comum",
        "descricao": "Uma maldição fraca apareceu nas sombras do servidor.",
        "imagem": "https://media.tenor.com/0Vr8KlT2j1kAAAAd/jujutsu-kaisen.gif",
        "chance": 60,
        "cargo_id": 123456789012345678,
        "rara": False,
    },
    {
        "nome": "Maldição Especial",
        "descricao": "Uma energia amaldiçoada perigosa tomou conta do ambiente.",
        "imagem": "https://media.tenor.com/CKTB0HiHuOAAAAAC/finger-bearer-jjk.gif",
        "chance": 30,
        "cargo_id": 123456789012345678,
        "rara": False,
    },
]


def criar_tabela_maldicoes():
    conn = sqlite3.connect(DB_MALDICOES)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exorcistas (
            user_id INTEGER PRIMARY KEY,
            vitorias INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def adicionar_vitoria(user_id: int):
    conn = sqlite3.connect(DB_MALDICOES)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO exorcistas (user_id, vitorias)
        VALUES (?, 1)
        ON CONFLICT(user_id)
        DO UPDATE SET vitorias = vitorias + 1
    """, (user_id,))

    conn.commit()
    conn.close()


def pegar_vitorias(user_id: int):
    conn = sqlite3.connect(DB_MALDICOES)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT vitorias FROM exorcistas WHERE user_id = ?",
        (user_id,)
    )

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else 0


def pegar_ranking(limit: int = 10):
    conn = sqlite3.connect(DB_MALDICOES)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, vitorias
        FROM exorcistas
        ORDER BY vitorias DESC
        LIMIT ?
    """, (limit,))

    resultado = cursor.fetchall()
    conn.close()
    return resultado


def pegar_proximo_rank(vitorias: int):
    ranks = sorted(CARGOS_PROGRESSAO, key=lambda x: x[0])

    for requisito, cargo_id in ranks:
        if vitorias < requisito:
            return requisito, cargo_id

    return None, None


def escolher_maldicao():
    # 12% de chance de aparecer maldição rara
    if random.randint(1, 100) <= 12:
        raras = [m for m in MALDICOES if m.get("rara")]
        return random.choice(raras)

    comuns = [m for m in MALDICOES if not m.get("rara")]
    return random.choice(comuns)


def buscar_maldicao_por_nome(nome: str):
    nome = nome.lower().strip()

    for maldicao in MALDICOES:
        if maldicao["nome"].lower() == nome:
            return maldicao

    return None


async def atualizar_cargo_progressao(member: discord.Member):
    vitorias = pegar_vitorias(member.id)

    cargo_novo = None

    for requisito, cargo_id in CARGOS_PROGRESSAO:
        if vitorias >= requisito:
            cargo_novo = member.guild.get_role(cargo_id)
            break

    if not cargo_novo:
        return None

    cargos_remover = []

    for _, cargo_id in CARGOS_PROGRESSAO:
        cargo = member.guild.get_role(cargo_id)

        if cargo and cargo in member.roles and cargo != cargo_novo:
            cargos_remover.append(cargo)

    if cargos_remover:
        await member.remove_roles(
            *cargos_remover,
            reason="Atualização de rank de exorcista"
        )

    if cargo_novo not in member.roles:
        await member.add_roles(
            cargo_novo,
            reason="Novo rank de exorcista desbloqueado"
        )
        return cargo_novo

    return None


class BotaoExorcizar(discord.ui.View):
    def __init__(self, maldicao):
        super().__init__(timeout=TEMPO_EXPIRACAO)
        self.maldicao = maldicao
        self.derrotada = False
        self.cooldown = set()
        self.mensagem = None

    async def on_timeout(self):
        if self.derrotada:
            return

        for item in self.children:
            item.disabled = True

        if self.mensagem:
            try:
                await self.mensagem.edit(view=self)
                await self.mensagem.channel.send(
                    f"🌑 **{self.maldicao['nome']} desapareceu nas sombras...**\n"
                    f"Ninguém conseguiu exorcizá-la a tempo."
                )
            except Exception as e:
                print(f"[ERRO AO EXPIRAR MALDIÇÃO] {e}")

    async def remover_cooldown(self, user_id: int):
        await asyncio.sleep(5)
        self.cooldown.discard(user_id)

    @discord.ui.button(
        label="Tentar Exorcizar",
        emoji="🧿",
        style=discord.ButtonStyle.danger
    )
    async def tentar_exorcizar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if self.derrotada:
            await interaction.response.send_message(
                "💀 Essa maldição já foi derrotada.",
                ephemeral=True
            )
            return

        if interaction.user.id in self.cooldown:
            await interaction.response.send_message(
                "⏳ Você acabou de tentar exorcizar. Espere alguns segundos.",
                ephemeral=True
            )
            return

        self.cooldown.add(interaction.user.id)
        asyncio.create_task(self.remover_cooldown(interaction.user.id))

        sorteio = random.randint(1, 100)

        if sorteio <= self.maldicao["chance"]:
            self.derrotada = True
            adicionar_vitoria(interaction.user.id)

            cargo_maldicao = interaction.guild.get_role(self.maldicao["cargo_id"])
            cargo_progressao = None

            try:
                if cargo_maldicao:
                    await interaction.user.add_roles(
                        cargo_maldicao,
                        reason=f"Derrotou a maldição {self.maldicao['nome']}"
                    )

                cargo_progressao = await atualizar_cargo_progressao(interaction.user)

            except discord.Forbidden:
                await interaction.response.send_message(
                    "⚠️ A maldição foi derrotada, mas eu não tenho permissão para entregar cargos.",
                    ephemeral=True
                )
                return

            for item in self.children:
                item.disabled = True

            await interaction.response.edit_message(view=self)

            vitorias = pegar_vitorias(interaction.user.id)

            mensagem = (
                f"🧿 {interaction.user.mention} **derrotou a {self.maldicao['nome']}!**\n"
                f"🏆 Vitória registrada: **{vitorias}** maldição(ões) derrotada(s)."
            )

            if cargo_maldicao:
                mensagem += f"\n🎖️ Cargo recebido: {cargo_maldicao.mention}"

            if cargo_progressao:
                mensagem += (
                    f"\n\n🔥 **SUBIU DE RANK!**"
                    f"\n📈 Novo cargo desbloqueado: {cargo_progressao.mention}"
                    f"\n👁️ Sua energia amaldiçoada evoluiu."
                )

            proximo_requisito, proximo_cargo_id = pegar_proximo_rank(vitorias)

            if proximo_requisito:
                faltam = proximo_requisito - vitorias
                proximo_cargo = interaction.guild.get_role(proximo_cargo_id)

                if proximo_cargo:
                    mensagem += (
                        f"\n\n📊 **Progresso:** `{vitorias}/{proximo_requisito}` vitórias"
                        f"\n🎯 Faltam **{faltam}** para alcançar {proximo_cargo.mention}"
                    )
            else:
                mensagem += "\n\n👑 **Você já alcançou o rank máximo de exorcista.**"

            await interaction.followup.send(mensagem)

            canal_log = interaction.guild.get_channel(CANAL_LOG_MALDICOES_ID)

            if canal_log:
                embed_log = discord.Embed(
                    title="📜 Maldição Exorcizada",
                    description=(
                        f"👤 Exorcista: {interaction.user.mention}\n"
                        f"💀 Maldição: **{self.maldicao['nome']}**\n"
                        f"🎲 Chance: **{self.maldicao['chance']}%**\n"
                        f"🏆 Total de vitórias: **{vitorias}**"
                    ),
                    color=COR_ROXA_JUJUTSU
                )

                if cargo_maldicao:
                    embed_log.add_field(
                        name="🎖️ Cargo da Maldição",
                        value=cargo_maldicao.mention,
                        inline=False
                    )

                if cargo_progressao:
                    embed_log.add_field(
                        name="📈 Progressão",
                        value=f"Novo cargo: {cargo_progressao.mention}",
                        inline=False
                    )

                embed_log.set_footer(text="Família Sant's • Logs de Maldições")
                await canal_log.send(embed=embed_log)

        else:
            await interaction.response.send_message(
                f"❌ {interaction.user.mention} tentou exorcizar **{self.maldicao['nome']}**, mas falhou...",
                ephemeral=False
            )


class Maldicoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tarefa_maldicoes = None
        criar_tabela_maldicoes()

    async def cog_load(self):
        self.tarefa_maldicoes = asyncio.create_task(self.sistema_maldicoes())

    def cog_unload(self):
        if self.tarefa_maldicoes:
            self.tarefa_maldicoes.cancel()

    async def enviar_maldicao(self, canal, manual=False, maldicao_especifica=None):
        maldicao = maldicao_especifica or escolher_maldicao()

        extra = (
            "⚠️ Invocada manualmente."
            if manual
            else f"⏳ Essa maldição ficará ativa por **{TEMPO_EXPIRACAO // 60} minutos**."
        )

        embed = discord.Embed(
            title=f"💀 {maldicao['nome']} apareceu!",
            description=(
                f"{maldicao['descricao']}\n\n"
                f"🧿 Clique no botão abaixo para tentar exorcizar.\n"
                f"🎲 Chance de vitória: **{maldicao['chance']}%**\n\n"
                f"{extra}"
            ),
            color=COR_ROXA_JUJUTSU
        )

        embed.set_image(url=maldicao["imagem"])
        embed.set_footer(text="Família Sant's • Maldições Aleatórias")

        view = BotaoExorcizar(maldicao)

        mensagem = await canal.send(
            embed=embed,
            view=view
        )

        view.mensagem = mensagem

    async def sistema_maldicoes(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            agora = datetime.datetime.now()
            hora = agora.hour

            if 0 <= hora <= 5:
                tempo = random.randint(TEMPO_MADRUGADA_MIN, TEMPO_MADRUGADA_MAX)
            else:
                tempo = random.randint(TEMPO_MINIMO, TEMPO_MAXIMO)

            await asyncio.sleep(tempo)

            canal = self.bot.get_channel(CANAL_MALDICOES_ID)

            if not canal:
                print("[MALDIÇÕES] Canal não encontrado.")
                continue

            try:
                await self.enviar_maldicao(canal)
            except Exception as e:
                print(f"[ERRO MALDIÇÕES] {e}")

    @commands.command(name="maldicao")
    @commands.has_permissions(administrator=True)
    async def spawn_maldicao(self, ctx, *, nome: str = None):
        if nome:
            maldicao = buscar_maldicao_por_nome(nome)

            if not maldicao:
                nomes = ", ".join([m["nome"] for m in MALDICOES])
                await ctx.reply(
                    f"❌ Maldição não encontrada.\n"
                    f"Use uma dessas: `{nomes}`"
                )
                return

            await self.enviar_maldicao(ctx.channel, manual=True, maldicao_especifica=maldicao)
            return

        await self.enviar_maldicao(ctx.channel, manual=True)

    @spawn_maldicao.error
    async def spawn_maldicao_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ Apenas administradores podem invocar uma maldição.")
        else:
            await ctx.reply("⚠️ Ocorreu um erro ao invocar a maldição.")
            print(f"[ERRO COMANDO MALDIÇÃO] {error}")

    @app_commands.command(
        name="ranking_exorcistas",
        description="Mostra o ranking dos maiores exorcistas do servidor."
    )
    async def ranking_exorcistas(self, interaction: discord.Interaction):
        ranking = pegar_ranking(10)

        if not ranking:
            await interaction.response.send_message(
                "💀 Nenhuma maldição foi derrotada ainda.",
                ephemeral=True
            )
            return

        texto = ""

        for posicao, (user_id, vitorias) in enumerate(ranking, start=1):
            membro = interaction.guild.get_member(user_id)
            nome = membro.mention if membro else f"`{user_id}`"

            medalha = ["🥇", "🥈", "🥉"][posicao - 1] if posicao <= 3 else f"**{posicao}º**"
            texto += f"{medalha} {nome} — 🧿 **{vitorias}** vitória(s)\n"

        embed = discord.Embed(
            title="🏆 Ranking de Exorcistas",
            description=texto,
            color=COR_ROXA_JUJUTSU
        )

        embed.set_footer(text="Família Sant's • Sistema de Maldições")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Maldicoes(bot))