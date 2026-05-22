import random
import asyncio
import discord
from discord.ext import commands
from datetime import datetime, timezone

from utils import cassino_db as _db

# ── Importação compatível ────────────────────────────────────
adicionar_moedas = getattr(_db, "adicionar_moedas", None) or getattr(_db, "add_moedas", None)
remover_moedas   = getattr(_db, "remover_moedas",   None) or getattr(_db, "remove_moedas", None)
get_moedas       = (getattr(_db, "get_moedas", None) or getattr(_db, "obter_saldo", None)
                    or getattr(_db, "buscar_moedas", None) or getattr(_db, "get_saldo", None))

import sqlite3
from pathlib import Path

def _db_path() -> Path:
    for p in [Path("cassino.db"), Path("data/cassino.db"), Path("database/cassino.db")]:
        if p.exists(): return p
    return Path("cassino.db")

def _ensure():
    db = _db_path(); db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as c:
        c.execute("CREATE TABLE IF NOT EXISTS usuarios_cassino (user_id INTEGER PRIMARY KEY, moedas INTEGER NOT NULL DEFAULT 0)")
        c.commit()
    return db

if get_moedas is None:
    def get_moedas(uid):
        db = _ensure()
        with sqlite3.connect(db) as c:
            r = c.execute("SELECT moedas FROM usuarios_cassino WHERE user_id=?", (uid,)).fetchone()
            return int(r[0]) if r else 0

if adicionar_moedas is None:
    def adicionar_moedas(uid, qtd):
        db = _ensure()
        with sqlite3.connect(db) as c:
            c.execute("INSERT OR IGNORE INTO usuarios_cassino VALUES (?,0)", (uid,))
            c.execute("UPDATE usuarios_cassino SET moedas=moedas+? WHERE user_id=?", (max(0,int(qtd)), uid))
            c.commit()

if remover_moedas is None:
    def remover_moedas(uid, qtd):
        db = _ensure()
        with sqlite3.connect(db) as c:
            c.execute("INSERT OR IGNORE INTO usuarios_cassino VALUES (?,0)", (uid,))
            c.execute("UPDATE usuarios_cassino SET moedas=MAX(moedas-?,0) WHERE user_id=?", (max(0,int(qtd)), uid))
            c.commit()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                   CONFIGURAÇÕES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CHANCE_BASE    = 10000
CHANCE_PACTO   = 1
TIMEOUT_PACTO  = 300
CUSTO_SEGURO   = 5000
DURACAO_SEGURO = 3600
COOLDOWN_AUTO  = 3600

ID_CANAL_LOG     = 1507228052776681502
ID_CANAL_PUBLICO = 0

IMAGEM_PADRAO = "https://i.imgur.com/MX7rQpp.png"
SEPARADOR     = "```\n ─────────────────────────── \n```"

CARGOS_PROTEGIDOS = [
    1483191687927828766, 1480349452744265759, 1501356975491907664,
    1500545846427652166, 1480381506064093225, 1487560221202321600,
    1505698473125609636, 1505698594651373719, 1505698708711538829,
    1505701356743295048, 1505701448900411413, 1487272681685647510,
    1494113762947371202, 1494114100907741214, 1493475034503577611,
    1494134900360744961, 1487891283102924961, 1480350529027707001,
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
            "consequencia": "Perde um cargo menor.",
            "perde_cargo": True, "rejeitar_custo": 200,
            "cor": 0x808080, "encadeia": False,
        },
        {
            "nome": "🌫️ Pacto do Esquecimento",
            "tipo": "moedas_perda",
            "recompensa_min": 3000,  "recompensa_max": 8000,
            "descricao": "O Cassino oferece moedas em troca de uma parte das suas reservas.",
            "consequencia": "Perde 10% das moedas atuais.",
            "perde_cargo": False, "rejeitar_custo": 100,
            "cor": 0x7F8C8D, "encadeia": False,
        },
    ],
    "raro": [
        {
            "nome": "☠️ Pacto do Sacrifício",
            "tipo": "normal",
            "recompensa_min": 10000, "recompensa_max": 30000,
            "descricao": "Você receberá moedas em troca de perder um cargo aleatório.",
            "consequencia": "Perderá um cargo aleatório.",
            "perde_cargo": True, "rejeitar_custo": 1000,
            "cor": 0x3498DB, "encadeia": False,
        },
        {
            "nome": "🎲 Pacto do Dobro ou Nada",
            "tipo": "dobro_ou_nada",
            "recompensa_min": 10000, "recompensa_max": 40000,
            "descricao": "50% de chance de dobrar todas as suas moedas. 50% de perder tudo.",
            "consequencia": "Dobra o saldo ou perde tudo.",
            "perde_cargo": False, "rejeitar_custo": 1000,
            "cor": 0xF39C12, "encadeia": False,
        },
        {
            "nome": "🦹 Pacto do Ladrão",
            "tipo": "ladrao",
            "recompensa_min": 0,     "recompensa_max": 0,
            "descricao": "O Cassino aponta um alvo. Você rouba as moedas dele, mas perde um cargo.",
            "consequencia": "Rouba moedas de outro membro e perde um cargo.",
            "perde_cargo": True, "rejeitar_custo": 1500,
            "cor": 0xE67E22, "encadeia": False,
        },
        {
            "nome": "🔫 Pacto da Roleta Russa",
            "tipo": "roleta_russa",
            "recompensa_min": 20000, "recompensa_max": 50000,
            "descricao": "Seis câmaras. Uma bala. O Cassino aposta na sua sorte.",
            "consequencia": "1 em 6 de perder todos os cargos. 5 em 6 recebe a recompensa.",
            "perde_cargo": False, "rejeitar_custo": 2000,
            "cor": 0xE74C3C, "encadeia": False,
        },
        {
            "nome": "🎁 Pacto da Generosidade",
            "tipo": "bonus_puro",
            "recompensa_min": 8000,  "recompensa_max": 25000,
            "descricao": "O Cassino está de bom humor. Uma oferta sem armadilhas — desta vez.",
            "consequencia": "Nenhuma. Só moedas.",
            "perde_cargo": False, "rejeitar_custo": 500,
            "cor": 0x2ECC71, "encadeia": False,
        },
    ],
    "epico": [
        {
            "nome": "👁️ Pacto do Dealer",
            "tipo": "normal",
            "recompensa_min": 50000, "recompensa_max": 75000,
            "descricao": "O Cassino reconheceu seu nome. A oferta é alta, mas o preço também.",
            "consequencia": "Perderá um cargo aleatório.",
            "perde_cargo": True, "rejeitar_custo": 5000,
            "cor": 0x9B59B6, "encadeia": True,
        },
        {
            "nome": "🎭 Pacto da Troca",
            "tipo": "troca",
            "recompensa_min": 20000, "recompensa_max": 60000,
            "descricao": "O Cassino escolhe um membro aleatório. Vocês trocam um cargo entre si.",
            "consequencia": "Troca um cargo com outro membro aleatório.",
            "perde_cargo": False, "rejeitar_custo": 3000,
            "cor": 0x2ECC71, "encadeia": True,
        },
        {
            "nome": "🌀 Pacto do Caos",
            "tipo": "caos",
            "recompensa_min": 30000, "recompensa_max": 70000,
            "descricao": "Ninguém sabe o que vai acontecer. Nem o Dealer. O Caos decide.",
            "consequencia": "Efeito completamente aleatório.",
            "perde_cargo": False, "rejeitar_custo": 5000,
            "cor": 0x1ABC9C, "encadeia": True,
        },
        {
            "nome": "🔄 Pacto da Inversão",
            "tipo": "inversao",
            "recompensa_min": 40000, "recompensa_max": 80000,
            "descricao": "Entregue um cargo e receba uma recompensa generosa em moedas.",
            "consequencia": "Perde um cargo aleatório. Ganha recompensa em moedas.",
            "perde_cargo": True, "rejeitar_custo": 5000,
            "cor": 0x8E44AD, "encadeia": False,
        },
        {
            "nome": "💎 Pacto do Cofre",
            "tipo": "cofre",
            "recompensa_min": 60000, "recompensa_max": 120000,
            "descricao": "O Cassino abre um cofre secreto. O conteúdo é seu — por um preço em moedas.",
            "consequencia": "Perde 20% das moedas atuais. Ganha muito mais.",
            "perde_cargo": False, "rejeitar_custo": 5000,
            "cor": 0x3498DB, "encadeia": True,
        },
    ],
    "lendario": [
        {
            "nome": "💀 Pacto da Ruína",
            "tipo": "normal",
            "recompensa_min": 75000,  "recompensa_max": 100000,
            "descricao": "Uma proposta rara surgiu. Poucos recebem. Menos ainda aceitam.",
            "consequencia": "Perderá um cargo aleatório.",
            "perde_cargo": True, "rejeitar_custo": 10000,
            "cor": 0xFFD700, "encadeia": True,
        },
        {
            "nome": "💀 Pacto do Diabo",
            "tipo": "diabo",
            "recompensa_min": 200000, "recompensa_max": 500000,
            "descricao": "A maior oferta que o Cassino já fez. Recompensa absurda. Preço? Tudo.",
            "consequencia": "Perde TODOS os cargos não protegidos.",
            "perde_cargo": False, "rejeitar_custo": 20000,
            "cor": 0xFF0000, "encadeia": False,
        },
        {
            "nome": "👑 Pacto do Rei",
            "tipo": "rei",
            "recompensa_min": 100000, "recompensa_max": 200000,
            "descricao": "O Cassino oferece poder e riqueza. Nenhum cargo é removido — desta vez.",
            "consequencia": "Apenas moedas. Uma raridade.",
            "perde_cargo": False, "rejeitar_custo": 15000,
            "cor": 0xFFD700, "encadeia": True,
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#               BANCO EM MEMÓRIA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

historico: dict[int, dict] = {}
seguros:   dict[int, dict] = {}
cooldowns: dict[int, float] = {}

def _hist(uid):
    if uid not in historico:
        historico[uid] = {"aceitos":0,"recusados":0,"cargos_perdidos":0,"moedas_ganhas":0,"lendarios":0}
    return historico[uid]

def registrar(uid, raridade, resultado, moedas):
    h = _hist(uid)
    if resultado == "aceito":
        h["aceitos"] += 1; h["moedas_ganhas"] += moedas
        if raridade == "lendario": h["lendarios"] += 1
    else:
        h["recusados"] += 1

def cargo_segurado(uid, cargo_id):
    return datetime.now(timezone.utc).timestamp() < seguros.get(uid, {}).get(cargo_id, 0)

def em_cooldown(uid):
    return datetime.now(timezone.utc).timestamp() < cooldowns.get(uid, 0)

def set_cooldown(uid):
    cooldowns[uid] = datetime.now(timezone.utc).timestamp() + COOLDOWN_AUTO

def sortear(raridade=None):
    if not raridade:
        raridade = random.choices(list(PESOS), weights=list(PESOS.values()), k=1)[0]
    p = random.choice(PACTOS[raridade]).copy()
    p["recompensa"] = random.randint(p["recompensa_min"], p["recompensa_max"])
    return p, raridade

def cargos_removiveis(membro, uid):
    return [c for c in membro.roles
            if c.name != "@everyone" and not c.managed
            and c.id not in CARGOS_PROTEGIDOS
            and c < membro.guild.me.top_role
            and not cargo_segurado(uid, c.id)]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#              LÓGICA DOS TIPOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def executar_tipo(membro: discord.Member, pacto: dict) -> tuple[str, int]:
    tipo       = pacto.get("tipo", "normal")
    recompensa = pacto["recompensa"]

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
                    _hist(membro.id)["cargos_perdidos"] += 1
                except Exception:
                    cargo_removido = None
        return (
            f"🪙 **+{recompensa:,} Moedas do Diabo** recebidas.\n\n"
            f"{'🎭 Cargo perdido: **' + cargo_removido.name + '**' if cargo_removido else '🎭 Nenhum cargo pôde ser removido.'}",
            recompensa
        )

    # ── BONUS PURO ───────────────────────────────────
    elif tipo == "bonus_puro":
        adicionar_moedas(membro.id, recompensa)
        return f"🎁 **O Cassino foi generoso.**\n\n🪙 **+{recompensa:,} Moedas do Diabo**\n\n> *Nem sempre há um preço.*", recompensa

    # ── REI ──────────────────────────────────────────
    elif tipo == "rei":
        adicionar_moedas(membro.id, recompensa)
        return (
            f"👑 **O Cassino coroou você.**\n\n"
            f"🪙 **+{recompensa:,} Moedas do Diabo**\n\n"
            f"> *Poder real não precisa de sacrifícios.*",
            recompensa
        )

    # ── PERDA DE MOEDAS ──────────────────────────────
    elif tipo == "moedas_perda":
        saldo = get_moedas(membro.id)
        perda = int(saldo * 0.10)
        remover_moedas(membro.id, perda)
        adicionar_moedas(membro.id, recompensa)
        liquido = recompensa - perda
        return (
            f"🌫️ **Troca registrada.**\n\n"
            f"🪙 **+{recompensa:,}** recebidas\n"
            f"📉 **-{perda:,}** cobradas (10% do saldo)\n\n"
            f"💰 Líquido: **{'+'if liquido>=0 else ''}{liquido:,} Moedas do Diabo**",
            max(liquido, 0)
        )

    # ── COFRE ────────────────────────────────────────
    elif tipo == "cofre":
        saldo = get_moedas(membro.id)
        taxa  = int(saldo * 0.20)
        remover_moedas(membro.id, taxa)
        adicionar_moedas(membro.id, recompensa)
        return (
            f"💎 **Cofre aberto!**\n\n"
            f"🪙 **+{recompensa:,} Moedas do Diabo**\n"
            f"📉 Taxa cobrada: **-{taxa:,}** (20% do saldo)\n\n"
            f"> *O Cassino cobra pelo acesso. Sempre.*",
            recompensa
        )

    # ── DOBRO OU NADA ─────────────────────────────────
    elif tipo == "dobro_ou_nada":
        saldo = get_moedas(membro.id)
        if random.random() < 0.5:
            adicionar_moedas(membro.id, saldo)
            return f"🎲 **A sorte sorriu!**\n\nSuas moedas foram **dobradas**.\n🪙 **+{saldo:,} Moedas do Diabo**", saldo
        else:
            remover_moedas(membro.id, saldo)
            return f"💀 **A casa ganhou.**\n\nVocê perdeu **tudo**.\n🪙 **-{saldo:,} Moedas do Diabo**", 0

    # ── ROLETA RUSSA ──────────────────────────────────
    elif tipo == "roleta_russa":
        if random.randint(1, 6) == 1:
            validos  = cargos_removiveis(membro, membro.id)
            removidos = []
            for c in validos:
                try:
                    await membro.remove_roles(c, reason="Roleta Russa")
                    removidos.append(f"**{c.name}**")
                except Exception: pass
            return (
                f"🔫 **BANG! A câmara tinha bala.**\n\nTodos os seus cargos foram removidos!\n\n"
                f"Perdidos: {', '.join(removidos) if removidos else 'nenhum'}",
                0
            )
        else:
            adicionar_moedas(membro.id, recompensa)
            return f"🎲 **Câmara vazia. Você sobreviveu.**\n\n🪙 **+{recompensa:,} Moedas do Diabo**", recompensa

    # ── CAOS ──────────────────────────────────────────
    elif tipo == "caos":
        efeito = random.choice(["bonus","perda","cargo","dobro","nada","roubo","timeout_moedas"])
        if efeito == "bonus":
            b = random.randint(5000,50000); adicionar_moedas(membro.id, b)
            return f"🌀 **O Caos foi gentil.**\n\n🪙 **+{b:,} Moedas do Diabo**", b
        elif efeito == "perda":
            p = random.randint(1000,20000); s = get_moedas(membro.id); remover_moedas(membro.id, min(p,s))
            return f"🌀 **O Caos cobrou seu preço.**\n\n🪙 **-{min(p,s):,} Moedas do Diabo**", 0
        elif efeito == "cargo":
            validos = cargos_removiveis(membro, membro.id)
            if validos:
                c = random.choice(validos)
                try:
                    await membro.remove_roles(c, reason="Pacto do Caos")
                    return f"🌀 **O Caos removeu algo seu.**\n\n🎭 Cargo perdido: **{c.name}**", 0
                except Exception: pass
            return "🌀 **O Caos tentou, mas falhou.**", 0
        elif efeito == "dobro":
            s = get_moedas(membro.id); adicionar_moedas(membro.id, s)
            return f"🌀 **O Caos dobrou tudo!**\n\n🪙 **+{s:,} Moedas do Diabo**", s
        elif efeito == "roubo":
            alvos = [m for m in membro.guild.members if not m.bot and m.id != membro.id and get_moedas(m.id) > 0]
            if alvos:
                alvo = random.choice(alvos); r = int(get_moedas(alvo.id)*random.uniform(0.1,0.3))
                remover_moedas(alvo.id, r); adicionar_moedas(membro.id, r)
                return f"🌀 **O Caos roubou para você.**\n\n🎯 Alvo: **{alvo.display_name}**\n🪙 **+{r:,}** roubadas", r
            return "🌀 **O Caos não encontrou alvo.**", 0
        elif efeito == "timeout_moedas":
            s = get_moedas(membro.id); p = int(s*0.15); remover_moedas(membro.id, p)
            b = random.randint(10000,40000); adicionar_moedas(membro.id, b)
            return f"🌀 **O Caos redistribuiu sua riqueza.**\n\n📉 **-{p:,}** cobradas\n🪙 **+{b:,}** concedidas", b
        else:
            return "🌀 **O Caos não fez nada desta vez.**\n\n> *Ou fez? Ninguém sabe.*", 0

    # ── PACTO DO DIABO ────────────────────────────────
    elif tipo == "diabo":
        adicionar_moedas(membro.id, recompensa)
        validos  = cargos_removiveis(membro, membro.id)
        removidos = []
        for c in validos:
            try: await membro.remove_roles(c, reason="Pacto do Diabo"); removidos.append(f"**{c.name}**")
            except Exception: pass
        return (
            f"💀 **O Diabo cobrou tudo.**\n\n"
            f"🪙 **+{recompensa:,} Moedas do Diabo**\n\n"
            f"Cargos removidos: {', '.join(removidos) if removidos else 'nenhum'}",
            recompensa
        )

    # ── LADRÃO ────────────────────────────────────────
    elif tipo == "ladrao":
        alvos = [m for m in membro.guild.members if not m.bot and m.id != membro.id and get_moedas(m.id) > 0]
        if alvos:
            alvo   = random.choice(alvos)
            roubo  = int(get_moedas(alvo.id)*random.uniform(0.1,0.4))
            remover_moedas(alvo.id, roubo); adicionar_moedas(membro.id, roubo)
            validos = cargos_removiveis(membro, membro.id)
            cp = None
            if validos:
                cp = random.choice(validos)
                try: await membro.remove_roles(cp, reason="Pacto do Ladrão")
                except Exception: cp = None
            try:
                av = discord.Embed(title="🦹 Você foi roubado!",
                    description=f"**{membro.display_name}** assinou um **Pacto do Ladrão**.\n\n🪙 Você perdeu **{roubo:,} Moedas do Diabo**.\n\n> *O Cassino não garante segurança.*",
                    color=0xE67E22)
                av.set_footer(text="Cassino do Diabo  •  Pacto do Ladrão")
                av.timestamp = discord.utils.utcnow()
                await alvo.send(embed=av)
            except Exception: pass
            return (
                f"🦹 **Roubo efetuado!**\n\n🎯 Alvo: **{alvo.display_name}**\n"
                f"🪙 **+{roubo:,} Moedas do Diabo** roubadas\n\n"
                f"{'🎭 Cargo perdido: **'+cp.name+'**' if cp else '🎭 Nenhum cargo removido.'}",
                roubo
            )
        adicionar_moedas(membro.id, recompensa)
        return f"🦹 **Nenhum alvo encontrado.** O Cassino compensou.\n\n🪙 **+{recompensa:,}**", recompensa

    # ── TROCA ─────────────────────────────────────────
    elif tipo == "troca":
        alvos       = [m for m in membro.guild.members if not m.bot and m.id != membro.id and len(cargos_removiveis(m, m.id)) > 0]
        meus_cargos = cargos_removiveis(membro, membro.id)
        if alvos and meus_cargos:
            alvo        = random.choice(alvos)
            cargos_alvo = cargos_removiveis(alvo, alvo.id)
            if cargos_alvo:
                mc = random.choice(meus_cargos); sc = random.choice(cargos_alvo)
                try:
                    await membro.remove_roles(mc, reason="Pacto da Troca")
                    await membro.add_roles(sc, reason="Pacto da Troca")
                    await alvo.remove_roles(sc, reason="Pacto da Troca")
                    await alvo.add_roles(mc, reason="Pacto da Troca")
                    adicionar_moedas(membro.id, recompensa)
                    try:
                        av = discord.Embed(title="🎭 Troca de Cargo!",
                            description=f"**{membro.display_name}** assinou um **Pacto da Troca** com você.\n\n❌ Você perdeu: **{sc.name}**\n✅ Você ganhou: **{mc.name}**\n\n> *O Cassino do Diabo selou o acordo.*",
                            color=0x2ECC71)
                        av.set_footer(text="Cassino do Diabo  •  Pacto da Troca"); av.timestamp = discord.utils.utcnow()
                        await alvo.send(embed=av)
                    except Exception: pass
                    return (f"🎭 **Troca realizada!**\n\n🤝 Com: **{alvo.display_name}**\n❌ Você perdeu: **{mc.name}**\n✅ Você ganhou: **{sc.name}**\n\n🪙 **+{recompensa:,}**", recompensa)
                except Exception: pass
        adicionar_moedas(membro.id, recompensa)
        return f"🎭 **Troca falhou. O Cassino compensou.**\n\n🪙 **+{recompensa:,}**", recompensa

    # ── INVERSÃO ──────────────────────────────────────
    elif tipo == "inversao":
        adicionar_moedas(membro.id, recompensa)
        validos = cargos_removiveis(membro, membro.id); cp = None
        if validos:
            cp = random.choice(validos)
            try: await membro.remove_roles(cp, reason="Pacto da Inversão")
            except Exception: cp = None
        return (
            f"🔄 **Inversão concluída!**\n\n🪙 **+{recompensa:,} Moedas do Diabo**\n\n"
            f"{'🎭 Cargo perdido: **'+cp.name+'**' if cp else '🎭 Nenhum cargo removido.'}",
            recompensa
        )

    adicionar_moedas(membro.id, recompensa)
    return f"🪙 **+{recompensa:,} Moedas do Diabo**", recompensa


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                    VIEWS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PactoView(discord.ui.View):
    def __init__(self, membro, pacto, raridade, cog):
        super().__init__(timeout=TIMEOUT_PACTO)
        self.membro = membro; self.pacto = pacto; self.raridade = raridade
        self.cog = cog; self.respondido = False; self.message = None

    async def on_timeout(self):
        if self.respondido: return
        for i in self.children: i.disabled = True
        embed = discord.Embed(
            title="⏳  PACTO EXPIRADO",
            description=(f"### {self.pacto['nome']}\n-# {EMBLEMAS[self.raridade]}\n\n"
                         "O tempo acabou. O Cassino retirou a oferta.\n\n> *Quem hesita, perde.*"),
            color=0x555555)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Expirado")
        embed.timestamp = discord.utils.utcnow()
        try: await self.message.edit(embed=embed, view=self)
        except Exception: pass

    @discord.ui.button(label="Assinar o Pacto", emoji="☠️", style=discord.ButtonStyle.danger)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.membro.id:
            return await interaction.response.send_message("❌ Este pacto não pertence a você.", ephemeral=True)
        if self.respondido:
            return await interaction.response.send_message("⚠️ Este pacto já foi decidido.", ephemeral=True)
        self.respondido = True
        desc, moedas = await executar_tipo(self.membro, self.pacto)
        registrar(self.membro.id, self.raridade, "aceito", moedas)
        for i in self.children: i.disabled = True
        embed = discord.Embed(
            title="☠️  PACTO ASSINADO",
            description=(f"### {self.pacto['nome']}\n-# {EMBLEMAS[self.raridade]}\n\n"
                         f"{desc}\n\n{SEPARADOR}> *A casa sempre cobra.*"),
            color=self.pacto["cor"])
        embed.set_thumbnail(url=self.membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Proibido")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.edit_message(embed=embed, view=self)
        await self.cog.enviar_log(self.membro, self.pacto, self.raridade, "aceito", moedas)
        if self.raridade == "lendario": await self.cog.anuncio_publico(self.membro, self.pacto)
        if self.pacto.get("encadeia"):
            await asyncio.sleep(6)
            await self.cog.enviar_pacto_encadeado(self.membro)

    @discord.ui.button(label="Recusar", emoji="❌", style=discord.ButtonStyle.secondary)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.membro.id:
            return await interaction.response.send_message("❌ Este pacto não pertence a você.", ephemeral=True)
        if self.respondido:
            return await interaction.response.send_message("⚠️ Este pacto já foi decidido.", ephemeral=True)
        self.respondido = True
        custo = self.pacto.get("rejeitar_custo", 0); cobrado = 0
        if custo > 0:
            s = get_moedas(self.membro.id); cobrado = min(custo, s)
            if cobrado > 0: remover_moedas(self.membro.id, cobrado)
        registrar(self.membro.id, self.raridade, "recusado", 0)
        for i in self.children: i.disabled = True
        embed = discord.Embed(
            title="📜  PACTO RECUSADO",
            description=(f"### {self.pacto['nome']}\n-# {EMBLEMAS[self.raridade]}\n\n"
                         "Você recusou a proposta do Cassino.\n\n"
                         + (f"💸 O Cassino cobrou **{cobrado:,} Moedas** pela recusa.\n\n" if cobrado else "")
                         + f"{SEPARADOR}> *Talvez ele não ofereça novamente.*"),
            color=0x2C2C2C)
        embed.set_thumbnail(url=self.membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Proibido")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.edit_message(embed=embed, view=self)
        await self.cog.enviar_log(self.membro, self.pacto, self.raridade, "recusado", 0)


class PactoColetivoView(discord.ui.View):
    def __init__(self, pacto, raridade, cog):
        super().__init__(timeout=TIMEOUT_PACTO)
        self.pacto = pacto; self.raridade = raridade; self.cog = cog; self.reivindicado = False

    @discord.ui.button(label="Reivindicar", emoji="🤝", style=discord.ButtonStyle.success)
    async def reivindicar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.reivindicado:
            return await interaction.response.send_message("❌ Este pacto já foi reivindicado!", ephemeral=True)
        self.reivindicado = True
        membro = interaction.guild.get_member(interaction.user.id)
        desc, moedas = await executar_tipo(membro, self.pacto)
        registrar(membro.id, self.raridade, "aceito", moedas)
        for i in self.children: i.disabled = True
        embed = discord.Embed(
            title="🤝  PACTO REIVINDICADO",
            description=(f"### {self.pacto['nome']}\n-# {EMBLEMAS[self.raridade]}\n\n"
                         f"{membro.mention} assinou o pacto coletivo!\n\n{desc}\n\n{SEPARADOR}"
                         "> *A casa sempre encontra seu dono.*"),
            color=self.pacto["cor"])
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

    def _embed_pacto(self, membro, pacto, raridade):
        ts = int(discord.utils.utcnow().timestamp() + TIMEOUT_PACTO)
        embed = discord.Embed(
            title="☠️  UMA CARTA NEGRA APARECEU",
            description=(
                f"### {pacto['nome']}\n-# {EMBLEMAS[raridade]}\n\n"
                "O Cassino do Diabo observou seus movimentos e enviou uma proposta.\n\n"
                f"{SEPARADOR}"
                f"📜 **Descrição**\n{pacto['descricao']}\n\n"
                f"🪙 **Recompensa**\n**{pacto['recompensa']:,} Moedas do Diabo**\n\n"
                f"🎭 **Consequência**\n{pacto['consequencia']}\n\n"
                f"💸 **Custo de recusa**\n{pacto.get('rejeitar_custo',0):,} Moedas\n\n"
                f"{SEPARADOR}⏳ Expira <t:{ts}:R>\n\n> *Toda fortuna exige um sacrifício.*"
            ),
            color=pacto["cor"])
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Proibido")
        embed.timestamp = discord.utils.utcnow()
        return embed

    async def enviar_pacto_dm(self, membro, raridade=None):
        pacto, raridade = sortear(raridade)
        view = PactoView(membro, pacto, raridade, self)
        msg  = await membro.send(embed=self._embed_pacto(membro, pacto, raridade), view=view)
        view.message = msg

    async def enviar_pacto_encadeado(self, membro):
        pacto, raridade = sortear(random.choice(["epico","lendario"]))
        ts = int(discord.utils.utcnow().timestamp() + TIMEOUT_PACTO)
        embed = discord.Embed(
            title="🔗  PACTO ENCADEADO DESBLOQUEADO",
            description=(
                f"### {pacto['nome']}\n-# {EMBLEMAS[raridade]}\n\n"
                "Sua ousadia chamou a atenção do Cassino. Uma segunda proposta foi enviada.\n\n"
                f"{SEPARADOR}"
                f"📜 **Descrição**\n{pacto['descricao']}\n\n"
                f"🪙 **Recompensa**\n**{pacto['recompensa']:,} Moedas do Diabo**\n\n"
                f"🎭 **Consequência**\n{pacto['consequencia']}\n\n"
                f"{SEPARADOR}⏳ Expira <t:{ts}:R>\n\n> *O Cassino raramente oferece duas vezes.*"
            ),
            color=pacto["cor"])
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Encadeado")
        embed.timestamp = discord.utils.utcnow()
        view = PactoView(membro, pacto, raridade, self)
        msg  = await membro.send(embed=embed, view=view)
        view.message = msg

    async def enviar_log(self, membro, pacto, raridade, resultado, moedas):
        if not ID_CANAL_LOG: return
        canal = membro.guild.get_channel(ID_CANAL_LOG)
        if not canal: return
        cor = 0x2ECC71 if resultado == "aceito" else 0xE74C3C
        embed = discord.Embed(
            title=f"{'✅' if resultado=='aceito' else '❌'}  Log — {EMBLEMAS[raridade]}",
            color=cor, timestamp=discord.utils.utcnow())
        embed.add_field(name="👤 Membro",    value=membro.mention,         inline=True)
        embed.add_field(name="📜 Pacto",     value=pacto["nome"],          inline=True)
        embed.add_field(name="🎯 Resultado", value=resultado.capitalize(), inline=True)
        if resultado == "aceito":
            embed.add_field(name="🪙 Moedas", value=f"{moedas:,}", inline=True)
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_footer(text="Cassino do Diabo  •  Sistema de Pactos")
        await canal.send(embed=embed)

    async def anuncio_publico(self, membro, pacto):
        if not ID_CANAL_PUBLICO: return
        canal = membro.guild.get_channel(ID_CANAL_PUBLICO)
        if not canal: return
        embed = discord.Embed(
            title="🟡  PACTO LENDÁRIO ACEITO",
            description=(f"{membro.mention} assinou um **Pacto Lendário**!\n\n### {pacto['nome']}\n\n"
                         "> *Poucos chegam até aqui. Menos ainda sobrevivem.*"),
            color=0xFFD700)
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Lendário")
        embed.timestamp = discord.utils.utcnow()
        await canal.send(embed=embed)

    # ── Comandos ─────────────────────────────────────

    @commands.command(name="pacto")
    @commands.has_permissions(administrator=True)
    async def cmd_pacto(self, ctx, membro: discord.Member, raridade: str = None):
        try: await ctx.message.delete()
        except Exception: pass
        if membro.bot: return await ctx.send("❌ Bots não recebem pactos.", delete_after=8)
        if raridade and raridade not in PACTOS:
            return await ctx.send("❌ Raridade inválida. Use: `comum` `raro` `epico` `lendario`", delete_after=8)
        try:
            await self.enviar_pacto_dm(membro, raridade)
            await ctx.send(random.choice(["☠️ O Dealer entregou uma carta negra.","🎰 Um novo contrato foi enviado.","👁️ O Cassino escolheu um novo alvo.","📜 Um pacto proibido encontrou seu destino.","💀 Nem todos recusam a oferta."]), delete_after=8)
        except discord.Forbidden:
            await ctx.send("❌ O membro está com a DM fechada.", delete_after=8)

    @commands.command(name="pactos")
    @commands.has_permissions(administrator=True)
    async def cmd_pactos(self, ctx):
        try: await ctx.message.delete()
        except Exception: pass
        validos    = [m for m in ctx.guild.members if not m.bot]
        escolhidos = random.sample(validos, min(random.randint(3,7), len(validos)))
        if ctx.author not in escolhidos: escolhidos.append(ctx.author)
        enviados = 0
        for m in escolhidos:
            try: await self.enviar_pacto_dm(m); enviados += 1
            except Exception: pass
        await ctx.send(random.choice([f"☠️ Cartas negras enviadas para **{enviados}** membro(s).",f"🎰 **{enviados}** contratos espalhados.",f"👁️ O Cassino escolheu **{enviados}** alvo(s)."]), delete_after=10)

    @commands.command(name="pacto_coletivo")
    @commands.has_permissions(administrator=True)
    async def cmd_pacto_coletivo(self, ctx, raridade: str = None):
        try: await ctx.message.delete()
        except Exception: pass
        if raridade and raridade not in PACTOS: return await ctx.send("❌ Raridade inválida.", delete_after=8)
        pacto, raridade = sortear(raridade)
        embed = discord.Embed(
            title="🤝  PACTO COLETIVO APARECEU",
            description=(f"### {pacto['nome']}\n-# {EMBLEMAS[raridade]}\n\n"
                         "O Cassino lançou uma oferta aberta. O **primeiro** a reivindicar leva tudo.\n\n"
                         f"{SEPARADOR}📜 **Descrição**\n{pacto['descricao']}\n\n"
                         f"🪙 **Recompensa**\n**{pacto['recompensa']:,} Moedas do Diabo**\n\n"
                         f"🎭 **Consequência**\n{pacto['consequencia']}\n\n{SEPARADOR}"
                         "> *A casa sempre encontra seu dono.*"),
            color=pacto["cor"])
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Coletivo")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed, view=PactoColetivoView(pacto, raridade, self))

    @commands.command(name="seguro")
    async def cmd_seguro(self, ctx, cargo: discord.Role):
        saldo = get_moedas(ctx.author.id)
        if saldo < CUSTO_SEGURO:
            return await ctx.send(f"❌ Precisa de **{CUSTO_SEGURO:,}** moedas. Você tem: **{saldo:,}**.", delete_after=10)
        if cargo.id in CARGOS_PROTEGIDOS: return await ctx.send("❌ Este cargo já é permanentemente protegido.", delete_after=8)
        if cargo not in ctx.author.roles: return await ctx.send("❌ Você não possui este cargo.", delete_after=8)
        remover_moedas(ctx.author.id, CUSTO_SEGURO)
        agora = datetime.now(timezone.utc).timestamp()
        if ctx.author.id not in seguros: seguros[ctx.author.id] = {}
        seguros[ctx.author.id][cargo.id] = agora + DURACAO_SEGURO
        embed = discord.Embed(title="🛡️  Seguro Contratado",
            description=(f"O cargo **{cargo.name}** está protegido de pactos.\n\n"
                         f"🪙 Custo: **{CUSTO_SEGURO:,} moedas**\n⏳ Expira: <t:{int(agora+DURACAO_SEGURO)}:R>"),
            color=0x2ECC71)
        embed.set_footer(text="Cassino do Diabo  •  Sistema de Seguro")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="meus_pactos")
    async def cmd_meus_pactos(self, ctx):
        h = historico.get(ctx.author.id)
        if not h: return await ctx.send("📜 Você ainda não participou de nenhum pacto.", delete_after=10)
        embed = discord.Embed(title="📜  Seus Pactos",
            description=f"-# *\"O Cassino registra tudo.\"*\n\nHistórico de **{ctx.author.display_name}**.",
            color=0x8B0000)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="✅ Aceitos",         value=str(h["aceitos"]),         inline=True)
        embed.add_field(name="❌ Recusados",       value=str(h["recusados"]),       inline=True)
        embed.add_field(name="🎭 Cargos Perdidos", value=str(h["cargos_perdidos"]), inline=True)
        embed.add_field(name="🪙 Moedas Ganhas",   value=f"{h['moedas_ganhas']:,}", inline=True)
        embed.add_field(name="🟡 Lendários",       value=str(h["lendarios"]),       inline=True)
        embed.set_footer(text="Cassino do Diabo  •  Histórico de Pactos")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="ranking_pactos")
    async def cmd_ranking(self, ctx):
        if not historico: return await ctx.send("📊 Nenhum pacto registrado ainda.", delete_after=10)
        top = sorted(historico.items(), key=lambda x: x[1]["moedas_ganhas"], reverse=True)[:10]
        medalhas = ["🥇","🥈","🥉"]
        linhas = [
            f"{''.join([medalhas[i]] if i<3 else [f'`{i+1}.`'])} **{(ctx.guild.get_member(uid) or type('',(),{'display_name':f'ID {uid}'})()).display_name}** — 🪙 {h['moedas_ganhas']:,} | ✅ {h['aceitos']}"
            for i,(uid,h) in enumerate(top)
        ]
        embed = discord.Embed(title="🏆  Ranking de Pactos",
            description=f"-# *\"Riqueza conquistada com risco.\"*\n\n{SEPARADOR}" + "\n".join(linhas),
            color=0xFFD700)
        embed.set_footer(text="Cassino do Diabo  •  Ranking")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not isinstance(message.author, discord.Member): return
        if em_cooldown(message.author.id): return
        if random.randint(1, CHANCE_BASE) > CHANCE_PACTO: return
        set_cooldown(message.author.id)
        try: await self.enviar_pacto_dm(message.author)
        except discord.Forbidden: pass


async def setup(bot):
    await bot.add_cog(Pactos(bot))