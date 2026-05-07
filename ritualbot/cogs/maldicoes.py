import random
import asyncio
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


async def setup(bot):
    await bot.add_cog(Maldicoes(bot))
