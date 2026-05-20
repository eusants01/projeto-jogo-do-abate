import random
import asyncio
import datetime
import time
import json
import discord
from discord.ext import commands
from discord import app_commands

from utils.db import (
    buscar_jogador,
    listar_jogadores_vivos,
    adicionar_abate,
    remover_vida,
    conectar,
    resetar_jogo,
)

from utils.economia import (
    criar_tabelas_economia,
    adicionar_vitoria,
    pegar_vitorias,
    pegar_ranking,
    resetar_ranking_periodo,
    pegar_corrupcao,
    adicionar_corrupcao,
    reduzir_corrupcao,
    adicionar_item,
    adicionar_buff,
    consumir_buff,
    quantidade_buff,
)


# Opcional: recompensa dos bosses em Moedas do Diabo.
# Se utils/cassino_db.py existir, os bosses também darão moedas.
try:
    from utils.cassino_db import adicionar_moedas
except Exception:
    adicionar_moedas = None

COR_ROXA_JUJUTSU = 0x6A00FF
COR_VERMELHA = 0xE63946
COR_VERDE = 0x2ECC71

GUILD_ID = 1480334256763961465

CANAL_MALDICOES_ID = 1499600179244830730
CANAL_LOG_MALDICOES_ID = 1500543560834089272

VIDAS_MAXIMAS = 750

TEMPO_MINIMO = 600
TEMPO_MAXIMO = 2700
TEMPO_MADRUGADA_MIN = 120
TEMPO_MADRUGADA_MAX = 800

TEMPO_EXPIRACAO = 300
TEMPO_DELETAR_FALHA = 4
TEMPO_DELETAR_VITORIA = 15
COOLDOWN_EXORCIZAR = 2
AVISO_EXPIRACAO = 60

ITEM_FRAGMENTO = "Fragmento Amaldiçoado"

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
        "corrupcao_falha": 1,
        "fragmentos_min": 5,
        "fragmentos_max": 12,
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
        "corrupcao_falha": 2,
        "fragmentos_min": 10,
        "fragmentos_max": 20,
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
        "corrupcao_falha": 4,
        "fragmentos_min": 20,
        "fragmentos_max": 35,
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
        "corrupcao_falha": 5,
        "fragmentos_min": 25,
        "fragmentos_max": 45,
    },
    {
        "nome": "Sukuna",
        "descricao": "O Rei das Maldições despertou. O domínio foi aberto.",
        "imagem": "https://media.tenor.com/RAp5YpmEH5EAAAAd/jujutsu-kaisen-shibuya-arc-sukuna-shibuya-arc.gif",
        "chance": 2,
        "peso_spawn": 3,
        "cargo_id": 123456789012345678,
        "bonus_abate": 5,
        "dano_falha": 10,
        "dano_expiracao": 8,
        "corrupcao_falha": 7,
        "fragmentos_min": 35,
        "fragmentos_max": 60,
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
        "corrupcao_falha": 3,
        "fragmentos_min": 15,
        "fragmentos_max": 30,
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
        "corrupcao_falha": 3,
        "fragmentos_min": 15,
        "fragmentos_max": 30,
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
        "corrupcao_falha": 3,
        "fragmentos_min": 15,
        "fragmentos_max": 30,
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
        "corrupcao_falha": 3,
        "fragmentos_min": 15,
        "fragmentos_max": 30,
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
        "corrupcao_falha": 4,
        "fragmentos_min": 25,
        "fragmentos_max": 45,
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
        "corrupcao_falha": 5,
        "fragmentos_min": 30,
        "fragmentos_max": 55,
    },
]


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


def status_corrupcao(corrupcao: int):
    if corrupcao >= 20:
        return "☠️ **Semi-Maldição**"
    if corrupcao >= 10:
        return "💀 **Marcado pela Maldição**"
    if corrupcao >= 5:
        return "🩸 **Instável**"
    return "🧿 **Estável**"


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
        await member.remove_roles(*cargos_remover, reason="Atualização de rank de exorcista")

    if cargo_novo not in member.roles:
        await member.add_roles(cargo_novo, reason="Novo rank de exorcista desbloqueado")
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

    if consumir_buff(user_id, "escudo", 1):
        quantidade = max(0, quantidade - 5)

    if quantidade <= 0:
        jogador = buscar_jogador(user_id)
        return jogador

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
        SET vidas = %s, status = 'vivo'
        WHERE user_id = %s
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

    corrupcao = pegar_corrupcao(user_id)
    penalidade_corrupcao = min(20, corrupcao)

    chance_final = chance_base + bonus - penalidade_corrupcao

    if consumir_buff(user_id, "sorte", 1):
        chance_final += 10

    return max(1, min(95, chance_final)), bonus, familia, penalidade_corrupcao, corrupcao


def sortear_drop_maldicao(nome_maldicao: str, user_id: int):
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

    sorte = random.randint(1, 100)

    if quantidade_buff(user_id, "sorte") > 0:
        consumir_buff(user_id, "sorte", 1)
        sorte -= 10

    nome_lower = nome_maldicao.lower()

    if sorte <= 4:
        return {"raridade": "LENDÁRIO", "emoji": "🌟", "item": drops_lendarios.get(nome_lower, f"Relíquia de {nome_maldicao}"), "bonus_abate": 5}
    if sorte <= 15:
        return {"raridade": "ÉPICO", "emoji": "🟣", "item": f"Núcleo Especial de {nome_maldicao}", "bonus_abate": 3}
    if sorte <= 40:
        return {"raridade": "RARO", "emoji": "🔵", "item": f"Marca de {nome_maldicao}", "bonus_abate": 2}

    return {"raridade": "COMUM", "emoji": "⚪", "item": ITEM_FRAGMENTO, "bonus_abate": 1}


def escolher_jogador_vivo_aleatorio():
    jogadores = listar_jogadores_vivos()
    if not jogadores:
        return None
    return random.choice(jogadores)


async def deletar_depois(mensagem: discord.Message, segundos: int):
    await asyncio.sleep(segundos)
    try:
        await mensagem.delete()
    except Exception:
        pass


class BotaoExorcizar(discord.ui.View):
    def __init__(self, maldicao):
        super().__init__(timeout=TEMPO_EXPIRACAO)
        self.maldicao = maldicao
        self.derrotada = False
        self.cooldown = set()
        self.mensagem = None
        self.exorcista_id = None

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
        if not self.mensagem:
            return

        try:
            descricao = (
                f"🧿 Exorcista: {exorcista.mention}\n"
                f"💀 Maldição: **{self.maldicao['nome']}**\n\n"
                "O botão foi removido para evitar novas tentativas."
                if exorcista
                else f"💀 Maldição: **{self.maldicao['nome']}**\n\nEssa maldição já foi finalizada."
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
            await self.mensagem.channel.send(
                f"🌑 **{self.maldicao['nome']} desapareceu nas sombras...**\nNenhum jogador vivo foi encontrado para ser atacado.",
                delete_after=15
            )
            return

        alvo_id = alvo[0]
        alvo_mencao = f"<@{alvo_id}>"

        jogador_atacado = aplicar_dano_abate(alvo_id, dano)
        adicionar_corrupcao(alvo_id, max(1, dano // 2))

        if not jogador_atacado:
            return

        vidas = jogador_atacado[2]
        status = jogador_atacado[5]
        corrupcao_atual = pegar_corrupcao(alvo_id)

        texto = (
            f"🌑 **{self.maldicao['nome']} não foi exorcizada a tempo.**\n\n"
            f"💀 A maldição atacou {alvo_mencao}.\n"
            f"🩸 Dano causado: **-{dano} vida(s)**\n"
            f"🧫 Corrupção: **{corrupcao_atual}** — {status_corrupcao(corrupcao_atual)}\n"
            f"❤️ Vidas restantes: **{vidas}/{VIDAS_MAXIMAS}**"
        )

        if status == "eliminado":
            texto += f"\n\n☠️ {alvo_mencao} foi eliminado do **Jogo do Abate**."

        await self.mensagem.channel.send(texto)

        canal_log = self.mensagem.guild.get_channel(CANAL_LOG_MALDICOES_ID)
        if canal_log:
            embed_log = discord.Embed(
                title="💀 Maldição Atacou",
                description=(
                    f"💀 Maldição: **{self.maldicao['nome']}**\n"
                    f"🎯 Alvo atingido: {alvo_mencao}\n"
                    f"🩸 Dano: **-{dano} vida(s)**\n"
                    f"🧫 Corrupção atual: **{corrupcao_atual}**\n"
                    f"❤️ Vidas restantes: **{vidas}/{VIDAS_MAXIMAS}**"
                ),
                color=COR_VERMELHA
            )
            embed_log.set_footer(text="Família Sant's • Maldições Automáticas")
            await canal_log.send(embed=embed_log)

    async def remover_cooldown(self, user_id: int):
        await asyncio.sleep(COOLDOWN_EXORCIZAR)
        self.cooldown.discard(user_id)

    @discord.ui.button(label="Tentar Exorcizar", emoji="🧿", style=discord.ButtonStyle.danger)
    async def tentar_exorcizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.derrotada:
            await self.finalizar_visual_maldicao()
            await interaction.response.send_message("💀 Essa maldição já foi derrotada.", ephemeral=True)
            return

        if interaction.user.id in self.cooldown:
            await interaction.response.send_message(f"⏳ Espere {COOLDOWN_EXORCIZAR} segundos.", ephemeral=True)
            return

        self.cooldown.add(interaction.user.id)
        asyncio.create_task(self.remover_cooldown(interaction.user.id))

        sorteio = random.randint(1, 100)
        chance_final, bonus_familia_chance, familia_jogador, penalidade_corrupcao, corrupcao_antes = calcular_chance_final(
            interaction.user.id,
            self.maldicao["chance"]
        )

        if sorteio <= chance_final:
            self.derrotada = True
            self.exorcista_id = interaction.user.id
            adicionar_vitoria(interaction.user.id)

            cargo_maldicao = interaction.guild.get_role(self.maldicao["cargo_id"])
            cargo_progressao = None

            try:
                if cargo_maldicao:
                    await interaction.user.add_roles(cargo_maldicao, reason=f"Derrotou a maldição {self.maldicao['nome']}")
                cargo_progressao = await atualizar_cargo_progressao(interaction.user)
            except discord.Forbidden:
                await interaction.response.send_message("⚠️ Não tenho permissão para entregar cargos.", ephemeral=True)
                return

            bonus = self.maldicao.get("bonus_abate", 0)
            bonus_aplicado = aplicar_bonus_abate(interaction.user.id, bonus)
            vida_restaurada = restaurar_vida_total(interaction.user.id)

            fragmentos = random.randint(self.maldicao.get("fragmentos_min", 5), self.maldicao.get("fragmentos_max", 15))
            adicionar_item(interaction.user.id, ITEM_FRAGMENTO, fragmentos)

            drop = sortear_drop_maldicao(self.maldicao["nome"], interaction.user.id)
            adicionar_item(interaction.user.id, drop["item"], 1)
            drop_aplicado = aplicar_bonus_abate(interaction.user.id, drop["bonus_abate"])

            nova_corrupcao = reduzir_corrupcao(interaction.user.id, 2)

            for item in self.children:
                item.disabled = True

            await interaction.response.defer()
            await self.finalizar_visual_maldicao(interaction.user)

            vitorias = pegar_vitorias(interaction.user.id)

            mensagem = (
                f"🧿 {interaction.user.mention} **derrotou a {self.maldicao['nome']}!**\n"
                f"🏆 Vitórias: **{vitorias}**\n"
                f"🧩 Fragmentos recebidos: **+{fragmentos}**\n"
                f"🎁 Drop: {drop['emoji']} **{drop['raridade']}** — **{drop['item']}**\n"
                f"🧫 Corrupção: **{corrupcao_antes} → {nova_corrupcao}** — {status_corrupcao(nova_corrupcao)}"
            )

            if cargo_maldicao:
                mensagem += f"\n🎖️ Cargo recebido: {cargo_maldicao.mention}"

            if bonus > 0:
                mensagem += f"\n🩸 **Jogo do Abate:** {'+' + str(bonus) + ' abate(s)' if bonus_aplicado else 'bônus não aplicado; jogador não registrado.'}"

            if bonus_familia_chance > 0:
                mensagem += f"\n🔵 **Bônus Família Gojo:** +{bonus_familia_chance}%"

            if penalidade_corrupcao > 0:
                mensagem += f"\n🩸 **Penalidade de Corrupção:** -{penalidade_corrupcao}%"

            if vida_restaurada:
                mensagem += f"\n❤️ Vida restaurada: **{VIDAS_MAXIMAS}/{VIDAS_MAXIMAS}**"

            if not drop_aplicado:
                mensagem += "\n⚠️ Bônus do drop no Abate não aplicado, pois você não está registrado."

            if cargo_progressao:
                mensagem += f"\n\n🔥 **SUBIU DE RANK!**\n📈 Novo cargo: {cargo_progressao.mention}"

            proximo_requisito, proximo_cargo_id = pegar_proximo_rank(vitorias)
            if proximo_requisito:
                faltam = proximo_requisito - vitorias
                proximo_cargo = interaction.guild.get_role(proximo_cargo_id)
                if proximo_cargo:
                    mensagem += f"\n\n📊 Progresso: `{vitorias}/{proximo_requisito}`\n🎯 Faltam **{faltam} vitórias** para o seu próximo grau"
            else:
                mensagem += "\n\n👑 Você já alcançou o rank máximo."

            msg_vitoria = await interaction.channel.send(mensagem)
            asyncio.create_task(deletar_depois(msg_vitoria, TEMPO_DELETAR_VITORIA))

            canal_log = interaction.guild.get_channel(CANAL_LOG_MALDICOES_ID)
            if canal_log:
                embed_log = discord.Embed(
                    title="📜 Maldição Exorcizada",
                    description=(
                        f"👤 Exorcista: {interaction.user.mention}\n"
                        f"💀 Maldição: **{self.maldicao['nome']}**\n"
                        f"🎲 Chance base: **{self.maldicao['chance']}%**\n"
                        f"🎲 Chance final: **{chance_final}%**\n"
                        f"🏯 Família: **{familia_jogador}**\n"
                        f"🧩 Fragmentos: **+{fragmentos}**\n"
                        f"🎁 Drop: {drop['emoji']} **{drop['item']}**\n"
                        f"🧫 Corrupção: **{nova_corrupcao}**"
                    ),
                    color=COR_VERDE
                )
                embed_log.set_footer(text="Família Sant's • Logs de Maldições")
                await canal_log.send(embed=embed_log)

        else:
            dano = self.maldicao.get("dano_falha", 0)
            corrupcao_ganha = self.maldicao.get("corrupcao_falha", 1)

            jogador_afetado = aplicar_dano_abate(interaction.user.id, dano)
            corrupcao_atual = adicionar_corrupcao(interaction.user.id, corrupcao_ganha)

            texto_falha = (
                f"❌ {interaction.user.mention} tentou exorcizar **{self.maldicao['nome']}**, mas falhou...\n"
                f"🧫 Corrupção recebida: **+{corrupcao_ganha}**\n"
                f"🩸 Corrupção atual: **{corrupcao_atual}** — {status_corrupcao(corrupcao_atual)}"
            )

            if dano > 0:
                if jogador_afetado:
                    vidas = jogador_afetado[2]
                    status = jogador_afetado[5]
                    texto_falha += f"\n🩸 Jogo do Abate: perdeu **{dano} vida(s)**.\n❤️ Vidas: **{vidas}/{VIDAS_MAXIMAS}**"
                    if status == "eliminado":
                        texto_falha += "\n💀 Você foi eliminado do ritual."
                else:
                    texto_falha += "\n🩸 Você não está registrado no Jogo do Abate, então não perdeu vida."

            await interaction.response.send_message(texto_falha, ephemeral=False)

            try:
                msg = await interaction.original_response()
                asyncio.create_task(deletar_depois(msg, TEMPO_DELETAR_FALHA))
            except Exception:
                pass


class Maldicoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tarefa_maldicoes = None
        criar_tabelas_economia()

    async def cog_load(self):
        self.tarefa_maldicoes = asyncio.create_task(self.sistema_maldicoes())

    def cog_unload(self):
        if self.tarefa_maldicoes:
            self.tarefa_maldicoes.cancel()

    async def enviar_maldicao(self, canal, manual=False, maldicao_especifica=None):
        maldicao = maldicao_especifica or escolher_maldicao()

        extra = "⚠️ Invocada manualmente." if manual else f"⏳ Ativa por **{TEMPO_EXPIRACAO // 60} minutos**."

        embed = discord.Embed(
            title=f"💀 {maldicao['nome']} apareceu!",
            description=(
                f"{maldicao['descricao']}\n\n"
                f"🧿 Clique no botão abaixo para tentar exorcizar.\n"
                f"🎲 Chance base: **{maldicao['chance']}%**\n"
                f"🩸 Dano ao falhar: **-{maldicao.get('dano_falha', 0)} vida(s)**\n"
                f"🧫 Corrupção ao falhar: **+{maldicao.get('corrupcao_falha', 1)}**\n"
                f"🌑 Dano se ninguém derrotar: **-{maldicao.get('dano_expiracao', 0)} vida(s)**\n\n"
                f"{extra}"
            ),
            color=COR_ROXA_JUJUTSU
        )
        embed.set_image(url=maldicao["imagem"])
        embed.set_footer(text="Família Sant's • Maldições Aleatórias")

        view = BotaoExorcizar(maldicao)
        mensagem = await canal.send(embed=embed, view=view)
        view.mensagem = mensagem
        asyncio.create_task(view.aviso_quase_expirando())

    async def sistema_maldicoes(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            hora = datetime.datetime.now().hour
            tempo = random.randint(TEMPO_MADRUGADA_MIN, TEMPO_MADRUGADA_MAX) if 0 <= hora <= 5 else random.randint(TEMPO_MINIMO, TEMPO_MAXIMO)
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
                await ctx.send(f"❌ Maldição não encontrada.\nUse: `{nomes}`", delete_after=10)
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

    @app_commands.command(name="ranking_exorcistas", description="Mostra o ranking dos maiores exorcistas.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ranking_exorcistas(self, interaction: discord.Interaction, periodo: str = "geral"):
        periodo = periodo.lower().strip()
        if periodo not in ["geral", "semanal", "mensal"]:
            periodo = "geral"

        ranking = pegar_ranking(10, periodo=periodo)

        if not ranking:
            await interaction.response.send_message("💀 Nenhuma maldição foi derrotada ainda.", ephemeral=True)
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
            await ctx.reply("❌ Use `!resetar_ranking_exorcistas semanal` ou `mensal`.", delete_after=10)
            return
        resetar_ranking_periodo(periodo)
        await ctx.reply(f"🔄 Ranking **{periodo}** resetado.", delete_after=10)


# ============================================================
# SISTEMA DE BOSSES INTEGRADO AO COG DE MALDIÇÕES
# ============================================================
# Opcional: recompensa em Moedas do Diabo.
# Se o arquivo utils/cassino_db.py existir, o boss também dará moedas.
try:
    from utils.cassino_db import adicionar_moedas
except Exception:
    adicionar_moedas = None


# =========================
# CORES
# =========================
COR_VERMELHA = 0xE63946
COR_VERDE = 0x2ECC71
COR_ROXA = 0x7B2CFF
COR_DOURADA = 0xF1C40F
COR_CASSINO = 0x8B0000


# =========================
# CONFIGURAÇÕES
# =========================
VIDAS_MAXIMAS = 750
CANAL_LOG_MALDICOES_ID = 1500543560834089272

TEMPO_APAGAR_ATAQUE = 5
COOLDOWN_ATAQUE = 5

BOSS_ATIVO = None

# =========================
# PERSISTÊNCIA ANTI-PERDA DE RAID
# =========================
# Salva o boss ativo no PostgreSQL para não perder HP/danos ao dar push/restart.
# Não cria arquivos novos e não mexe em dados de família/abate/inventário.

def criar_tabelas_raid():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS raid_boss_ativo (
            singleton BOOLEAN PRIMARY KEY DEFAULT TRUE,
            boss_nome TEXT NOT NULL,
            boss_json TEXT NOT NULL,
            canal_id BIGINT,
            mensagem_id BIGINT,
            vida INTEGER NOT NULL,
            max_vida INTEGER NOT NULL,
            danos_json TEXT NOT NULL DEFAULT '{}',
            ultimo_hit BIGINT,
            agressividade INTEGER NOT NULL DEFAULT 1,
            turnos INTEGER NOT NULL DEFAULT 0,
            finalizado BOOLEAN NOT NULL DEFAULT FALSE,
            iniciou_em TIMESTAMP DEFAULT NOW(),
            atualizado_em TIMESTAMP DEFAULT NOW()
        )
        """
    )
    conn.commit()
    conn.close()


def salvar_boss_ativo(view):
    if not view or view.finalizado:
        return

    try:
        criar_tabelas_raid()

        canal_id = view.mensagem.channel.id if view.mensagem else None
        mensagem_id = view.mensagem.id if view.mensagem else None

        dados_dano = {str(uid): int(dmg) for uid, dmg in view.danos.items()}

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO raid_boss_ativo (
                singleton, boss_nome, boss_json, canal_id, mensagem_id,
                vida, max_vida, danos_json, ultimo_hit, agressividade,
                turnos, finalizado, atualizado_em
            )
            VALUES (
                TRUE, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, NOW()
            )
            ON CONFLICT (singleton) DO UPDATE SET
                boss_nome = EXCLUDED.boss_nome,
                boss_json = EXCLUDED.boss_json,
                canal_id = EXCLUDED.canal_id,
                mensagem_id = EXCLUDED.mensagem_id,
                vida = EXCLUDED.vida,
                max_vida = EXCLUDED.max_vida,
                danos_json = EXCLUDED.danos_json,
                ultimo_hit = EXCLUDED.ultimo_hit,
                agressividade = EXCLUDED.agressividade,
                turnos = EXCLUDED.turnos,
                finalizado = EXCLUDED.finalizado,
                atualizado_em = NOW()
            """,
            (
                view.boss.get("nome"),
                json.dumps(view.boss, ensure_ascii=False),
                canal_id,
                mensagem_id,
                int(view.vida),
                int(view.max_vida),
                json.dumps(dados_dano, ensure_ascii=False),
                view.ultimo_hit,
                int(view.agressividade),
                int(view.turnos),
                bool(view.finalizado),
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[PERSISTÊNCIA RAID] Erro ao salvar boss ativo: {e}")


def carregar_boss_ativo():
    try:
        criar_tabelas_raid()

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT boss_json, canal_id, mensagem_id, vida, max_vida,
                   danos_json, ultimo_hit, agressividade, turnos, finalizado
            FROM raid_boss_ativo
            WHERE singleton = TRUE
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        boss_json, canal_id, mensagem_id, vida, max_vida, danos_json, ultimo_hit, agressividade, turnos, finalizado = row

        if finalizado:
            limpar_boss_ativo()
            return None

        danos_raw = json.loads(danos_json or "{}")
        danos = {int(uid): int(dmg) for uid, dmg in danos_raw.items()}

        return {
            "boss": json.loads(boss_json),
            "canal_id": canal_id,
            "mensagem_id": mensagem_id,
            "vida": int(vida),
            "max_vida": int(max_vida),
            "danos": danos,
            "ultimo_hit": int(ultimo_hit) if ultimo_hit else None,
            "agressividade": int(agressividade),
            "turnos": int(turnos),
        }
    except Exception as e:
        print(f"[PERSISTÊNCIA RAID] Erro ao carregar boss ativo: {e}")
        return None


def limpar_boss_ativo():
    try:
        criar_tabelas_raid()
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM raid_boss_ativo WHERE singleton = TRUE")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[PERSISTÊNCIA RAID] Erro ao limpar boss ativo: {e}")


def calcular_dano_com_buffs(user_id: int, dano_base: int):
    """
    Integração real com as lojas:
    - furia: +40% dano
    - critico: dobra dano
    - berserk: triplica dano, mas aumenta corrupção
    """
    dano = int(dano_base)
    efeitos = []

    if consumir_buff(user_id, "furia", 1):
        bonus = max(1, int(dano * 0.40))
        dano += bonus
        efeitos.append(f"🔥 Fúria +{bonus}")

    if consumir_buff(user_id, "critico", 1):
        dano *= 2
        efeitos.append("💥 Crítico x2")

    if consumir_buff(user_id, "berserk", 1):
        dano *= 3
        corrupcao = adicionar_corrupcao(user_id, 3)
        efeitos.append(f"☠️ Berserk x3 | Corrupção: {corrupcao}")

    return max(1, dano), efeitos


def aplicar_defesa_boss(user_id: int, dano: int):
    """
    Integração defensiva com a loja:
    - escudo reduz dano recebido do boss em 50%
    """
    dano = int(dano)

    if dano <= 0:
        return 0, False

    if consumir_buff(user_id, "escudo", 1):
        dano = max(0, dano // 2)
        return dano, True

    return dano, False



# =========================
# BOSSES
# =========================
BOSSES = [
    # =========================
    # JUJUTSU
    # =========================
    {
        "nome": "Sukuna",
        "categoria": "Jujutsu",
        "descricao": "O Rei das Maldições abriu seu domínio.",
        "imagem": "https://c.tenor.com/w3KbwTJ-F5IAAAAd/tenor.gif",
        "vida": 25000,
        "tempo": 600,
        "dano_min": 80,
        "dano_max": 150,
        "recompensa_participou": 1,
        "recompensa_top": 5,
        "recompensa_final": 3,
        "moedas_participou": 250,
        "moedas_top": 1200,
        "moedas_final": 900,
        "dano_falha": 12,
        "agressividade": 1,
        "agressividade_max": 8,
        "chance_ataque": 30,
        "chance_habilidade": 25,
        "habilidade": "corte_area",
        "dano_habilidade": 18,
        "drop_lendario": "Fragmento do Rei das Maldições",
        "frase": "A lâmina invisível já escolheu seus alvos.",
    },
    {
        "nome": "Mahoraga",
        "categoria": "Jujutsu",
        "descricao": "A roda gira. A adaptação começou.",
        "imagem": "https://c.tenor.com/mS_lFC5waJcAAAAC/tenor.gif",
        "vida": 15000,
        "tempo": 600,
        "dano_min": 50,
        "dano_max": 90,
        "recompensa_participou": 1,
        "recompensa_top": 4,
        "recompensa_final": 3,
        "moedas_participou": 220,
        "moedas_top": 1000,
        "moedas_final": 800,
        "dano_falha": 10,
        "agressividade": 1,
        "agressividade_max": 7,
        "chance_ataque": 22,
        "chance_habilidade": 45,
        "habilidade": "adaptacao",
        "dano_habilidade": 14,
        "drop_lendario": "Roda da Adaptação",
        "frase": "Quanto mais você ataca, mais ele entende.",
    },
    {
        "nome": "Bruna e Sants",
        "categoria": "Jujutsu",
        "descricao": "Uma história que jamais será apagada.",
        "imagem": "https://c.tenor.com/m__ZnOd5kF8AAAAd/tenor.gif",
        "vida": 30000,
        "tempo": 600,
        "dano_min": 80,
        "dano_max": 150,
        "recompensa_participou": 1,
        "recompensa_top": 4,
        "recompensa_final": 3,
        "moedas_participou": 240,
        "moedas_top": 1100,
        "moedas_final": 850,
        "dano_falha": 16,
        "agressividade": 1,
        "agressividade_max": 10,
        "chance_ataque": 25,
        "chance_habilidade": 35,
        "habilidade": "pacto_eterno",
        "dano_habilidade": 20,
        "drop_lendario": "Pacto Eterno",
        "frase": "Nem todo pacto pode ser quebrado.",
    },
    {
        "nome": "Rika",
        "categoria": "Jujutsu",
        "descricao": "Uma força esmagadora apareceu.",
        "imagem": "https://c.tenor.com/7z8vSgeTDq0AAAAd/tenor.gif",
        "vida": 20000,
        "tempo": 600,
        "dano_min": 65,
        "dano_max": 110,
        "recompensa_participou": 1,
        "recompensa_top": 3,
        "recompensa_final": 2,
        "moedas_participou": 200,
        "moedas_top": 900,
        "moedas_final": 700,
        "dano_falha": 8,
        "agressividade": 1,
        "agressividade_max": 6,
        "chance_ataque": 18,
        "chance_habilidade": 30,
        "habilidade": "grito",
        "dano_habilidade": 16,
        "drop_lendario": "Olhar da Rainha das Maldições",
        "frase": "O amor também pode ser uma maldição.",
    },

    # =========================
    # CUPHEAD / CASSINO DO DIABO
    # =========================
    {
        "nome": "O Diabo",
        "categoria": "Cuphead",
        "descricao": "O dono do cassino saiu das sombras para cobrar suas dívidas.",
        "imagem": "https://c.tenor.com/dJ_AasjA5-sAAAAC/tenor.gif",
        "vida": 30000,
        "tempo": 600,
        "dano_min": 80,
        "dano_max": 150,
        "recompensa_participou": 2,
        "recompensa_top": 6,
        "recompensa_final": 4,
        "moedas_participou": 350,
        "moedas_top": 1800,
        "moedas_final": 1500,
        "dano_falha": 18,
        "agressividade": 1,
        "agressividade_max": 10,
        "chance_ataque": 32,
        "chance_habilidade": 35,
        "habilidade": "cobranca_da_casa",
        "dano_habilidade": 22,
        "drop_lendario": "Contrato do Diabo",
        "frase": "A casa sempre vence. Mas hoje ela quer espetáculo.",
    },
    {
        "nome": "King Dice",
        "categoria": "Cuphead",
        "descricao": "O mestre dos dados abriu a mesa final.",
        "imagem": "https://c.tenor.com/ADa6Z69I9PUAAAAC/tenor.gif",
        "vida": 12000,
        "tempo": 600,
        "dano_min": 56,
        "dano_max": 87,
        "recompensa_participou": 2,
        "recompensa_top": 5,
        "recompensa_final": 4,
        "moedas_participou": 300,
        "moedas_top": 1500,
        "moedas_final": 1200,
        "dano_falha": 15,
        "agressividade": 1,
        "agressividade_max": 9,
        "chance_ataque": 28,
        "chance_habilidade": 40,
        "habilidade": "dados_viciados",
        "dano_habilidade": 18,
        "drop_lendario": "Dado Viciado",
        "frase": "Role os dados. O resultado já estava decidido.",
    },
    {
        "nome": "Cagney Carnation",
        "categoria": "Cuphead",
        "descricao": "Uma flor mortal floresceu no centro do cassino.",
        "imagem": "https://media1.tenor.com/m/DUXafcfQ664AAAAC/death-flower.gif",
        "vida": 6000,
        "tempo": 600,
        "dano_min": 20,
        "dano_max": 70,
        "recompensa_participou": 1,
        "recompensa_top": 4,
        "recompensa_final": 3,
        "moedas_participou": 220,
        "moedas_top": 1000,
        "moedas_final": 800,
        "dano_falha": 12,
        "agressividade": 1,
        "agressividade_max": 7,
        "chance_ataque": 25,
        "chance_habilidade": 38,
        "habilidade": "espinhos",
        "dano_habilidade": 16,
        "drop_lendario": "Semente Infernal",
        "frase": "Nem toda flor nasce para enfeitar.",
    },
    {
        "nome": "Baroness Von Bon Bon",
        "categoria": "Cuphead",
        "descricao": "A doce rainha da loucura tomou conta da arena.",
        "imagem": "https://c.tenor.com/LvH_8WtffvgAAAAC/tenor.gif",
        "vida": 26000,
        "tempo": 600,
        "dano_min": 80,
        "dano_max": 150,
        "recompensa_participou": 1,
        "recompensa_top": 4,
        "recompensa_final": 3,
        "moedas_participou": 240,
        "moedas_top": 1100,
        "moedas_final": 850,
        "dano_falha": 13,
        "agressividade": 1,
        "agressividade_max": 8,
        "chance_ataque": 26,
        "chance_habilidade": 35,
        "habilidade": "doces_explosivos",
        "dano_habilidade": 17,
        "drop_lendario": "Coroa Açucarada",
        "frase": "A doçura acabou. Agora só resta o veneno.",
    },
    {
    
    },
]


# =========================
# FUNÇÕES AUXILIARES
# =========================
def buscar_boss(nome: str):
    if not nome:
        return None

    nome = nome.lower().strip()

    for boss in BOSSES:
        if not boss.get("nome"):
            continue
        if boss["nome"].lower() == nome:
            return boss

    for boss in BOSSES:
        if not boss.get("nome"):
            continue
        if nome in boss["nome"].lower():
            return boss

    return None


def normalizar_linha_jogador(jogador):
    """
    Compatibilidade entre tupla/lista e RealDictCursor.
    Esperado no código antigo:
    jogador[0] = user_id
    jogador[2] = vidas
    jogador[5] = status
    """
    if isinstance(jogador, dict):
        return {
            "user_id": jogador.get("user_id"),
            "vidas": jogador.get("vidas"),
            "status": jogador.get("status"),
        }

    return {
        "user_id": jogador[0],
        "vidas": jogador[2] if len(jogador) > 2 else None,
        "status": jogador[5] if len(jogador) > 5 else None,
    }


async def enviar_log(guild: discord.Guild, embed: discord.Embed):
    if not guild:
        return

    canal = guild.get_channel(CANAL_LOG_MALDICOES_ID)

    if canal:
        await canal.send(embed=embed)


def resetar_vidas_todos():
    # Não apaga família, ranking, abates ou contratos.
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE jogadores
        SET vidas = %s, status = 'vivo', alvo_id = NULL
        """,
        (VIDAS_MAXIMAS,)
    )

    conn.commit()
    conn.close()


def sortear_drop(boss_nome: str, boss_drop_lendario: str):
    chance = random.randint(1, 100)

    if chance <= 5:
        return {
            "raridade": "LENDÁRIO",
            "emoji": "🌟",
            "nome": boss_drop_lendario,
            "bonus_abate": 8,
            "bonus_moedas": 1200,
        }

    if chance <= 18:
        return {
            "raridade": "ÉPICO",
            "emoji": "🟣",
            "nome": f"Relíquia de {boss_nome}",
            "bonus_abate": 5,
            "bonus_moedas": 750,
        }

    if chance <= 45:
        return {
            "raridade": "RARO",
            "emoji": "🔵",
            "nome": f"Marca de {boss_nome}",
            "bonus_abate": 3,
            "bonus_moedas": 400,
        }

    return {
        "raridade": "COMUM",
        "emoji": "⚪",
        "nome": "Fragmento Amaldiçoado",
        "bonus_abate": 1,
        "bonus_moedas": 150,
    }


def recompensar_moedas(user_id: int, quantidade: int):
    if adicionar_moedas is None:
        return

    if quantidade <= 0:
        return

    try:
        adicionar_moedas(user_id, quantidade)
    except Exception as e:
        print(f"[BOSS] Erro ao adicionar moedas para {user_id}: {e}")


# =========================
# VIEW DO BOSS
# =========================
class BossView(discord.ui.View):
    def __init__(self, boss, estado_salvo=None):
        super().__init__(timeout=boss["tempo"])

        self.boss = boss.copy()
        self.vida = self.boss["vida"]
        self.max_vida = self.boss["vida"]
        self.danos = {}
        self.ultimo_ataque = {}
        self.defendendo = set()
        self.finalizado = False
        self.mensagem = None
        self.ultimo_hit = None
        self.agressividade = self.boss.get("agressividade", 1)
        self.agressividade_max = self.boss.get("agressividade_max", 5)
        self.turnos = 0
        self.fases_anunciadas = set()

        if estado_salvo:
            self.vida = estado_salvo.get("vida", self.vida)
            self.max_vida = estado_salvo.get("max_vida", self.max_vida)
            self.danos = estado_salvo.get("danos", {})
            self.ultimo_hit = estado_salvo.get("ultimo_hit")
            self.agressividade = estado_salvo.get("agressividade", self.agressividade)
            self.turnos = estado_salvo.get("turnos", self.turnos)

    def barra(self):
        if self.max_vida <= 0:
            return "⬛" * 10

        pct = max(0, self.vida) / self.max_vida
        cheio = max(0, min(10, round(pct * 10)))

        if pct <= 0:
            return "⬛" * 10

        if pct <= 0.10:
            cheio = max(1, cheio)
            return "🔥" * cheio + "⬛" * (10 - cheio)

        if pct <= 0.30:
            cheio = max(1, cheio)
            return "🟧" * cheio + "⬛" * (10 - cheio)

        if pct <= 0.60:
            cheio = max(1, cheio)
            return "🟨" * cheio + "⬛" * (10 - cheio)

        return "🟥" * cheio + "⬛" * (10 - cheio)

    def estado_boss(self):
        pct = max(0, self.vida) / self.max_vida

        if pct <= 0.10:
            return "🌑 **FASE FINAL — Despertar absoluto. O boss está no limite.**"

        if pct <= 0.25:
            return "🩸 **FASE 3 — Domínio instável. Os ataques estão muito mais perigosos.**"

        if pct <= 0.50:
            return "🔥 **FASE 2 — Agressividade elevada. O boss começou a pressionar.**"

        if pct <= 0.75:
            return "🟧 **FASE 1 — Energia subindo. A batalha ficou séria.**"

        return "🟥 **INÍCIO — O boss ainda está firme.**"

    def cor_embed(self):
        if self.boss.get("categoria") == "Cuphead":
            return COR_CASSINO
        return COR_VERMELHA

    def embed(self):
        ranking = sorted(self.danos.items(), key=lambda x: x[1], reverse=True)[:5]

        texto = ""

        for i, (uid, dmg) in enumerate(ranking, start=1):
            medalha = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"`#{i}`"
            texto += f"{medalha} <@{uid}> — 💥 **{dmg:,}** dano\n"

        if not texto:
            texto = "Ninguém atacou ainda."

        porcentagem = int((max(0, self.vida) / self.max_vida) * 100)

        embed = discord.Embed(
            title=f"💀 BOSS — {self.boss['nome']}",
            description=(
                f"**Categoria:** `{self.boss.get('categoria', 'Especial')}`\n"
                f"{self.boss['descricao']}\n\n"
                f"> *{self.boss.get('frase', 'A batalha começou.')}*\n\n"
                f"❤️ **Vida:** `{max(0, self.vida):,}/{self.max_vida:,}` `({porcentagem}%)`\n"
                f"{self.barra()}\n\n"
                f"{self.estado_boss()}\n"
                f"🔥 **Agressividade:** `{self.agressividade}/{self.agressividade_max}`\n"
                f"⏳ **Tempo limite:** `{self.boss['tempo'] // 60} minutos`\n"
                f"⚔️ **Cooldown de ataque:** `{COOLDOWN_ATAQUE}s`"
            ),
            color=self.cor_embed()
        )

        embed.add_field(name="🏆 Ranking de Dano", value=texto, inline=False)
        embed.set_image(url=self.boss["imagem"])
        embed.set_footer(text="Família Sant's • Raid Boss • Progresso salvo automaticamente")

        return embed

    async def verificar_fase(self, canal):
        pct = max(0, self.vida) / self.max_vida

        fases = [
            (0.75, "fase_75", "🟧 **FASE 1 DESPERTADA**", "A energia do boss começou a distorcer a arena."),
            (0.50, "fase_50", "🔥 **FASE 2 ATIVADA**", "A pressão aumentou. O boss está muito mais agressivo."),
            (0.25, "fase_25", "🩸 **FASE 3 — DOMÍNIO INSTÁVEL**", "O domínio começa a esmagar os jogadores. Cuidado com os contra-ataques."),
            (0.10, "fase_10", "🌑 **FASE FINAL — DESESPERO ABSOLUTO**", "O boss está no limite. Os próximos golpes decidirão a raid."),
        ]

        for limite, chave, titulo, descricao in fases:
            if pct <= limite and chave not in self.fases_anunciadas:
                self.fases_anunciadas.add(chave)
                self.agressividade = min(self.agressividade + 1, self.agressividade_max)

                embed = discord.Embed(
                    title=titulo,
                    description=(
                        f"💀 **Boss:** {self.boss['nome']}\n"
                        f"{descricao}\n\n"
                        f"🔥 Agressividade atual: **{self.agressividade}/{self.agressividade_max}**"
                    ),
                    color=self.cor_embed()
                )
                embed.set_image(url=self.boss["imagem"])
                embed.set_footer(text="Família Sant's • Mudança de Fase")
                try:
                    await canal.send(embed=embed, delete_after=20)
                except Exception:
                    pass

                salvar_boss_ativo(self)
                break

    async def enviar_ataque_temporario(self, canal, texto: str):
        try:
            await canal.send(texto, delete_after=TEMPO_APAGAR_ATAQUE)
        except Exception:
            pass

    async def causar_dano_em_jogador(self, user_id: int, dano: int):
        dano_final, usou_escudo = aplicar_defesa_boss(user_id, dano)

        if user_id in self.defendendo:
            dano_final = max(0, dano_final // 2)
            self.defendendo.discard(user_id)

        if dano_final <= 0:
            jogador = buscar_jogador(user_id)
            return normalizar_linha_jogador(jogador) if jogador else None

        resultado = remover_vida(user_id, dano_final)

        if not resultado:
            return None

        dados = normalizar_linha_jogador(resultado)
        dados["dano_recebido"] = dano_final
        dados["escudo_usado"] = usou_escudo

        return dados

    async def usar_habilidade(self, interaction: discord.Interaction):
        habilidade = self.boss.get("habilidade")
        dano_base = self.boss.get("dano_habilidade", 0)

        if not habilidade or dano_base <= 0:
            return

        if random.randint(1, 100) > self.boss.get("chance_habilidade", 25):
            return

        jogadores = listar_jogadores_vivos()

        if not jogadores:
            return

        dano = max(1, int((dano_base * 0.6) + self.agressividade))

        # =========================
        # HABILIDADES JUJUTSU
        # =========================
        if habilidade == "corte_area":
            alvos = random.sample(jogadores, min(3, len(jogadores)))
            texto = f"🔥 **{self.boss['nome']} usou CORTE EM ÁREA!**\n"

            for jogador in alvos:
                user_id = normalizar_linha_jogador(jogador)["user_id"]
                resultado = await self.causar_dano_em_jogador(user_id, dano)

                if resultado:
                    texto += f"🩸 <@{user_id}> recebeu **-{dano}** dano. ❤️ `{resultado['vidas']}/{VIDAS_MAXIMAS}`"

                    if resultado["status"] == "eliminado":
                        texto += " ☠️ **ELIMINADO**"

                    texto += "\n"

            await self.enviar_ataque_temporario(interaction.channel, texto)

        elif habilidade == "adaptacao":
            self.agressividade = min(self.agressividade + 1, self.agressividade_max)
            self.boss["dano_min"] += 1
            self.boss["dano_max"] += 1

            await self.enviar_ataque_temporario(
                interaction.channel,
                f"⚙️ **{self.boss['nome']} se adaptou ao dano recebido!**\n"
                f"🔥 Agressividade atual: **{self.agressividade}/{self.agressividade_max}**"
            )

        elif habilidade == "grito":
            resultado = await self.causar_dano_em_jogador(interaction.user.id, dano)

            if resultado:
                texto = (
                    f"👁️ **{self.boss['nome']} soltou um GRITO AMALDIÇOADO!**\n"
                    f"🎯 Alvo: {interaction.user.mention}\n"
                    f"🩸 Dano: **-{dano}**\n"
                    f"❤️ Vida restante: **{resultado['vidas']}/{VIDAS_MAXIMAS}**"
                )

                if resultado["status"] == "eliminado":
                    texto += "\n☠️ **ELIMINADO**"

                await self.enviar_ataque_temporario(interaction.channel, texto)

        elif habilidade == "pacto_eterno":
            alvos = random.sample(jogadores, min(2, len(jogadores)))
            cura = min(5000, self.max_vida - self.vida)
            self.vida += cura

            texto = f"💜 **{self.boss['nome']} ativou PACTO ETERNO!**\n❤️ O boss recuperou **{cura:,}** de vida.\n"

            for jogador in alvos:
                user_id = normalizar_linha_jogador(jogador)["user_id"]
                resultado = await self.causar_dano_em_jogador(user_id, dano)

                if resultado:
                    texto += f"🩸 <@{user_id}> recebeu **-{dano}** dano. ❤️ `{resultado['vidas']}/{VIDAS_MAXIMAS}`"

                    if resultado["status"] == "eliminado":
                        texto += " ☠️ **ELIMINADO**"

                    texto += "\n"

            await self.enviar_ataque_temporario(interaction.channel, texto)

        # =========================
        # HABILIDADES CUPHEAD
        # =========================
        elif habilidade == "cobranca_da_casa":
            alvos = random.sample(jogadores, min(4, len(jogadores)))
            cura = min(3000, self.max_vida - self.vida)
            self.vida += cura

            texto = (
                f"🎰 **{self.boss['nome']} ativou COBRANÇA DA CASA!**\n"
                f"❤️ O boss recuperou **{cura:,}** de vida.\n"
            )

            for jogador in alvos:
                user_id = normalizar_linha_jogador(jogador)["user_id"]
                resultado = await self.causar_dano_em_jogador(user_id, dano)

                if resultado:
                    texto += f"🪙 <@{user_id}> pagou a dívida com **-{dano}** de vida. ❤️ `{resultado['vidas']}/{VIDAS_MAXIMAS}`"

                    if resultado["status"] == "eliminado":
                        texto += " ☠️ **ELIMINADO**"

                    texto += "\n"

            await self.enviar_ataque_temporario(interaction.channel, texto)

        elif habilidade == "dados_viciados":
            rolagem = random.randint(1, 6)
            dano_dados = dano + (rolagem * 2)

            resultado = await self.causar_dano_em_jogador(interaction.user.id, dano_dados)

            if resultado:
                texto = (
                    f"🎲 **{self.boss['nome']} rolou dados viciados!**\n"
                    f"🎯 Resultado: **{rolagem}**\n"
                    f"🎯 Alvo: {interaction.user.mention}\n"
                    f"🩸 Dano: **-{dano_dados}**\n"
                    f"❤️ Vida restante: **{resultado['vidas']}/{VIDAS_MAXIMAS}**"
                )

                if resultado["status"] == "eliminado":
                    texto += "\n☠️ **ELIMINADO**"

                await self.enviar_ataque_temporario(interaction.channel, texto)

        elif habilidade == "espinhos":
            alvos = random.sample(jogadores, min(3, len(jogadores)))
            texto = f"🌺 **{self.boss['nome']} espalhou espinhos pelo cassino!**\n"

            for jogador in alvos:
                user_id = normalizar_linha_jogador(jogador)["user_id"]
                resultado = await self.causar_dano_em_jogador(user_id, dano)

                if resultado:
                    texto += f"🌹 <@{user_id}> foi perfurado por espinhos. **-{dano}** vida. ❤️ `{resultado['vidas']}/{VIDAS_MAXIMAS}`"

                    if resultado["status"] == "eliminado":
                        texto += " ☠️ **ELIMINADO**"

                    texto += "\n"

            await self.enviar_ataque_temporario(interaction.channel, texto)

        elif habilidade == "doces_explosivos":
            alvos = random.sample(jogadores, min(2, len(jogadores)))
            texto = f"🍬 **{self.boss['nome']} lançou doces explosivos!**\n"

            for jogador in alvos:
                user_id = normalizar_linha_jogador(jogador)["user_id"]
                resultado = await self.causar_dano_em_jogador(user_id, dano + 4)

                if resultado:
                    texto += f"💥 <@{user_id}> recebeu **-{dano + 4}** dano. ❤️ `{resultado['vidas']}/{VIDAS_MAXIMAS}`"

                    if resultado["status"] == "eliminado":
                        texto += " ☠️ **ELIMINADO**"

                    texto += "\n"

            await self.enviar_ataque_temporario(interaction.channel, texto)

        elif habilidade == "chamas":
            self.agressividade = min(self.agressividade + 1, self.agressividade_max)
            alvos = random.sample(jogadores, min(3, len(jogadores)))

            texto = (
                f"🔥 **{self.boss['nome']} incendiou a arena!**\n"
                f"🔥 Agressividade atual: **{self.agressividade}/{self.agressividade_max}**\n"
            )

            for jogador in alvos:
                user_id = normalizar_linha_jogador(jogador)["user_id"]
                resultado = await self.causar_dano_em_jogador(user_id, dano)

                if resultado:
                    texto += f"🔥 <@{user_id}> sofreu **-{dano}** dano. ❤️ `{resultado['vidas']}/{VIDAS_MAXIMAS}`"

                    if resultado["status"] == "eliminado":
                        texto += " ☠️ **ELIMINADO**"

                    texto += "\n"

            await self.enviar_ataque_temporario(interaction.channel, texto)

    async def finalizar(self, channel: discord.TextChannel, guild: discord.Guild):
        global BOSS_ATIVO

        if self.finalizado is False:
            self.finalizado = True

        BOSS_ATIVO = None
        limpar_boss_ativo()

        if not self.danos:
            return

        top = max(self.danos, key=self.danos.get)

        # Recompensas fixas de abate
        for uid in self.danos:
            if buscar_jogador(uid):
                adicionar_abate(uid, self.boss["recompensa_participou"])

            recompensar_moedas(uid, self.boss.get("moedas_participou", 0))

        if buscar_jogador(top):
            adicionar_abate(top, self.boss["recompensa_top"])

        recompensar_moedas(top, self.boss.get("moedas_top", 0))

        if self.ultimo_hit and buscar_jogador(self.ultimo_hit):
            adicionar_abate(self.ultimo_hit, self.boss["recompensa_final"])

        if self.ultimo_hit:
            recompensar_moedas(self.ultimo_hit, self.boss.get("moedas_final", 0))

        # Drops
        drop_top = sortear_drop(
            self.boss["nome"],
            self.boss.get("drop_lendario", "Artefato Lendário")
        )

        drop_final = sortear_drop(
            self.boss["nome"],
            self.boss.get("drop_lendario", "Artefato Lendário")
        )

        if buscar_jogador(top):
            adicionar_abate(top, drop_top["bonus_abate"])
            adicionar_item(top, drop_top["nome"], 1)

        recompensar_moedas(top, drop_top["bonus_moedas"])

        if self.ultimo_hit and buscar_jogador(self.ultimo_hit):
            adicionar_abate(self.ultimo_hit, drop_final["bonus_abate"])
            adicionar_item(self.ultimo_hit, drop_final["nome"], 1)

        if self.ultimo_hit:
            recompensar_moedas(self.ultimo_hit, drop_final["bonus_moedas"])

        ranking = sorted(self.danos.items(), key=lambda x: x[1], reverse=True)[:5]

        texto_ranking = ""

        for i, (uid, dmg) in enumerate(ranking, start=1):
            medalha = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"`#{i}`"
            texto_ranking += f"{medalha} <@{uid}> — 💥 **{dmg:,}** dano\n"

        embed = discord.Embed(
            title="🏆 BOSS DERROTADO",
            description=(
                f"💀 **Boss:** {self.boss['nome']}\n"
                f"🎭 **Categoria:** `{self.boss.get('categoria', 'Especial')}`\n"
                f"🥇 **Maior dano:** <@{top}>\n"
                f"⚔️ **Golpe final:** <@{self.ultimo_hit}>\n\n"
                f"🎁 **Recompensas fixas:**\n"
                f"• Participou: +{self.boss['recompensa_participou']} abate(s) "
                f"e +{self.boss.get('moedas_participou', 0):,} 🪙\n"
                f"• Top dano: +{self.boss['recompensa_top']} abate(s) "
                f"e +{self.boss.get('moedas_top', 0):,} 🪙\n"
                f"• Golpe final: +{self.boss['recompensa_final']} abate(s) "
                f"e +{self.boss.get('moedas_final', 0):,} 🪙"
            ),
            color=COR_VERDE
        )

        embed.add_field(name="📊 Ranking Final", value=texto_ranking, inline=False)

        embed.add_field(
            name="🎁 Drop do Maior Dano",
            value=(
                f"{drop_top['emoji']} **{drop_top['raridade']}**\n"
                f"Item: **{drop_top['nome']}**\n"
                f"Bônus: +{drop_top['bonus_abate']} abate(s)\n"
                f"Moedas: +{drop_top['bonus_moedas']:,} 🪙\n"
                f"Recebedor: <@{top}>"
            ),
            inline=False
        )

        embed.add_field(
            name="⚔️ Drop do Golpe Final",
            value=(
                f"{drop_final['emoji']} **{drop_final['raridade']}**\n"
                f"Item: **{drop_final['nome']}**\n"
                f"Bônus: +{drop_final['bonus_abate']} abate(s)\n"
                f"Moedas: +{drop_final['bonus_moedas']:,} 🪙\n"
                f"Recebedor: <@{self.ultimo_hit}>"
            ),
            inline=False
        )

        embed.set_image(url=self.boss["imagem"])
        embed.set_footer(text="Família Sant's • Raid Boss Finalizado")

        await channel.send(embed=embed)
        await enviar_log(guild, embed)

    async def on_timeout(self):
        global BOSS_ATIVO

        if self.finalizado:
            return

        self.finalizado = True
        BOSS_ATIVO = None
        limpar_boss_ativo()

        for item in self.children:
            item.disabled = True

        if self.mensagem:
            try:
                await self.mensagem.edit(embed=self.embed(), view=self)
            except Exception:
                pass

        jogadores = listar_jogadores_vivos()

        if not jogadores:
            return

        atingidos = random.sample(jogadores, min(3, len(jogadores)))
        dano_final = max(1, int((self.boss["dano_falha"] * 0.7) + self.agressividade))
        texto_atingidos = ""

        for jogador in atingidos:
            user_id = normalizar_linha_jogador(jogador)["user_id"]
            resultado = await self.causar_dano_em_jogador(user_id, dano_final)

            if resultado:
                texto_atingidos += f"💀 <@{user_id}> perdeu **{dano_final}** vida(s). ❤️ `{resultado['vidas']}/{VIDAS_MAXIMAS}`"

                if resultado["status"] == "eliminado":
                    texto_atingidos += " ☠️ **ELIMINADO**"

                texto_atingidos += "\n"

        embed = discord.Embed(
            title="☠️ O BOSS VENCEU",
            description=(
                f"💀 **{self.boss['nome']}** não foi derrotado a tempo.\n\n"
                f"{texto_atingidos}"
            ),
            color=COR_VERMELHA
        )

        embed.set_image(url=self.boss["imagem"])
        embed.set_footer(text="Família Sant's • Raid Boss")

        if self.mensagem:
            await self.mensagem.channel.send(embed=embed)
            await enviar_log(self.mensagem.guild, embed)

    @discord.ui.button(
        label="Atacar",
        emoji="⚔️",
        style=discord.ButtonStyle.danger,
        custom_id="boss_atacar"
    )
    async def atacar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finalizado:
            await interaction.response.send_message("💀 Esse boss já foi finalizado.", ephemeral=True)
            return

        jogador = buscar_jogador(interaction.user.id)

        if not jogador:
            await interaction.response.send_message(
                "🚫 Você precisa entrar no **Jogo do Abate** antes de atacar bosses.",
                ephemeral=True
            )
            return

        dados_jogador = normalizar_linha_jogador(jogador)

        if dados_jogador["status"] != "vivo":
            await interaction.response.send_message(
                "💀 Você está eliminado e não pode atacar bosses.",
                ephemeral=True
            )
            return

        agora = time.time()
        ultimo = self.ultimo_ataque.get(interaction.user.id, 0)
        restante = COOLDOWN_ATAQUE - (agora - ultimo)

        if restante > 0:
            await interaction.response.send_message(
                f"⏳ Aguarde **{int(restante)}s** para atacar novamente.",
                ephemeral=True
            )
            return

        self.ultimo_ataque[interaction.user.id] = agora

        self.turnos += 1

        if self.turnos % 8 == 0 and self.agressividade < self.agressividade_max:
            self.agressividade += 1

        dano_base = random.randint(self.boss["dano_min"], self.boss["dano_max"])
        dano, efeitos = calcular_dano_com_buffs(interaction.user.id, dano_base)

        self.vida -= dano
        self.danos[interaction.user.id] = self.danos.get(interaction.user.id, 0) + dano
        self.ultimo_hit = interaction.user.id

        await self.verificar_fase(interaction.channel)
        salvar_boss_ativo(self)

        # Atualiza primeiro o painel principal
        await interaction.response.edit_message(embed=self.embed(), view=self)

        if efeitos:
            await self.enviar_ataque_temporario(
                interaction.channel,
                f"✨ {interaction.user.mention} ativou efeitos da loja:\n" + "\n".join([f"• {e}" for e in efeitos]) + f"\n💥 Dano causado: **{dano:,}**"
            )

        # Contra-ataque básico
        if random.randint(1, 100) <= self.boss.get("chance_ataque", 20):
            dano_boss = random.randint(
                max(1, int(self.boss["dano_falha"] * 0.4)),
                max(2, int(self.boss["dano_falha"] * 0.7))
            ) + self.agressividade

            resultado = await self.causar_dano_em_jogador(interaction.user.id, dano_boss)

            if resultado:
                texto = (
                    f"💢 **{self.boss['nome']} contra-atacou!**\n"
                    f"🎯 Alvo: {interaction.user.mention}\n"
                    f"🩸 Dano: **-{dano_boss}**\n"
                    f"❤️ Vida restante: **{resultado['vidas']}/{VIDAS_MAXIMAS}**"
                )

                if resultado["status"] == "eliminado":
                    texto += "\n☠️ **ELIMINADO**"

                await self.enviar_ataque_temporario(interaction.channel, texto)

        await self.usar_habilidade(interaction)
        salvar_boss_ativo(self)

        if self.vida <= 0:
            self.vida = 0
            self.finalizado = True

            for item in self.children:
                item.disabled = True

            try:
                await self.mensagem.edit(embed=self.embed(), view=self)
            except Exception:
                pass

            await self.finalizar(interaction.channel, interaction.guild)


    @discord.ui.button(
        label="Técnica",
        emoji="✨",
        style=discord.ButtonStyle.primary,
        custom_id="boss_tecnica"
    )
    async def tecnica(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finalizado:
            await interaction.response.send_message("💀 Esse boss já foi finalizado.", ephemeral=True)
            return

        jogador = buscar_jogador(interaction.user.id)
        if not jogador or normalizar_linha_jogador(jogador)["status"] != "vivo":
            await interaction.response.send_message("🚫 Você precisa estar vivo no **Jogo do Abate**.", ephemeral=True)
            return

        # A técnica usa buffs de loja sem depender do ataque comum.
        dano_base = random.randint(
            max(1, int(self.boss["dano_min"] * 0.7)),
            max(2, int(self.boss["dano_max"] * 0.9))
        )
        dano, efeitos = calcular_dano_com_buffs(interaction.user.id, dano_base)

        if not efeitos:
            await interaction.response.send_message(
                "✨ Você tentou usar uma técnica, mas não possui `furia`, `critico` ou `berserk` ativo.\n"
                "Compre itens no Mercado Amaldiçoado ou no Mercado dos Feiticeiros.",
                ephemeral=True
            )
            return

        self.vida -= dano
        self.danos[interaction.user.id] = self.danos.get(interaction.user.id, 0) + dano
        self.ultimo_hit = interaction.user.id

        await self.verificar_fase(interaction.channel)
        salvar_boss_ativo(self)
        await interaction.response.edit_message(embed=self.embed(), view=self)

        await self.enviar_ataque_temporario(
            interaction.channel,
            f"✨ {interaction.user.mention} usou uma **Técnica Jujutsu**!\n"
            + "\n".join([f"• {e}" for e in efeitos])
            + f"\n💥 Dano causado: **{dano:,}**"
        )

        if self.vida <= 0:
            self.vida = 0
            self.finalizado = True
            for item in self.children:
                item.disabled = True
            try:
                await self.mensagem.edit(embed=self.embed(), view=self)
            except Exception:
                pass
            await self.finalizar(interaction.channel, interaction.guild)

    @discord.ui.button(
        label="Defender",
        emoji="🛡️",
        style=discord.ButtonStyle.success,
        custom_id="boss_defender"
    )
    async def defender(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogador = buscar_jogador(interaction.user.id)
        if not jogador or normalizar_linha_jogador(jogador)["status"] != "vivo":
            await interaction.response.send_message("🚫 Você precisa estar vivo para defender.", ephemeral=True)
            return

        self.defendendo.add(interaction.user.id)
        salvar_boss_ativo(self)
        await interaction.response.send_message(
            "🛡️ Defesa preparada! O próximo dano recebido nesta raid será reduzido.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Purificar",
        emoji="🧿",
        style=discord.ButtonStyle.secondary,
        custom_id="boss_purificar"
    )
    async def purificar(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogador = buscar_jogador(interaction.user.id)
        if not jogador:
            await interaction.response.send_message("🚫 Você precisa estar registrado no **Jogo do Abate**.", ephemeral=True)
            return

        saldo_sorte = quantidade_buff(interaction.user.id, "sorte")
        if saldo_sorte <= 0:
            await interaction.response.send_message(
                "🧿 Você precisa de pelo menos **1 buff de sorte** para canalizar uma purificação rápida na raid.",
                ephemeral=True
            )
            return

        consumir_buff(interaction.user.id, "sorte", 1)
        nova_corrupcao = reduzir_corrupcao(interaction.user.id, 8)

        await interaction.response.send_message(
            f"🧿 Purificação rápida concluída.\n🩸 Corrupção atual: **{nova_corrupcao}**",
            ephemeral=True
        )



# =========================
# COG
# =========================
class BossRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        criar_tabelas_raid()

    async def cog_load(self):
        # Recupera boss ativo após push/restart/redeploy.
        self.bot.loop.create_task(self.recuperar_boss_ativo())

    async def recuperar_boss_ativo(self):
        global BOSS_ATIVO

        await self.bot.wait_until_ready()

        if BOSS_ATIVO is not None:
            return

        estado = carregar_boss_ativo()
        if not estado:
            return

        canal = self.bot.get_channel(estado.get("canal_id"))
        if not canal:
            print("[RAID] Boss salvo encontrado, mas canal não foi localizado.")
            return

        view = BossView(estado["boss"], estado_salvo=estado)
        embed = view.embed()
        embed.title = f"♻️ RAID RECUPERADA — {estado['boss']['nome']}"
        embed.description += "\n\n♻️ **Esta raid foi recuperada automaticamente após reinício/push.**"

        try:
            msg = await canal.send(embed=embed, view=view)
            view.mensagem = msg
            BOSS_ATIVO = view
            salvar_boss_ativo(view)
            print("[RAID] Boss ativo recuperado com sucesso.")
        except Exception as e:
            print(f"[RAID] Erro ao recuperar boss ativo: {e}")

    @commands.command(name="boss")
    @commands.has_permissions(administrator=True)
    async def boss(self, ctx, *, nome=None):
        global BOSS_ATIVO

        try:
            await ctx.message.delete()
        except Exception:
            pass

        try:
            if BOSS_ATIVO is not None:
                await ctx.send(
                    "⚠️ Já existe um **boss ativo** no servidor.\n"
                    "Use `!limpar_boss` se precisar limpar manualmente.",
                    delete_after=12
                )
                return

            bosses_validos = [b for b in BOSSES if b.get("nome")]
            boss = buscar_boss(nome) if nome else random.choice(bosses_validos)

            if not boss:
                nomes = ", ".join([b["nome"] for b in bosses_validos])
                await ctx.send(
                    f"❌ Boss não encontrado.\nUse um destes:\n`{nomes}`",
                    delete_after=15
                )
                return

            view = BossView(boss)
            msg = await ctx.send(embed=view.embed(), view=view)
            view.mensagem = msg
            BOSS_ATIVO = view
            salvar_boss_ativo(view)

        except Exception as e:
            print(f"[ERRO AO INVOCAR BOSS] {repr(e)}")
            await ctx.send(
                f"⚠️ Erro ao invocar boss.\n```{repr(e)}```",
                delete_after=20
            )

    @commands.command(name="bosses")
    @commands.has_permissions(administrator=True)
    async def bosses(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        texto = ""

        for boss in BOSSES:
            if not boss.get("nome"):
                continue
            texto += f"• **{boss['nome']}** — `{boss.get('categoria', 'Especial')}`\n"

        embed = discord.Embed(
            title="📜 Bosses Disponíveis",
            description=texto,
            color=COR_DOURADA
        )

        embed.set_footer(text="Use: !boss nome_do_boss")
        await ctx.send(embed=embed, delete_after=30)

    @commands.command(name="limpar_boss")
    @commands.has_permissions(administrator=True)
    async def limpar_boss(self, ctx):
        global BOSS_ATIVO

        try:
            await ctx.message.delete()
        except Exception:
            pass

        if BOSS_ATIVO and BOSS_ATIVO.mensagem:
            try:
                for item in BOSS_ATIVO.children:
                    item.disabled = True
                await BOSS_ATIVO.mensagem.edit(view=BOSS_ATIVO)
            except Exception:
                pass

        BOSS_ATIVO = None
        limpar_boss_ativo()

        await ctx.send(
            "🧹 Boss ativo limpo manualmente. Agora outro boss pode ser invocado.",
            delete_after=10
        )

    @commands.command(name="resetar_vida", aliases=["vidas"])
    @commands.has_permissions(administrator=True)
    async def resetar_vida(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        resetar_vidas_todos()

        await ctx.send(
            f"❤️ **Vidas restauradas!**\n"
            f"Todos os jogadores voltaram para **{VIDAS_MAXIMAS}/{VIDAS_MAXIMAS}** e status **vivo**.\n"
            f"Famílias, ranking e dados continuam salvos.",
            delete_after=12
        )

    @commands.command(name="resetar_tudo", aliases=["reset_tudo"])
    @commands.has_permissions(administrator=True)
    async def resetar_tudo(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        resetar_jogo()
        limpar_boss_ativo()

        await ctx.send(
            "🩸 **Jogo do Abate resetado completamente.**\n"
            "Todos os registros foram apagados.",
            delete_after=12
        )

    @boss.error
    async def boss_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ Apenas administradores podem invocar bosses.", delete_after=8)
        else:
            await ctx.reply("⚠️ Ocorreu um erro ao invocar o boss.", delete_after=8)
            print(f"[ERRO BOSS] {error}")

    @bosses.error
    async def bosses_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ Apenas administradores podem ver a lista de bosses.", delete_after=8)
        else:
            await ctx.reply("⚠️ Ocorreu um erro ao listar bosses.", delete_after=8)
            print(f"[ERRO BOSSES] {error}")

    @limpar_boss.error
    async def limpar_boss_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ Apenas administradores podem limpar boss ativo.", delete_after=8)
        else:
            await ctx.reply("⚠️ Ocorreu um erro ao limpar o boss ativo.", delete_after=8)
            print(f"[ERRO LIMPAR BOSS] {error}")

    @resetar_vida.error
    async def resetar_vida_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ Apenas administradores podem resetar as vidas.", delete_after=8)
        else:
            await ctx.reply("⚠️ Ocorreu um erro ao resetar vidas.", delete_after=8)
            print(f"[ERRO RESETAR VIDA] {error}")

    @resetar_tudo.error
    async def resetar_tudo_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ Apenas administradores podem resetar o jogo.", delete_after=8)
        else:
            await ctx.reply("⚠️ Ocorreu um erro ao resetar tudo.", delete_after=8)
            print(f"[ERRO RESETAR TUDO] {error}")


async def setup(bot):
    # Remove comandos antigos para evitar conflito
    for comando in ["boss", "bosses", "limpar_boss", "resetar_vida", "vidas", "resetar_tudo", "reset_tudo"]:
        if bot.get_command(comando):
            bot.remove_command(comando)

    # Remove cogs antigas se existirem
    if bot.get_cog("Boss"):
        bot.remove_cog("Boss")

    if bot.get_cog("BossRaid"):
        bot.remove_cog("BossRaid")

    if bot.get_cog("Maldicoes"):
        bot.remove_cog("Maldicoes")

    await bot.add_cog(Maldicoes(bot))
    await bot.add_cog(BossRaid(bot))
