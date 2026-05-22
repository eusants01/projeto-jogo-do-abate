import random
import asyncio
import discord
from discord.ext import commands
from datetime import datetime, timezone

from utils.cassino_db import adicionar_moedas, get_moedas, remover_moedas

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                   CONFIGURAÇÕES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CHANCE_BASE        = 10000   # 1 em X mensagens dispara pacto
CHANCE_PACTO       = 1
TIMEOUT_PACTO      = 300     # segundos para responder
CUSTO_SEGURO       = 5000    # moedas para proteger cargo
DURACAO_SEGURO     = 3600    # 1 hora
COOLDOWN_HORAS     = 3600    # 1 hora entre pactos automáticos

ID_CANAL_LOG       = 1507228052776681502       # 🔧 ID do canal de log
ID_CANAL_PUBLICO   = 0       # 🔧 ID do canal de anúncios

IMAGEM_PADRAO      = "https://i.imgur.com/MX7rQpp.png"

CARGOS_PROTEGIDOS = [
    1483191687927828766, 1480349452744265759, 1501356975491907664,
    1500545846427652166, 1480381506064093225, 1487560221202321600,
    1505698473125609636, 1505698594651373719, 1505698708711538829,
    1505701356743295048, 1505701448900411413, 1487272681685647510,
    1494113762947371202, 1494114100907741214, 1493475034503577611,
    1494134900360744961, 1487891283102924961,
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                CATÁLOGO DE PACTOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PACTOS = {
    "comum": [
        {
            "nome": "📜 Pacto da Sombra",
            "tipo": "normal",
            "recompensa_min": 1000,  "recompensa_max": 5000,
            "descricao": "Uma oferta modesta do além. O preço é baixo, mas a alma tem valor.",
            "consequencia": "Pode perder um cargo menor.",
            "perde_cargo": True,
            "rejeitar_custo": 200,
            "cor": 0x808080,
            "encadeia": False,
        },
    ],
    "raro": [
        {
            "nome": "☠️ Pacto do Sacrifício",
            "tipo": "normal",
            "recompensa_min": 10000, "recompensa_max": 30000,
            "descricao": "Você receberá moedas em troca de perder um cargo aleatório.",
            "consequencia": "Perderá um cargo aleatório.",
            "perde_cargo": True,
            "rejeitar_custo": 1000,
            "cor": 0x3498DB,
            "encadeia": False,
        },
        {
            "nome": "🎲 Pacto do Dobro ou Nada",
            "tipo": "dobro_ou_nada",
            "recompensa_min": 10000, "recompensa_max": 40000,
            "descricao": "50% de chance de dobrar todas as suas moedas. 50% de perder tudo.",
            "consequencia": "Dobra o saldo ou perde tudo.",
            "perde_cargo": False,
            "rejeitar_custo": 1000,
            "cor": 0xF39C12,
            "encadeia": False,
        },
        {
            "nome": "🦹 Pacto do Ladrão",
            "tipo": "ladrao",
            "recompensa_min": 0,     "recompensa_max": 0,
            "descricao": "O Cassino aponta um alvo. Você rouba as moedas dele, mas perde um cargo.",
            "consequencia": "Rouba moedas de outro membro e perde um cargo.",
            "perde_cargo": True,
            "rejeitar_custo": 1500,
            "cor": 0xE67E22,
            "encadeia": False,
        },
        {
            "nome": "🔫 Pacto da Roleta Russa",
            "tipo": "roleta_russa",
            "recompensa_min": 20000, "recompensa_max": 50000,
            "descricao": "Seis câmaras. Uma bala. O Cassino aposta na sua sorte.",
            "consequencia": "1 em 6 de perder todos os cargos. 5 em 6 recebe a recompensa.",
            "perde_cargo": False,
            "rejeitar_custo": 2000,
            "cor": 0xE74C3C,
            "encadeia": False,
        },
    ],
    "epico": [
        {
            "nome": "👁️ Pacto do Dealer",
            "tipo": "normal",
            "recompensa_min": 50000, "recompensa_max": 75000,
            "descricao": "O Cassino reconheceu seu nome. A oferta é alta, mas o preço também.",
            "consequencia": "Perderá um cargo aleatório.",
            "perde_cargo": True,
            "rejeitar_custo": 5000,
            "cor": 0x9B59B6,
            "encadeia": True,
        },
        {
            "nome": "🎭 Pacto da Troca",
            "tipo": "troca",
            "recompensa_min": 20000, "recompensa_max": 60000,
            "descricao": "O Cassino escolhe um membro aleatório. Vocês trocam um cargo entre si.",
            "consequencia": "Troca um cargo com outro membro aleatório.",
            "perde_cargo": False,
            "rejeitar_custo": 3000,
            "cor": 0x2ECC71,
            "encadeia": True,
        },
        {
            "nome": "🌀 Pacto do Caos",
            "tipo": "caos",
            "recompensa_min": 30000, "recompensa_max": 70000,
            "descricao": "Ninguém sabe o que vai acontecer. Nem o Dealer. O Caos decide.",
            "consequencia": "Efeito completamente aleatório.",
            "perde_cargo": False,
            "rejeitar_custo": 5000,
            "cor": 0x1ABC9C,
            "encadeia": True,
        },
        {
            "nome": "🔄 Pacto da Inversão",
            "tipo": "inversao",
            "recompensa_min": 40000, "recompensa_max": 80000,
            "descricao": "Entregue um cargo e receba moedas e um título especial temporário.",
            "consequencia": "Perde um cargo aleatório. Ganha recompensa em moedas.",
            "perde_cargo": True,
            "rejeitar_custo": 5000,
            "cor": 0x8E44AD,
            "encadeia": False,
        },
    ],
    "lendario": [
        {
            "nome": "💀 Pacto da Ruína",
            "tipo": "normal",
            "recompensa_min": 75000,  "recompensa_max": 100000,
            "descricao": "Uma proposta rara surgiu. Poucos recebem. Menos ainda aceitam.",
            "consequencia": "Perderá um cargo aleatório.",
            "perde_cargo": True,
            "rejeitar_custo": 10000,
            "cor": 0xFFD700,
            "encadeia": True,
        },
        {
            "nome": "💀 Pacto do Diabo",
            "tipo": "diabo",
            "recompensa_min": 200000, "recompensa_max": 500000,
            "descricao": "A maior oferta que o Cassino já fez. Recompensa absurda. Preço? Tudo.",
            "consequencia": "Perde TODOS os cargos não protegidos.",
            "perde_cargo": False,
            "rejeitar_custo": 20000,
            "cor": 0xFF0000,
            "encadeia": False,
        },
    ],
}

PESOS = {"comum": 60, "raro": 25, "epico": 12, "lendario": 3}

EMBLEMAS = {
    "comum":    "⚪ Comum",
    "raro":     "🔵 Raro",
    "epico":    "🟣 Épico",
    "lendario": "🟡 Lendário",
}

SEPARADOR = "```\n ─────────────────────────── \n```"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#               BANCO EM MEMÓRIA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

historico:  dict[int, dict] = {}
seguros:    dict[int, dict] = {}   # {uid: {cargo_id: timestamp_expira}}
cooldowns:  dict[int, float] = {}  # {uid: timestamp_expira}

def _hist(uid: int) -> dict:
    if uid not in historico:
        historico[uid] = {"aceitos": 0, "recusados": 0, "cargos_perdidos": 0,
                          "moedas_ganhas": 0, "lendarios": 0}
    return historico[uid]

def registrar(uid: int, raridade: str, resultado: str, moedas: int):
    h = _hist(uid)
    if resultado == "aceito":
        h["aceitos"] += 1
        h["moedas_ganhas"] += moedas
        if raridade == "lendario":
            h["lendarios"] += 1
    else:
        h["recusados"] += 1

def cargo_segurado(uid: int, cargo_id: int) -> bool:
    exp = seguros.get(uid, {}).get(cargo_id, 0)
    return datetime.now(timezone.utc).timestamp() < exp

def em_cooldown(uid: int) -> bool:
    return datetime.now(timezone.utc).timestamp() < cooldowns.get(uid, 0)

def set_cooldown(uid: int):
    cooldowns[uid] = datetime.now(timezone.utc).timestamp() + COOLDOWN_HORAS

def sortear(raridade: str = None) -> tuple[dict, str]:
    if not raridade:
        raridade = random.choices(list(PESOS), weights=list(PESOS.values()), k=1)[0]
    p = random.choice(PACTOS[raridade]).copy()
    p["recompensa"] = random.randint(p["recompensa_min"], p["recompensa_max"])
    return p, raridade

def cargos_removiveis(membro: discord.Member, uid: int) -> list:
    return [
        c for c in membro.roles
        if c.name != "@everyone"
        and not c.managed
        and c.id not in CARGOS_PROTEGIDOS
        and c < membro.guild.me.top_role
        and not cargo_segurado(uid, c.id)
    ]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#              LÓGICA DOS TIPOS ESPECIAIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def executar_tipo(membro: discord.Member, pacto: dict) -> tuple[str, int]:
    tipo      = pacto.get("tipo", "normal")
    recompensa = pacto["recompensa"]
    desc      = ""

    # ── NORMAL ───────────────────────────────────────
    if tipo == "normal":
        adicionar_moedas(membro.id, recompensa)
        cargo_removido = None
        if pacto.get("perde_cargo"):
            validos = cargos_removiveis(membro, membro.id)
            if validos:
                cargo_removido = random.choice(validos)
                try:
                    await membro.remove_roles(cargo_removido, reason="Pacto aceito")
                    historico[membro.id]["cargos_perdidos"] = \
                        historico.get(membro.id, {}).get("cargos_perdidos", 0) + 1
                except Exception:
                    cargo_removido = None
        desc = (
            f"🪙 **+{recompensa:,} Moedas do Diabo** recebidas.\n\n"
            f"{'🎭 Cargo perdido: **' + cargo_removido.name + '**' if cargo_removido else '🎭 Nenhum cargo pôde ser removido.'}"
        )

    # ── DOBRO OU NADA ─────────────────────────────────
    elif tipo == "dobro_ou_nada":
        saldo = get_moedas(membro.id)
        if random.random() < 0.5:
            adicionar_moedas(membro.id, saldo)
            recompensa = saldo
            desc = (
                f"🎲 **A sorte sorriu!**\n\n"
                f"Suas moedas foram **dobradas**.\n"
                f"🪙 **+{saldo:,} Moedas do Diabo**"
            )
        else:
            remover_moedas(membro.id, saldo)
            recompensa = 0
            desc = (
                f"💀 **A casa ganhou.**\n\n"
                f"Você perdeu **tudo**.\n"
                f"🪙 **-{saldo:,} Moedas do Diabo**"
            )

    # ── ROLETA RUSSA ──────────────────────────────────
    elif tipo == "roleta_russa":
        bala = random.randint(1, 6) == 1
        if bala:
            validos = cargos_removiveis(membro, membro.id)
            removidos = []
            for c in validos:
                try:
                    await membro.remove_roles(c, reason="Roleta Russa")
                    removidos.append(f"**{c.name}**")
                except Exception:
                    pass
            recompensa = 0
            desc = (
                f"🔫 **BANG! A câmara tinha bala.**\n\n"
                f"Todos os seus cargos foram removidos!\n\n"
                f"Perdidos: {', '.join(removidos) if removidos else 'nenhum'}"
            )
        else:
            adicionar_moedas(membro.id, recompensa)
            desc = (
                f"🎲 **Câmara vazia. Você sobreviveu.**\n\n"
                f"🪙 **+{recompensa:,} Moedas do Diabo**"
            )

    # ── CAOS ──────────────────────────────────────────
    elif tipo == "caos":
        efeito = random.choice(["bonus", "perda", "cargo", "dobro", "nada", "roubo"])
        if efeito == "bonus":
            bonus = random.randint(5000, 50000)
            adicionar_moedas(membro.id, bonus)
            recompensa = bonus
            desc = f"🌀 **O Caos foi gentil.**\n\n🪙 **+{bonus:,} Moedas do Diabo**"
        elif efeito == "perda":
            perda = random.randint(1000, 20000)
            saldo = get_moedas(membro.id)
            remover_moedas(membro.id, min(perda, saldo))
            recompensa = 0
            desc = f"🌀 **O Caos cobrou seu preço.**\n\n🪙 **-{min(perda,saldo):,} Moedas do Diabo**"
        elif efeito == "cargo":
            validos = cargos_removiveis(membro, membro.id)
            if validos:
                c = random.choice(validos)
                try:
                    await membro.remove_roles(c, reason="Pacto do Caos")
                    desc = f"🌀 **O Caos removeu algo seu.**\n\n🎭 Cargo perdido: **{c.name}**"
                except Exception:
                    desc = "🌀 **O Caos tentou algo, mas falhou.**"
            else:
                desc = "🌀 **O Caos não encontrou nada para remover.**"
            recompensa = 0
        elif efeito == "dobro":
            saldo = get_moedas(membro.id)
            adicionar_moedas(membro.id, saldo)
            recompensa = saldo
            desc = f"🌀 **O Caos dobrou tudo!**\n\n🪙 **+{saldo:,} Moedas do Diabo**"
        elif efeito == "roubo":
            membros_alvo = [
                m for m in membro.guild.members
                if not m.bot and m.id != membro.id and get_moedas(m.id) > 0
            ]
            if membros_alvo:
                alvo = random.choice(membros_alvo)
                roubo = int(get_moedas(alvo.id) * random.uniform(0.1, 0.3))
                remover_moedas(alvo.id, roubo)
                adicionar_moedas(membro.id, roubo)
                recompensa = roubo
                desc = (
                    f"🌀 **O Caos roubou para você.**\n\n"
                    f"🎯 Alvo: **{alvo.display_name}**\n"
                    f"🪙 **+{roubo:,} Moedas do Diabo** roubadas"
                )
            else:
                desc = "🌀 **O Caos não encontrou alvo. Nada aconteceu.**"
                recompensa = 0
        else:
            desc = "🌀 **O Caos não fez nada desta vez.**\n\n> Ou fez? Ninguém sabe."
            recompensa = 0

    # ── PACTO DO DIABO ────────────────────────────────
    elif tipo == "diabo":
        adicionar_moedas(membro.id, recompensa)
        validos = cargos_removiveis(membro, membro.id)
        removidos = []
        for c in validos:
            try:
                await membro.remove_roles(c, reason="Pacto do Diabo")
                removidos.append(f"**{c.name}**")
            except Exception:
                pass
        desc = (
            f"💀 **O Diabo cobrou tudo.**\n\n"
            f"🪙 **+{recompensa:,} Moedas do Diabo**\n\n"
            f"Cargos removidos: {', '.join(removidos) if removidos else 'nenhum'}"
        )

    # ── LADRÃO ────────────────────────────────────────
    elif tipo == "ladrao":
        membros_alvo = [
            m for m in membro.guild.members
            if not m.bot and m.id != membro.id and get_moedas(m.id) > 0
        ]
        if membros_alvo:
            alvo = random.choice(membros_alvo)
            saldo_alvo = get_moedas(alvo.id)
            roubo = int(saldo_alvo * random.uniform(0.1, 0.4))
            remover_moedas(alvo.id, roubo)
            adicionar_moedas(membro.id, roubo)
            recompensa = roubo

            # Remove cargo do ladrão
            validos = cargos_removiveis(membro, membro.id)
            cargo_perdido = None
            if validos:
                cargo_perdido = random.choice(validos)
                try:
                    await membro.remove_roles(cargo_perdido, reason="Pacto do Ladrão")
                except Exception:
                    cargo_perdido = None

            # Notifica alvo
            try:
                aviso = discord.Embed(
                    title="🦹 Você foi roubado!",
                    description=(
                        f"**{membro.display_name}** assinou um **Pacto do Ladrão**.\n\n"
                        f"🪙 Você perdeu **{roubo:,} Moedas do Diabo**.\n\n"
                        "> O Cassino do Diabo não garante segurança."
                    ),
                    color=0xE67E22
                )
                aviso.set_footer(text="Cassino do Diabo • Pacto do Ladrão")
                aviso.timestamp = discord.utils.utcnow()
                await alvo.send(embed=aviso)
            except Exception:
                pass

            desc = (
                f"🦹 **Roubo efetuado com sucesso!**\n\n"
                f"🎯 Alvo: **{alvo.display_name}**\n"
                f"🪙 **+{roubo:,} Moedas do Diabo** roubadas\n\n"
                f"{'🎭 Cargo perdido: **' + cargo_perdido.name + '**' if cargo_perdido else '🎭 Nenhum cargo removido.'}"
            )
        else:
            adicionar_moedas(membro.id, recompensa)
            desc = (
                f"🦹 **Nenhum alvo encontrado.**\n\n"
                f"O Cassino compensou com moedas.\n"
                f"🪙 **+{recompensa:,} Moedas do Diabo**"
            )

    # ── TROCA ─────────────────────────────────────────
    elif tipo == "troca":
        membros_alvo = [
            m for m in membro.guild.members
            if not m.bot and m.id != membro.id
            and len(cargos_removiveis(m, m.id)) > 0
        ]
        meus_cargos = cargos_removiveis(membro, membro.id)

        if membros_alvo and meus_cargos:
            alvo = random.choice(membros_alvo)
            cargos_alvo = cargos_removiveis(alvo, alvo.id)

            if cargos_alvo:
                meu_cargo  = random.choice(meus_cargos)
                seu_cargo  = random.choice(cargos_alvo)
                try:
                    await membro.remove_roles(meu_cargo,  reason="Pacto da Troca")
                    await membro.add_roles(seu_cargo,     reason="Pacto da Troca")
                    await alvo.remove_roles(seu_cargo,    reason="Pacto da Troca")
                    await alvo.add_roles(meu_cargo,       reason="Pacto da Troca")
                    adicionar_moedas(membro.id, recompensa)

                    try:
                        aviso = discord.Embed(
                            title="🎭 Troca de Cargo!",
                            description=(
                                f"**{membro.display_name}** assinou um **Pacto da Troca** com você.\n\n"
                                f"❌ Você perdeu: **{seu_cargo.name}**\n"
                                f"✅ Você ganhou: **{meu_cargo.name}**\n\n"
                                "> O Cassino do Diabo selou o acordo."
                            ),
                            color=0x2ECC71
                        )
                        aviso.set_footer(text="Cassino do Diabo • Pacto da Troca")
                        aviso.timestamp = discord.utils.utcnow()
                        await alvo.send(embed=aviso)
                    except Exception:
                        pass

                    desc = (
                        f"🎭 **Troca realizada!**\n\n"
                        f"🤝 Com: **{alvo.display_name}**\n"
                        f"❌ Você perdeu: **{meu_cargo.name}**\n"
                        f"✅ Você ganhou: **{seu_cargo.name}**\n\n"
                        f"🪙 **+{recompensa:,} Moedas do Diabo**"
                    )
                except Exception:
                    adicionar_moedas(membro.id, recompensa)
                    desc = f"🎭 **Troca falhou. O Cassino compensou.**\n\n🪙 **+{recompensa:,} Moedas do Diabo**"
            else:
                adicionar_moedas(membro.id, recompensa)
                desc = f"🎭 **Nenhum cargo disponível no alvo.**\n\n🪙 **+{recompensa:,} Moedas do Diabo**"
        else:
            adicionar_moedas(membro.id, recompensa)
            desc = f"🎭 **Nenhum alvo encontrado. O Cassino compensou.**\n\n🪙 **+{recompensa:,} Moedas do Diabo**"

    # ── INVERSÃO ──────────────────────────────────────
    elif tipo == "inversao":
        adicionar_moedas(membro.id, recompensa)
        validos = cargos_removiveis(membro, membro.id)
        cargo_perdido = None
        if validos:
            cargo_perdido = random.choice(validos)
            try:
                await membro.remove_roles(cargo_perdido, reason="Pacto da Inversão")
            except Exception:
                cargo_perdido = None
        desc = (
            f"🔄 **Inversão concluída!**\n\n"
            f"🪙 **+{recompensa:,} Moedas do Diabo**\n\n"
            f"{'🎭 Cargo perdido: **' + cargo_perdido.name + '**' if cargo_perdido else '🎭 Nenhum cargo removido.'}"
        )

    return desc, recompensa


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                    VIEWS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PactoView(discord.ui.View):
    def __init__(self, membro: discord.Member, pacto: dict, raridade: str, cog):
        super().__init__(timeout=TIMEOUT_PACTO)
        self.membro   = membro
        self.pacto    = pacto
        self.raridade = raridade
        self.cog      = cog
        self.respondido = False
        self.message    = None

    async def on_timeout(self):
        if self.respondido:
            return
        for item in self.children:
            item.disabled = True
        embed = discord.Embed(
            title="⏳  PACTO EXPIRADO",
            description=(
                f"### {self.pacto['nome']}\n"
                f"-# {EMBLEMAS[self.raridade]}\n\n"
                "O tempo acabou. O Cassino retirou a oferta.\n\n"
                "> *Quem hesita, perde.*"
            ),
            color=0x555555
        )
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Expirado")
        embed.timestamp = discord.utils.utcnow()
        try:
            await self.message.edit(embed=embed, view=self)
        except Exception:
            pass

    @discord.ui.button(label="Assinar o Pacto", emoji="☠️", style=discord.ButtonStyle.danger)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.membro.id:
            return await interaction.response.send_message(
                "❌ Este pacto não pertence a você.", ephemeral=True)
        if self.respondido:
            return await interaction.response.send_message(
                "⚠️ Este pacto já foi decidido.", ephemeral=True)

        self.respondido = True
        registrar(self.membro.id, self.raridade, "aceito", 0)

        resultado_desc, moedas = await executar_tipo(self.membro, self.pacto)
        registrar(self.membro.id, self.raridade, "aceito", moedas)

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="☠️  PACTO ASSINADO",
            description=(
                f"### {self.pacto['nome']}\n"
                f"-# {EMBLEMAS[self.raridade]}\n\n"
                f"{resultado_desc}\n\n"
                f"{SEPARADOR}"
                "> *A casa sempre cobra.*"
            ),
            color=self.pacto["cor"]
        )
        embed.set_thumbnail(url=self.membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Proibido")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.edit_message(embed=embed, view=self)

        # DM de cargo perdido
        if self.pacto.get("perde_cargo") and self.pacto["tipo"] == "normal":
            try:
                aviso = discord.Embed(
                    title="🎭 Cargo Removido",
                    description="Um cargo foi removido como consequência do seu pacto.",
                    color=0x8B0000
                )
                aviso.set_footer(text="Cassino do Diabo  •  Pacto Proibido")
                await self.membro.send(embed=aviso)
            except Exception:
                pass

        await self.cog.enviar_log(
            self.membro, self.pacto, self.raridade, "aceito", moedas)

        if self.raridade == "lendario":
            await self.cog.anuncio_publico(self.membro, self.pacto)

        if self.pacto.get("encadeia"):
            await asyncio.sleep(6)
            await self.cog.enviar_pacto_encadeado(self.membro)

    @discord.ui.button(label="Recusar", emoji="❌", style=discord.ButtonStyle.secondary)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.membro.id:
            return await interaction.response.send_message(
                "❌ Este pacto não pertence a você.", ephemeral=True)
        if self.respondido:
            return await interaction.response.send_message(
                "⚠️ Este pacto já foi decidido.", ephemeral=True)

        self.respondido = True
        custo   = self.pacto.get("rejeitar_custo", 0)
        cobrado = 0
        if custo > 0:
            saldo = get_moedas(self.membro.id)
            cobrado = min(custo, saldo)
            if cobrado > 0:
                remover_moedas(self.membro.id, cobrado)

        registrar(self.membro.id, self.raridade, "recusado", 0)

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="📜  PACTO RECUSADO",
            description=(
                f"### {self.pacto['nome']}\n"
                f"-# {EMBLEMAS[self.raridade]}\n\n"
                "Você recusou a proposta do Cassino.\n\n"
                + (f"💸 O Cassino cobrou **{cobrado:,} Moedas** pela recusa.\n\n"
                   if cobrado else "")
                + f"{SEPARADOR}"
                "> *Talvez ele não ofereça novamente.*"
            ),
            color=0x2C2C2C
        )
        embed.set_thumbnail(url=self.membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Proibido")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.edit_message(embed=embed, view=self)
        await self.cog.enviar_log(
            self.membro, self.pacto, self.raridade, "recusado", 0)


class PactoColetivoView(discord.ui.View):
    def __init__(self, pacto: dict, raridade: str, cog):
        super().__init__(timeout=TIMEOUT_PACTO)
        self.pacto      = pacto
        self.raridade   = raridade
        self.cog        = cog
        self.reivindicado = False

    @discord.ui.button(label="Reivindicar", emoji="🤝", style=discord.ButtonStyle.success)
    async def reivindicar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.reivindicado:
            return await interaction.response.send_message(
                "❌ Este pacto já foi reivindicado!", ephemeral=True)

        self.reivindicado = True
        membro = interaction.guild.get_member(interaction.user.id)

        resultado_desc, moedas = await executar_tipo(membro, self.pacto)
        registrar(membro.id, self.raridade, "aceito", moedas)

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="🤝  PACTO REIVINDICADO",
            description=(
                f"### {self.pacto['nome']}\n"
                f"-# {EMBLEMAS[self.raridade]}\n\n"
                f"{membro.mention} assinou o pacto coletivo!\n\n"
                f"{resultado_desc}\n\n"
                f"{SEPARADOR}"
                "> *A casa sempre encontra seu dono.*"
            ),
            color=self.pacto["cor"]
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Coletivo")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.edit_message(embed=embed, view=self)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                    COG PRINCIPAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Pactos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── Helpers ──────────────────────────────────────

    def _embed_pacto(self, membro: discord.Member, pacto: dict, raridade: str) -> discord.Embed:
        expira_ts = int(discord.utils.utcnow().timestamp() + TIMEOUT_PACTO)
        embed = discord.Embed(
            title="☠️  UMA CARTA NEGRA APARECEU",
            description=(
                f"### {pacto['nome']}\n"
                f"-# {EMBLEMAS[raridade]}\n\n"
                "O Cassino do Diabo observou seus movimentos "
                "e enviou uma proposta diretamente a você.\n\n"
                f"{SEPARADOR}"
                f"📜 **Descrição**\n{pacto['descricao']}\n\n"
                f"🪙 **Recompensa**\n**{pacto['recompensa']:,} Moedas do Diabo**\n\n"
                f"🎭 **Consequência**\n{pacto['consequencia']}\n\n"
                f"💸 **Custo de recusa**\n{pacto.get('rejeitar_custo', 0):,} Moedas\n\n"
                f"{SEPARADOR}"
                f"⏳ Expira <t:{expira_ts}:R>\n\n"
                "> *Toda fortuna exige um sacrifício.*"
            ),
            color=pacto["cor"]
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Proibido")
        embed.timestamp = discord.utils.utcnow()
        return embed

    async def enviar_pacto_dm(self, membro: discord.Member, raridade: str = None):
        pacto, raridade = sortear(raridade)
        embed = self._embed_pacto(membro, pacto, raridade)
        view  = PactoView(membro, pacto, raridade, self)
        msg   = await membro.send(embed=embed, view=view)
        view.message = msg

    async def enviar_pacto_encadeado(self, membro: discord.Member):
        pacto, raridade = sortear(random.choice(["epico", "lendario"]))
        expira_ts = int(discord.utils.utcnow().timestamp() + TIMEOUT_PACTO)
        embed = discord.Embed(
            title="🔗  PACTO ENCADEADO DESBLOQUEADO",
            description=(
                f"### {pacto['nome']}\n"
                f"-# {EMBLEMAS[raridade]}\n\n"
                "Sua ousadia chamou a atenção do Cassino.\n"
                "Uma segunda proposta foi enviada.\n\n"
                f"{SEPARADOR}"
                f"📜 **Descrição**\n{pacto['descricao']}\n\n"
                f"🪙 **Recompensa**\n**{pacto['recompensa']:,} Moedas do Diabo**\n\n"
                f"🎭 **Consequência**\n{pacto['consequencia']}\n\n"
                f"{SEPARADOR}"
                f"⏳ Expira <t:{expira_ts}:R>\n\n"
                "> *O Cassino raramente oferece duas vezes.*"
            ),
            color=pacto["cor"]
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Encadeado")
        embed.timestamp = discord.utils.utcnow()
        view  = PactoView(membro, pacto, raridade, self)
        msg   = await membro.send(embed=embed, view=view)
        view.message = msg

    async def enviar_log(self, membro, pacto, raridade, resultado, moedas):
        if not ID_CANAL_LOG:
            return
        canal = membro.guild.get_channel(ID_CANAL_LOG)
        if not canal:
            return
        cor   = 0x2ECC71 if resultado == "aceito" else 0xE74C3C
        emoji = "✅" if resultado == "aceito" else "❌"
        embed = discord.Embed(
            title=f"{emoji}  Log de Pacto — {EMBLEMAS[raridade]}",
            color=cor,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="👤 Membro",    value=membro.mention,        inline=True)
        embed.add_field(name="📜 Pacto",     value=pacto["nome"],         inline=True)
        embed.add_field(name="🎯 Resultado", value=resultado.capitalize(), inline=True)
        if resultado == "aceito":
            embed.add_field(name="🪙 Moedas", value=f"{moedas:,}", inline=True)
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_footer(text="Cassino do Diabo  •  Sistema de Pactos")
        await canal.send(embed=embed)

    async def anuncio_publico(self, membro, pacto):
        if not ID_CANAL_PUBLICO:
            return
        canal = membro.guild.get_channel(ID_CANAL_PUBLICO)
        if not canal:
            return
        embed = discord.Embed(
            title="🟡  PACTO LENDÁRIO ACEITO",
            description=(
                f"{membro.mention} acabou de assinar um **Pacto Lendário**!\n\n"
                f"### {pacto['nome']}\n\n"
                "> *Poucos chegam até aqui. Menos ainda sobrevivem.*"
            ),
            color=0xFFD700
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Lendário")
        embed.timestamp = discord.utils.utcnow()
        await canal.send(embed=embed)

    # ── Comandos ──────────────────────────────────────

    @commands.command(name="pacto")
    @commands.has_permissions(administrator=True)
    async def cmd_pacto(self, ctx, membro: discord.Member, raridade: str = None):
        """Admin: envia pacto a um membro. Raridades: comum raro epico lendario"""
        try: await ctx.message.delete()
        except Exception: pass

        if membro.bot:
            return await ctx.send("❌ Não é possível enviar pactos para bots.", delete_after=8)
        if raridade and raridade not in PACTOS:
            return await ctx.send(
                "❌ Raridade inválida. Use: `comum` `raro` `epico` `lendario`", delete_after=8)

        try:
            await self.enviar_pacto_dm(membro, raridade)
            frases = [
                "☠️ O Dealer entregou uma carta negra.",
                "🎰 Um novo contrato foi enviado.",
                "👁️ O Cassino escolheu um novo alvo.",
                "📜 Um pacto proibido encontrou seu destino.",
                "💀 Nem todos recusam a oferta.",
            ]
            await ctx.send(random.choice(frases), delete_after=8)
        except discord.Forbidden:
            await ctx.send("❌ O membro está com a DM fechada.", delete_after=8)

    @commands.command(name="pactos")
    @commands.has_permissions(administrator=True)
    async def cmd_pactos(self, ctx):
        """Admin: envia pactos para múltiplos membros aleatórios"""
        try: await ctx.message.delete()
        except Exception: pass

        validos   = [m for m in ctx.guild.members if not m.bot]
        qtd       = random.randint(3, 7)
        escolhidos = random.sample(validos, min(qtd, len(validos)))
        if ctx.author not in escolhidos:
            escolhidos.append(ctx.author)

        enviados = 0
        for m in escolhidos:
            try:
                await self.enviar_pacto_dm(m)
                enviados += 1
            except Exception:
                pass

        await ctx.send(
            random.choice([
                f"☠️ O Dealer enviou cartas negras para **{enviados}** membro(s).",
                f"🎰 **{enviados}** contratos proibidos foram espalhados.",
                f"👁️ O Cassino escolheu **{enviados}** alvo(s).",
            ]), delete_after=10)

    @commands.command(name="pacto_coletivo")
    @commands.has_permissions(administrator=True)
    async def cmd_pacto_coletivo(self, ctx, raridade: str = None):
        """Admin: lança pacto coletivo no canal — o primeiro a clicar leva"""
        try: await ctx.message.delete()
        except Exception: pass

        if raridade and raridade not in PACTOS:
            return await ctx.send("❌ Raridade inválida.", delete_after=8)

        pacto, raridade = sortear(raridade)
        embed = discord.Embed(
            title="🤝  PACTO COLETIVO APARECEU",
            description=(
                f"### {pacto['nome']}\n"
                f"-# {EMBLEMAS[raridade]}\n\n"
                "O Cassino lançou uma oferta aberta.\n"
                "O **primeiro** a reivindicar leva tudo.\n\n"
                f"{SEPARADOR}"
                f"📜 **Descrição**\n{pacto['descricao']}\n\n"
                f"🪙 **Recompensa**\n**{pacto['recompensa']:,} Moedas do Diabo**\n\n"
                f"🎭 **Consequência**\n{pacto['consequencia']}\n\n"
                f"{SEPARADOR}"
                "> *A casa sempre encontra seu dono.*"
            ),
            color=pacto["cor"]
        )
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Coletivo")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed, view=PactoColetivoView(pacto, raridade, self))

    @commands.command(name="seguro")
    async def cmd_seguro(self, ctx, cargo: discord.Role):
        """Protege um cargo de pactos por 1 hora"""
        saldo = get_moedas(ctx.author.id)
        if saldo < CUSTO_SEGURO:
            return await ctx.send(
                f"❌ Você precisa de **{CUSTO_SEGURO:,} moedas**. "
                f"Você tem: **{saldo:,}**.", delete_after=10)
        if cargo.id in CARGOS_PROTEGIDOS:
            return await ctx.send("❌ Este cargo já é permanentemente protegido.", delete_after=8)
        if cargo not in ctx.author.roles:
            return await ctx.send("❌ Você não possui este cargo.", delete_after=8)

        remover_moedas(ctx.author.id, CUSTO_SEGURO)
        agora = datetime.now(timezone.utc).timestamp()
        if ctx.author.id not in seguros:
            seguros[ctx.author.id] = {}
        seguros[ctx.author.id][cargo.id] = agora + DURACAO_SEGURO

        embed = discord.Embed(
            title="🛡️  Seguro Contratado",
            description=(
                f"O cargo **{cargo.name}** está protegido de pactos.\n\n"
                f"🪙 Custo: **{CUSTO_SEGURO:,} moedas**\n"
                f"⏳ Expira: <t:{int(agora + DURACAO_SEGURO)}:R>"
            ),
            color=0x2ECC71
        )
        embed.set_footer(text="Cassino do Diabo  •  Sistema de Seguro")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="meus_pactos")
    async def cmd_meus_pactos(self, ctx):
        """Veja seu histórico de pactos"""
        h = historico.get(ctx.author.id)
        if not h:
            return await ctx.send(
                "📜 Você ainda não participou de nenhum pacto.", delete_after=10)

        embed = discord.Embed(
            title="📜  Seus Pactos",
            description=(
                f"Histórico de **{ctx.author.display_name}** no sistema de pactos."
            ),
            color=0x8B0000
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="✅ Aceitos",        value=str(h["aceitos"]),        inline=True)
        embed.add_field(name="❌ Recusados",      value=str(h["recusados"]),      inline=True)
        embed.add_field(name="🎭 Cargos Perdidos",value=str(h["cargos_perdidos"]),inline=True)
        embed.add_field(name="🪙 Moedas Ganhas",  value=f"{h['moedas_ganhas']:,}", inline=True)
        embed.add_field(name="🟡 Lendários",      value=str(h["lendarios"]),      inline=True)
        embed.set_footer(text="Cassino do Diabo  •  Histórico de Pactos")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="ranking_pactos")
    async def cmd_ranking(self, ctx):
        """Top 10 membros com mais moedas ganhas em pactos"""
        if not historico:
            return await ctx.send("📊 Nenhum pacto registrado ainda.", delete_after=10)

        top = sorted(historico.items(), key=lambda x: x[1]["moedas_ganhas"], reverse=True)[:10]

        linhas = []
        medalhas = ["🥇", "🥈", "🥉"]
        for i, (uid, h) in enumerate(top):
            membro = ctx.guild.get_member(uid)
            nome   = membro.display_name if membro else f"ID {uid}"
            medal  = medalhas[i] if i < 3 else f"`{i+1}.`"
            linhas.append(
                f"{medal} **{nome}** — 🪙 {h['moedas_ganhas']:,} moedas "
                f"| ✅ {h['aceitos']} aceitos"
            )

        embed = discord.Embed(
            title="🏆  Ranking de Pactos",
            description="\n".join(linhas),
            color=0xFFD700
        )
        embed.set_footer(text="Cassino do Diabo  •  Ranking")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    # ── Listener ──────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not isinstance(message.author, discord.Member):
            return
        if em_cooldown(message.author.id):
            return
        if random.randint(1, CHANCE_BASE) > CHANCE_PACTO:
            return

        set_cooldown(message.author.id)
        try:
            await self.enviar_pacto_dm(message.author)
        except discord.Forbidden:
            pass


async def setup(bot):
    await bot.add_cog(Pactos(bot))