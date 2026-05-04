import random
import asyncio
import sqlite3
import datetime
import discord
from discord.ext import commands
from discord import app_commands

from utils.db import (
    buscar_jogador,
    listar_jogadores_vivos,
    adicionar_abate,
    remover_vida,
    conectar,
)

COR_ROXA_JUJUTSU = 0x6A00FF
COR_VERMELHA = 0xE63946
COR_VERDE = 0x2ECC71

GUILD_ID = 1480334256763961465

CANAL_MALDICOES_ID = 1499600179244830730
CANAL_LOG_MALDICOES_ID = 1500543560834089272

DB_MALDICOES = "maldicoes.db"

VIDAS_MAXIMAS = 300

TEMPO_MINIMO = 600
TEMPO_MAXIMO = 2700

TEMPO_MADRUGADA_MIN = 300
TEMPO_MADRUGADA_MAX = 1200

TEMPO_EXPIRACAO = 300
TEMPO_DELETAR_FALHA = 8
TEMPO_DELETAR_VITORIA = 25
COOLDOWN_EXORCIZAR = 5
AVISO_EXPIRACAO = 60

CARGOS_PROGRESSAO = [
    (50, 1500547442003673220),
    (30, 1500545859643768882),
    (15, 1500545858247332000),
    (5, 1500545862743621782),
]

MALDICOES = [
    {
        "nome": "Maldição Comum",
        "descricao": "Uma maldição fraca apareceu nas sombras do servidor.",
        "imagem": "https://media.tenor.com/0Vr8KlT2j1kAAAAd/jujutsu-kaisen.gif",
        "chance": 35,
        "peso_spawn": 35,
        "cargo_id": 123456789012345678,
        "bonus_abate": 0,
        "dano_falha": 1,
        "dano_expiracao": 1,
    },
    {
        "nome": "Maldição Especial",
        "descricao": "Uma energia amaldiçoada perigosa tomou conta do ambiente.",
        "imagem": "https://media.tenor.com/CKTB0HiHuOAAAAAC/finger-bearer-jjk.gif",
        "chance": 20,
        "peso_spawn": 25,
        "cargo_id": 123456789012345678,
        "bonus_abate": 1,
        "dano_falha": 2,
        "dano_expiracao": 2,
    },
    {
        "nome": "Mahito",
        "descricao": "A alma foi tocada... uma presença distorcida surgiu no domínio.",
        "imagem": "https://media.tenor.com/rzLycKqpA_EAAAAd/mahito-domain-expansion.gif",
        "chance": 3,
        "peso_spawn": 14,
        "cargo_id": 123456789012345678,
        "bonus_abate": 2,
        "dano_falha": 3,
        "dano_expiracao": 3,
    },
    {
        "nome": "Mahoraga",
        "descricao": "A roda começou a girar... adapte-se ou seja destruído.",
        "imagem": "https://media.tenor.com/1qESUcxlIRMAAAAC/mahoraga-then-shadows.gif",
        "chance": 5,
        "peso_spawn": 6,
        "cargo_id": 123456789012345678,
        "bonus_abate": 3,
        "dano_falha": 5,
        "dano_expiracao": 6,
    },
    {
        "nome": "Sukuna",
        "descricao": "O Rei das Maldições despertou. O domínio foi aberto.",
        "imagem": "https://media.tenor.com/RAp5YpmEH5EAAAAd/jujutsu-kaisen-shibuya-arc-sukuna-shibuya-arc.gif",
        "chance": 2,
        "peso_spawn": 3,
        "cargo_id": 123456789012345678,
        "bonus_abate": 5,
        "dano_falha": 7,
        "dano_expiracao": 8,
    },
    {
        "nome": "Jogo",
        "descricao": "O vulcão despertou... o calor absoluto domina o campo.",
        "imagem": "https://c.tenor.com/e6A9UvvUAAYAAAAd/tenor.gif",
        "chance": 10,
        "peso_spawn": 10,
        "cargo_id": 123456789012345678,
        "bonus_abate": 2,
        "dano_falha": 4,
        "dano_expiracao": 4,
    },
    {
        "nome": "Hanami",
        "descricao": "A natureza rejeita a humanidade... raízes tomam o domínio.",
        "imagem": "https://c.tenor.com/HcLZrpaw2g0AAAAC/tenor.gif",
        "chance": 12,
        "peso_spawn": 12,
        "cargo_id": 123456789012345678,
        "bonus_abate": 2,
        "dano_falha": 3,
        "dano_expiracao": 3,
    },
    {
        "nome": "Dagon",
        "descricao": "O mar invadiu o domínio... você está cercado.",
        "imagem": "https://c.tenor.com/fVHf5gfybhgAAAAC/tenor.gif",
        "chance": 14,
        "peso_spawn": 12,
        "cargo_id": 123456789012345678,
        "bonus_abate": 2,
        "dano_falha": 3,
        "dano_expiracao": 3,
    },
    {
        "nome": "Choso",
        "descricao": "Sangue amaldiçoado corre pelo campo... o ataque será preciso.",
        "imagem": "https://c.tenor.com/rWC3ompXyoEAAAAC/tenor.gif",
        "chance": 8,
        "peso_spawn": 14,
        "cargo_id": 123456789012345678,
        "bonus_abate": 2,
        "dano_falha": 2,
        "dano_expiracao": 2,
    },
    {
        "nome": "Toji",
        "descricao": "Sem energia amaldiçoada... mas mortal.",
        "imagem": "https://c.tenor.com/ciFWBkRdnnAAAAAd/tenor.gif",
        "chance": 3,
        "peso_spawn": 5,
        "cargo_id": 123456789012345678,
        "bonus_abate": 3,
        "dano_falha": 5,
        "dano_expiracao": 5,
    },
    {
        "nome": "Rika",
        "descricao": "O amor distorcido tomou forma... uma presença esmagadora apareceu.",
        "imagem": "https://c.tenor.com/iK0fmiLdk_0AAAAC/tenor.gif",
        "chance": 4,
        "peso_spawn": 4,
        "cargo_id": 123456789012345678,
        "bonus_abate": 5,
        "dano_falha": 6,
        "dano_expiracao": 7,
},
]



def criar_tabela_maldicoes():
    conn = sqlite3.connect(DB_MALDICOES)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exorcistas (
            user_id INTEGER PRIMARY KEY,
            vitorias INTEGER DEFAULT 0,
            vitorias_semana INTEGER DEFAULT 0,
            vitorias_mes INTEGER DEFAULT 0
        )
    """)

    for coluna in ["vitorias_semana", "vitorias_mes"]:
        try:
            cursor.execute(f"ALTER TABLE exorcistas ADD COLUMN {coluna} INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


def adicionar_vitoria(user_id: int):
    conn = sqlite3.connect(DB_MALDICOES)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO exorcistas (user_id, vitorias, vitorias_semana, vitorias_mes)
        VALUES (?, 1, 1, 1)
        ON CONFLICT(user_id)
        DO UPDATE SET
            vitorias = vitorias + 1,
            vitorias_semana = vitorias_semana + 1,
            vitorias_mes = vitorias_mes + 1
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


def pegar_ranking(limit: int = 10, periodo: str = "geral"):
    conn = sqlite3.connect(DB_MALDICOES)
    cursor = conn.cursor()

    coluna = "vitorias"

    if periodo == "semanal":
        coluna = "vitorias_semana"
    elif periodo == "mensal":
        coluna = "vitorias_mes"

    cursor.execute(f"""
        SELECT user_id, {coluna}
        FROM exorcistas
        WHERE {coluna} > 0
        ORDER BY {coluna} DESC
        LIMIT ?
    """, (limit,))

    resultado = cursor.fetchall()
    conn.close()
    return resultado


def resetar_ranking_periodo(periodo: str):
    conn = sqlite3.connect(DB_MALDICOES)
    cursor = conn.cursor()

    if periodo == "semanal":
        cursor.execute("UPDATE exorcistas SET vitorias_semana = 0")
    elif periodo == "mensal":
        cursor.execute("UPDATE exorcistas SET vitorias_mes = 0")

    conn.commit()
    conn.close()


def pegar_proximo_rank(vitorias: int):
    ranks = sorted(CARGOS_PROGRESSAO, key=lambda x: x[0])

    for requisito, cargo_id in ranks:
        if vitorias < requisito:
            return requisito, cargo_id

    return None, None


def escolher_maldicao():
    pesos = [m.get("peso_spawn", 1) for m in MALDICOES]
    return random.choices(MALDICOES, weights=pesos, k=1)[0]


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


def aplicar_bonus_abate(user_id: int, quantidade: int):
    if quantidade <= 0:
        return False

    jogador = buscar_jogador(user_id)

    if not jogador:
        return False

    adicionar_abate(user_id, quantidade=quantidade)
    return True


def aplicar_dano_abate(user_id: int, quantidade: int):
    if quantidade <= 0:
        return None

    jogador = buscar_jogador(user_id)

    if not jogador:
        return None

    return remover_vida(user_id, quantidade=quantidade)


def restaurar_vida_total(user_id: int):
    jogador = buscar_jogador(user_id)

    if not jogador:
        return False

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE jogadores
        SET vidas = ?, status = 'vivo'
        WHERE user_id = ?
        """,
        (VIDAS_MAXIMAS, user_id)
    )

    conn.commit()
    conn.close()
    return True


def obter_familia_jogador(user_id: int):
    jogador = buscar_jogador(user_id)

    if not jogador:
        return "Livre"

    try:
        return jogador[7] or "Livre"
    except IndexError:
        return "Livre"


def calcular_chance_final(user_id: int, chance_base: int):
    familia = obter_familia_jogador(user_id)
    bonus = 0

    if "gojo" in familia.lower():
        bonus = 5

    return min(95, chance_base + bonus), bonus, familia


def sortear_drop_maldicao(nome_maldicao: str):
    drops_lendarios = {
        "sukuna": "Dedo Amaldiçoado do Sukuna",
        "mahoraga": "Roda da Adaptação",
        "rika": "Fragmento da Rainha das Maldições",
        "mahito": "Alma Transfigurada",
        "jogo": "Cinzas Vulcânicas",
        "hanami": "Raiz Amaldiçoada",
        "dagon": "Concha do Domínio Marinho",
        "toji": "Lâmina Sem Energia",
        "choso": "Sangue Condensado",
    }

    nome_lower = nome_maldicao.lower()
    chance = random.randint(1, 100)

    if chance <= 4:
        return {
            "raridade": "LENDÁRIO",
            "emoji": "🌟",
            "item": drops_lendarios.get(nome_lower, f"Relíquia de {nome_maldicao}"),
            "bonus_abate": 5,
        }

    if chance <= 15:
        return {
            "raridade": "ÉPICO",
            "emoji": "🟣",
            "item": f"Núcleo Especial de {nome_maldicao}",
            "bonus_abate": 3,
        }

    if chance <= 40:
        return {
            "raridade": "RARO",
            "emoji": "🔵",
            "item": f"Marca de {nome_maldicao}",
            "bonus_abate": 2,
        }

    return {
        "raridade": "COMUM",
        "emoji": "⚪",
        "item": "Fragmento Amaldiçoado",
        "bonus_abate": 1,
    }


def escolher_jogador_vivo_aleatorio():
    jogadores = listar_jogadores_vivos()

    if not jogadores:
        return None

    return random.choice(jogadores)


async def deletar_depois(mensagem: discord.Message, segundos: int):
    await asyncio.sleep(segundos)

    try:
        await mensagem.delete()
    except discord.NotFound:
        pass
    except discord.Forbidden:
        pass
    except discord.HTTPException:
        pass


class BotaoExorcizar(discord.ui.View):
    def __init__(self, maldicao):
        super().__init__(timeout=TEMPO_EXPIRACAO)
        self.maldicao = maldicao
        self.derrotada = False
        self.cooldown = set()
        self.mensagem = None

    async def aviso_quase_expirando(self):
        await asyncio.sleep(max(1, TEMPO_EXPIRACAO - AVISO_EXPIRACAO))

        if self.derrotada or not self.mensagem:
            return

        try:
            await self.mensagem.channel.send(
                f"⚠️ **Atenção!** A maldição **{self.maldicao['nome']}** atacará alguém em **{AVISO_EXPIRACAO} segundos** se ninguém derrotar.",
                delete_after=20
            )
        except Exception as e:
            print(f"[ERRO AVISO MALDIÇÃO] {e}")

    async def finalizar_visual_maldicao(self, exorcista: discord.Member | None = None):
        """Remove o botão e transforma a mensagem original em maldição finalizada."""
        if not self.mensagem:
            return

        try:
            descricao = (
                f"🧿 Exorcista: {exorcista.mention}\n"
                f"💀 Maldição: **{self.maldicao['nome']}**\n\n"
                "O botão foi removido para evitar novas tentativas."
                if exorcista
                else (
                    f"💀 Maldição: **{self.maldicao['nome']}**\n\n"
                    "Essa maldição já foi finalizada e não pode mais ser exorcizada."
                )
            )

            embed_derrotada = discord.Embed(
                title=f"✅ {self.maldicao['nome']} foi derrotada!",
                description=descricao,
                color=COR_VERDE
            )
            embed_derrotada.set_image(url=self.maldicao["imagem"])
            embed_derrotada.set_footer(text="Família Sant's • Maldição Finalizada")

            await self.mensagem.edit(embed=embed_derrotada, view=None)
        except Exception as e:
            print(f"[ERRO FINALIZAR VISUAL MALDIÇÃO] {e}")

    async def on_timeout(self):
        if self.derrotada:
            return

        for item in self.children:
            item.disabled = True

        if not self.mensagem:
            return

        try:
            await self.mensagem.edit(view=self)
        except Exception as e:
            print(f"[ERRO AO DESATIVAR BOTÃO] {e}")

        alvo = escolher_jogador_vivo_aleatorio()
        dano = self.maldicao.get("dano_expiracao", 1)

        if not alvo:
            try:
                await self.mensagem.channel.send(
                    f"🌑 **{self.maldicao['nome']} desapareceu nas sombras...**\n"
                    f"Nenhum jogador vivo foi encontrado para ser atacado.",
                    delete_after=15
                )
            except Exception as e:
                print(f"[ERRO AO EXPIRAR MALDIÇÃO] {e}")
            return

        alvo_id = alvo[0]
        alvo_mencao = f"<@{alvo_id}>"

        jogador_atacado = aplicar_dano_abate(alvo_id, dano)

        if not jogador_atacado:
            return

        vidas = jogador_atacado[2]
        status = jogador_atacado[5]

        texto = (
            f"🌑 **{self.maldicao['nome']} não foi exorcizada a tempo.**\n\n"
            f"💀 A maldição atacou {alvo_mencao}.\n"
            f"🩸 Dano causado: **-{dano} vida(s)**\n"
            f"❤️ Vidas restantes: **{vidas}/{VIDAS_MAXIMAS}**"
        )

        if status == "eliminado":
            texto += f"\n\n☠️ {alvo_mencao} foi eliminado do **Jogo do Abate**."

        try:
            await self.mensagem.channel.send(texto)
        except Exception as e:
            print(f"[ERRO AO ANUNCIAR ATAQUE DA MALDIÇÃO] {e}")

        try:
            canal_log = self.mensagem.guild.get_channel(CANAL_LOG_MALDICOES_ID)

            if canal_log:
                embed_log = discord.Embed(
                    title="💀 Maldição Atacou",
                    description=(
                        f"💀 Maldição: **{self.maldicao['nome']}**\n"
                        f"🎯 Alvo atingido: {alvo_mencao}\n"
                        f"🩸 Dano: **-{dano} vida(s)**\n"
                        f"❤️ Vidas restantes: **{vidas}/{VIDAS_MAXIMAS}**"
                    ),
                    color=COR_VERMELHA
                )

                if status == "eliminado":
                    embed_log.add_field(
                        name="☠️ Eliminação",
                        value=f"{alvo_mencao} foi eliminado pelo ataque da maldição.",
                        inline=False
                    )

                embed_log.set_footer(text="Família Sant's • Maldições Automáticas")
                await canal_log.send(embed=embed_log)

        except Exception as e:
            print(f"[ERRO LOG ATAQUE MALDIÇÃO] {e}")

    async def remover_cooldown(self, user_id: int):
        await asyncio.sleep(COOLDOWN_EXORCIZAR)
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
            await self.finalizar_visual_maldicao()

            await interaction.response.send_message(
                "💀 Essa maldição já foi derrotada e não pode mais ser exorcizada.",
                ephemeral=True
            )
            return

        if interaction.user.id in self.cooldown:
            await interaction.response.send_message(
                "⏳ Você acabou de tentar exorcizar. Espere 5 segundos.",
                ephemeral=True
            )
            return

        self.cooldown.add(interaction.user.id)
        asyncio.create_task(self.remover_cooldown(interaction.user.id))

        sorteio = random.randint(1, 100)
        chance_final, bonus_familia_chance, familia_jogador = calcular_chance_final(
            interaction.user.id,
            self.maldicao["chance"]
        )

        if sorteio <= chance_final:
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

            bonus = self.maldicao.get("bonus_abate", 0)
            bonus_aplicado = aplicar_bonus_abate(interaction.user.id, bonus)
            vida_restaurada = restaurar_vida_total(interaction.user.id)

            drop = sortear_drop_maldicao(self.maldicao["nome"])
            drop_aplicado = aplicar_bonus_abate(interaction.user.id, drop["bonus_abate"])

            for item in self.children:
                item.disabled = True

            await interaction.response.defer()
            await self.finalizar_visual_maldicao(interaction.user)

            vitorias = pegar_vitorias(interaction.user.id)

            mensagem = (
                f"🧿 {interaction.user.mention} **derrotou a {self.maldicao['nome']}!**\n"
                f"🏆 Vitória registrada: **{vitorias}** maldição(ões) derrotada(s)."
            )

            if cargo_maldicao:
                mensagem += f"\n🎖️ Cargo recebido: {cargo_maldicao.mention}"

            if bonus > 0:
                if bonus_aplicado:
                    mensagem += f"\n🩸 **Jogo do Abate:** +{bonus} ponto(s) de abate."
                else:
                    mensagem += "\n🩸 **Jogo do Abate:** bônus não aplicado, pois você não está registrado no ritual."

            if bonus_familia_chance > 0:
                mensagem += f"\n🔵 **Bônus da Família Gojo:** +{bonus_familia_chance}% de chance aplicado."

            if vida_restaurada:
                mensagem += f"\n❤️ **Vida restaurada:** {VIDAS_MAXIMAS}/{VIDAS_MAXIMAS}"

            if drop:
                mensagem += (
                    f"\n\n🎁 **DROP:** {drop['emoji']} **{drop['raridade']}**"
                    f"\n📦 Item: **{drop['item']}**"
                    f"\n⚔️ Bônus: +{drop['bonus_abate']} abate(s)"
                )

                if not drop_aplicado:
                    mensagem += "\n⚠️ Drop não aplicado no Abate, pois você não está registrado."

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

            msg_vitoria = await interaction.followup.send(
                mensagem,
                wait=True
            )

            asyncio.create_task(deletar_depois(msg_vitoria, TEMPO_DELETAR_VITORIA))

            canal_log = interaction.guild.get_channel(CANAL_LOG_MALDICOES_ID)

            if not canal_log:
                print(f"[LOG MALDIÇÕES] Canal de logs não encontrado: {CANAL_LOG_MALDICOES_ID}")

            if canal_log:
                embed_log = discord.Embed(
                    title="📜 Maldição Exorcizada",
                    description=(
                        f"👤 Exorcista: {interaction.user.mention}\n"
                        f"💀 Maldição: **{self.maldicao['nome']}**\n"
                        f"🎲 Chance base: **{self.maldicao['chance']}%**\n"
                        f"🎲 Chance final: **{chance_final}%**\n"
                        f"🏯 Família: **{familia_jogador}**\n"
                        f"🏆 Total de vitórias: **{vitorias}**"
                    ),
                    color=COR_VERDE
                )

                if cargo_maldicao:
                    embed_log.add_field(
                        name="🎖️ Cargo da Maldição",
                        value=cargo_maldicao.mention,
                        inline=False
                    )

                if bonus > 0:
                    embed_log.add_field(
                        name="🩸 Integração com Abate",
                        value=(
                            f"+{bonus} ponto(s) de abate aplicado(s)."
                            if bonus_aplicado
                            else "Jogador não registrado no Jogo do Abate."
                        ),
                        inline=False
                    )

                embed_log.add_field(
                    name="❤️ Vida Restaurada",
                    value=(
                        f"{VIDAS_MAXIMAS}/{VIDAS_MAXIMAS}"
                        if vida_restaurada
                        else "Não restaurada; jogador não registrado no Jogo do Abate."
                    ),
                    inline=False
                )

                embed_log.add_field(
                    name="🎁 Drop",
                    value=(
                        f"{drop['emoji']} **{drop['raridade']}**\n"
                        f"Item: **{drop['item']}**\n"
                        f"Bônus: +{drop['bonus_abate']} abate(s)"
                    ),
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
            dano = self.maldicao.get("dano_falha", 0)
            jogador_afetado = aplicar_dano_abate(interaction.user.id, dano)

            texto_falha = (
                f"❌ {interaction.user.mention} tentou exorcizar **{self.maldicao['nome']}**, mas falhou..."
            )

            if dano > 0:
                if jogador_afetado:
                    vidas = jogador_afetado[2]
                    status = jogador_afetado[5]

                    texto_falha += (
                        f"\n🩸 **Jogo do Abate:** você perdeu **{dano} vida(s)**."
                        f"\n❤️ Vidas restantes: **{vidas}/{VIDAS_MAXIMAS}**"
                    )

                    if status == "eliminado":
                        texto_falha += "\n💀 Você foi eliminado do ritual."
                else:
                    texto_falha += "\n🩸 Você não está registrado no Jogo do Abate, então não perdeu vida."

            await interaction.response.send_message(
                texto_falha,
                ephemeral=False
            )

            try:
                msg = await interaction.original_response()
                asyncio.create_task(deletar_depois(msg, TEMPO_DELETAR_FALHA))
            except Exception:
                pass


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
                f"🎲 Chance de vitória: **{maldicao['chance']}%**\n"
                f"🩸 Dano ao falhar: **-{maldicao.get('dano_falha', 0)} vida(s)**\n"
                f"🌑 Dano se ninguém derrotar: **-{maldicao.get('dano_expiracao', 0)} vida(s)**\n"
                f"⏳ Cooldown por jogador: **{COOLDOWN_EXORCIZAR}s**\n\n"
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
        asyncio.create_task(view.aviso_quase_expirando())

    async def sistema_maldicoes(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            hora = datetime.datetime.now().hour

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
        try:
            await ctx.message.delete()
        except Exception:
            pass

        if nome:
            maldicao = buscar_maldicao_por_nome(nome)

            if not maldicao:
                nomes = ", ".join([m["nome"] for m in MALDICOES])
                await ctx.send(
                    f"❌ Maldição não encontrada.\nUse uma dessas: `{nomes}`",
                    delete_after=10
                )
                return

            await self.enviar_maldicao(ctx.channel, manual=True, maldicao_especifica=maldicao)
            return

        await self.enviar_maldicao(ctx.channel, manual=True)

    @spawn_maldicao.error
    async def spawn_maldicao_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ Apenas administradores podem invocar uma maldição.", delete_after=8)
        else:
            await ctx.reply("⚠️ Ocorreu um erro ao invocar a maldição.", delete_after=8)
            print(f"[ERRO COMANDO MALDIÇÃO] {error}")

    @app_commands.command(
        name="ranking_exorcistas",
        description="Mostra o ranking dos maiores exorcistas do servidor."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ranking_exorcistas(self, interaction: discord.Interaction, periodo: str = "geral"):
        periodo = periodo.lower().strip()

        if periodo not in ["geral", "semanal", "mensal"]:
            periodo = "geral"

        ranking = pegar_ranking(10, periodo=periodo)

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
            title=f"🏆 Ranking de Exorcistas — {periodo.capitalize()}",
            description=texto,
            color=COR_ROXA_JUJUTSU
        )

        embed.set_footer(text="Família Sant's • Sistema de Maldições")
        await interaction.response.send_message(embed=embed)

    @commands.command(name="resetar_ranking_exorcistas")
    @commands.has_permissions(administrator=True)
    async def resetar_ranking_exorcistas(self, ctx, periodo: str = "semanal"):
        periodo = periodo.lower().strip()

        if periodo not in ["semanal", "mensal"]:
            await ctx.reply("❌ Use `!resetar_ranking_exorcistas semanal` ou `!resetar_ranking_exorcistas mensal`.", delete_after=10)
            return

        resetar_ranking_periodo(periodo)

        await ctx.reply(
            f"🔄 Ranking de exorcistas **{periodo}** resetado com sucesso.",
            delete_after=10
        )

    @resetar_ranking_exorcistas.error
    async def resetar_ranking_exorcistas_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ Apenas administradores podem resetar ranking.", delete_after=8)
        else:
            await ctx.reply("⚠️ Ocorreu um erro ao resetar o ranking.", delete_after=8)
            print(f"[ERRO RESET RANKING EXORCISTAS] {error}")



async def setup(bot):
    await bot.add_cog(Maldicoes(bot))