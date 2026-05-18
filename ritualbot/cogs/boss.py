import random
import time
import discord
from discord.ext import commands

from utils.db import (
    buscar_jogador,
    adicionar_abate,
    remover_vida,
    listar_jogadores_vivos,
    conectar,
    resetar_jogo,
)

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
        "dano_min": 30,
        "dano_max": 60,
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
        "dano_max": 26,
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
    def __init__(self, boss):
        super().__init__(timeout=boss["tempo"])

        self.boss = boss.copy()
        self.vida = self.boss["vida"]
        self.max_vida = self.boss["vida"]
        self.danos = {}
        self.ultimo_ataque = {}
        self.finalizado = False
        self.mensagem = None
        self.ultimo_hit = None
        self.agressividade = self.boss.get("agressividade", 1)
        self.agressividade_max = self.boss.get("agressividade_max", 5)
        self.turnos = 0

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
            return "🔥 **CRÍTICO — O boss está desesperado.**"

        if pct <= 0.30:
            return "🟧 **Fúria elevada — ataques mais perigosos.**"

        if pct <= 0.60:
            return "🟨 **Instável — a pressão está aumentando.**"

        return "🟥 **Controle inicial — o boss ainda está firme.**"

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
        embed.set_footer(text="Família Sant's • Raid Boss • A casa sempre observa")

        return embed

    async def enviar_ataque_temporario(self, canal, texto: str):
        try:
            await canal.send(texto, delete_after=TEMPO_APAGAR_ATAQUE)
        except Exception:
            pass

    async def causar_dano_em_jogador(self, user_id: int, dano: int):
        resultado = remover_vida(user_id, dano)

        if not resultado:
            return None

        dados = normalizar_linha_jogador(resultado)

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

        recompensar_moedas(top, drop_top["bonus_moedas"])

        if self.ultimo_hit and buscar_jogador(self.ultimo_hit):
            adicionar_abate(self.ultimo_hit, drop_final["bonus_abate"])

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

        dano = random.randint(self.boss["dano_min"], self.boss["dano_max"])
        self.vida -= dano
        self.danos[interaction.user.id] = self.danos.get(interaction.user.id, 0) + dano
        self.ultimo_hit = interaction.user.id

        # Atualiza primeiro o painel principal
        await interaction.response.edit_message(embed=self.embed(), view=self)

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


# =========================
# COG
# =========================
class BossRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
    # Evita conflito caso alguma versão antiga da cog ainda esteja carregada.
    if bot.get_cog("Boss"):
        bot.remove_cog("Boss")

    if bot.get_cog("BossRaid"):
        bot.remove_cog("BossRaid")

    await bot.add_cog(BossRaid(bot))
