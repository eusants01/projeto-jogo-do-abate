
from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Awaitable
import sqlite3

import discord
from discord.ext import commands

from utils import cassino_db as _db

log = logging.getLogger("pactos")

adicionar_moedas: Callable = (
    getattr(_db, "adicionar_moedas", None) or getattr(_db, "add_moedas", None)
)
remover_moedas: Callable = (
    getattr(_db, "remover_moedas", None) or getattr(_db, "remove_moedas", None)
)
get_moedas: Callable = (
    getattr(_db, "get_moedas", None)
    or getattr(_db, "obter_saldo", None)
    or getattr(_db, "buscar_moedas", None)
    or getattr(_db, "get_saldo", None)
)


def _db_path() -> Path:
    for p in [Path("cassino.db"), Path("data/cassino.db"), Path("database/cassino.db")]:
        if p.exists():
            return p
    return Path("cassino.db")


def _ensure() -> Path:
    db = _db_path()
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS usuarios_cassino "
            "(user_id INTEGER PRIMARY KEY, moedas INTEGER NOT NULL DEFAULT 0)"
        )
        c.commit()
    return db


if get_moedas is None:
    def get_moedas(uid: int) -> int:
        db = _ensure()
        with sqlite3.connect(db) as c:
            r = c.execute(
                "SELECT moedas FROM usuarios_cassino WHERE user_id=?", (uid,)
            ).fetchone()
            return int(r[0]) if r else 0

if adicionar_moedas is None:
    def adicionar_moedas(uid: int, qtd: int) -> None:
        db = _ensure()
        with sqlite3.connect(db) as c:
            c.execute("INSERT OR IGNORE INTO usuarios_cassino VALUES (?,0)", (uid,))
            c.execute(
                "UPDATE usuarios_cassino SET moedas=moedas+? WHERE user_id=?",
                (max(0, int(qtd)), uid),
            )
            c.commit()

if remover_moedas is None:
    def remover_moedas(uid: int, qtd: int) -> None:
        db = _ensure()
        with sqlite3.connect(db) as c:
            c.execute("INSERT OR IGNORE INTO usuarios_cassino VALUES (?,0)", (uid,))
            c.execute(
                "UPDATE usuarios_cassino SET moedas=MAX(moedas-?,0) WHERE user_id=?",
                (max(0, int(qtd)), uid),
            )
            c.commit()


# ──────────────────────────────────────────────────────
#  CONFIGURAÇÕES
# ──────────────────────────────────────────────────────

CHANCE_BASE      = 100          # 1 em N mensagens → pacto automático
CHANCE_PACTO     = 1
TIMEOUT_PACTO    = 300          # segundos para expirar
CUSTO_SEGURO     = 5_000        # moedas para contratar seguro de saldo
DURACAO_SEGURO   = 3_600        # duração do seguro em segundos
COOLDOWN_AUTO    = 3_600        # cooldown entre pactos automáticos

ID_CANAL_LOG     = 1507228052776681502
ID_CANAL_PUBLICO = 0            # 0 = desativado

IMAGEM_PADRAO = (
    "https://cdn.discordapp.com/attachments/1500528332008325281/"
    "1508349076108873728/content.png?ex=6a15370b&is=6a13e58b&"
    "hm=c08e065be149e22746d9b4495a94b37af25866cd0052441b6b027f72cc3d6be7&"
)
SEPARADOR = "```\n ─────────────────────────── \n```"


# ──────────────────────────────────────────────────────
#  CATÁLOGO DE PACTOS  (zero perda de cargo)
# ──────────────────────────────────────────────────────

PACTOS: dict[str, list[dict]] = {

    # ── COMUNS ────────────────────────────────────────
    "comum": [
        {
            "nome": "🌫️ Pacto do Esquecimento",
            "tipo": "moedas_perda_simples",
            "recompensa_min": 3_000, "recompensa_max": 8_000,
            "descricao": "O Cassino troca suas moedas atuais por um pacote maior — mas cobra uma fatia.",
            "consequencia": "Perde 10% do saldo atual. Ganha a recompensa.",
            "rejeitar_custo": 100,
            "cor": 0x7F8C8D, "encadeia": False,
        },
        {
            "nome": "📜 Contrato do Novato",
            "tipo": "bonus_puro",
            "recompensa_min": 1_000, "recompensa_max": 4_000,
            "descricao": "Uma oferta de boas-vindas. O Cassino quer que você volte mais.",
            "consequencia": "Nenhuma. Só moedas.",
            "rejeitar_custo": 100,
            "cor": 0x95A5A6, "encadeia": False,
        },
        {
            "nome": "🎯 Pacto do Apostador",
            "tipo": "aposta_simples",
            "recompensa_min": 2_000, "recompensa_max": 6_000,
            "descricao": "Cara ou coroa. O Cassino aposta contra você. Nível: iniciante.",
            "consequencia": "50% de ganhar o dobro. 50% de perder metade do valor.",
            "rejeitar_custo": 150,
            "cor": 0xBDC3C7, "encadeia": False,
        },
        {
            "nome": "💧 Pacto da Gota",
            "tipo": "drenagem_lenta",
            "recompensa_min": 5_000, "recompensa_max": 10_000,
            "descricao": "O Cassino vai cobrar 5% do seu saldo por 5 dias. Em troca, paga agora.",
            "consequencia": "Recebe a recompensa. Perde 5% do saldo por 5 dias consecutivos.",
            "rejeitar_custo": 200,
            "cor": 0x85C1E9, "encadeia": False,
        },
        {
            "nome": "🪤 Pacto da Armadilha Dourada",
            "tipo": "armadilha_dourada",
            "recompensa_min": 6_000, "recompensa_max": 12_000,
            "descricao": "Tudo parece bom demais para ser verdade. E geralmente é.",
            "consequencia": "70% de receber tudo. 30% de não receber nada.",
            "rejeitar_custo": 200,
            "cor": 0xF0B27A, "encadeia": False,
        },
    ],

    # ── RAROS ─────────────────────────────────────────
    "raro": [
        {
            "nome": "🎲 Pacto do Dobro ou Nada",
            "tipo": "dobro_ou_nada",
            "recompensa_min": 10_000, "recompensa_max": 40_000,
            "descricao": "50% de dobrar tudo. 50% de perder tudo. O Cassino ama equilíbrio.",
            "consequencia": "Dobra o saldo ou perde tudo.",
            "rejeitar_custo": 1_000,
            "cor": 0xF39C12, "encadeia": False,
        },
        {
            "nome": "🎁 Pacto da Generosidade",
            "tipo": "bonus_puro",
            "recompensa_min": 8_000, "recompensa_max": 25_000,
            "descricao": "O Cassino está de bom humor. Uma oferta sem armadilhas — desta vez.",
            "consequencia": "Nenhuma. Só moedas.",
            "rejeitar_custo": 500,
            "cor": 0x2ECC71, "encadeia": False,
        },
        {
            "nome": "🔫 Pacto da Roleta Russa",
            "tipo": "roleta_russa_moedas",
            "recompensa_min": 20_000, "recompensa_max": 50_000,
            "descricao": "Seis câmaras. Uma bala. Desta vez, o preço é pago em moedas.",
            "consequencia": "1 em 6: perde todo o saldo. 5 em 6: recebe a recompensa.",
            "rejeitar_custo": 2_000,
            "cor": 0xE74C3C, "encadeia": False,
        },
        {
            "nome": "🧨 Pacto da Bomba-Relógio",
            "tipo": "bomba_relogio",
            "recompensa_min": 15_000, "recompensa_max": 35_000,
            "descricao": "Você recebe agora — mas o Cassino vai cobrar uma dívida aleatória depois.",
            "consequencia": "Recebe a recompensa. Entre 1h e 24h, perde entre 10% e 40% do saldo.",
            "rejeitar_custo": 1_500,
            "cor": 0xE67E22, "encadeia": False,
        },
        {
            "nome": "📈 Pacto do Especulador",
            "tipo": "especulacao",
            "recompensa_min": 10_000, "recompensa_max": 30_000,
            "descricao": "O Cassino investe suas moedas num mercado instável. Alto risco, alta recompensa.",
            "consequencia": "33% triplo. 33% recompensa normal. 33% perde 25% do saldo.",
            "rejeitar_custo": 800,
            "cor": 0x27AE60, "encadeia": False,
        },
        {
            "nome": "🤲 Pacto do Mendigo Rei",
            "tipo": "mendigo_rei",
            "recompensa_min": 12_000, "recompensa_max": 28_000,
            "descricao": "O Cassino redistribui a fortuna. Quem tem mais doa para quem tem menos.",
            "consequencia": "Recebe moedas de outro membro com saldo maior — ou doa para alguém menor.",
            "rejeitar_custo": 700,
            "cor": 0x8E44AD, "encadeia": False,
        },
        {
            "nome": "⏳ Pacto do Tempo",
            "tipo": "multiplicador_tempo",
            "recompensa_min": 5_000, "recompensa_max": 15_000,
            "descricao": "Quanto mais tempo você ficar sem receber outro pacto, mais o bônus cresce.",
            "consequencia": "Recebe a recompensa × multiplicador baseado no seu cooldown acumulado.",
            "rejeitar_custo": 600,
            "cor": 0x1ABC9C, "encadeia": False,
        },
    ],

    # ── ÉPICOS ────────────────────────────────────────
    "epico": [
        {
            "nome": "🌀 Pacto do Caos",
            "tipo": "caos",
            "recompensa_min": 30_000, "recompensa_max": 70_000,
            "descricao": "Ninguém sabe o que vai acontecer. Nem o Dealer. O Caos decide.",
            "consequencia": "Efeito completamente aleatório — pode ser ótimo ou catastrófico.",
            "rejeitar_custo": 5_000,
            "cor": 0x1ABC9C, "encadeia": True,
        },
        {
            "nome": "💎 Pacto do Cofre",
            "tipo": "cofre",
            "recompensa_min": 90_000, "recompensa_max": 180_000,
            "descricao": "O Cassino abre um cofre secreto. O conteúdo é seu — por uma taxa em moedas.",
            "consequencia": "Perde 20% do saldo atual. Ganha muito mais.",
            "rejeitar_custo": 5_000,
            "cor": 0x3498DB, "encadeia": True,
        },
        {
            "nome": "🏦 Pacto do Banqueiro",
            "tipo": "banqueiro",
            "recompensa_min": 40_000, "recompensa_max": 80_000,
            "descricao": "O Cassino empresta dinheiro a juro abusivo. Você paga ou perde o dobro.",
            "consequencia": "Recebe agora. Em 30 min devolve com 50% de juros ou perde 2× do empréstimo.",
            "rejeitar_custo": 3_000,
            "cor": 0xD4AC0D, "encadeia": True,
        },
        {
            "nome": "🔮 Pacto do Oráculo",
            "tipo": "oraculo",
            "recompensa_min": 35_000, "recompensa_max": 65_000,
            "descricao": "O Oráculo do Cassino prevê o futuro — e ele cobra caro por isso.",
            "consequencia": "Você descobre o resultado antes de confirmar. Decide com informação completa.",
            "rejeitar_custo": 4_000,
            "cor": 0x9B59B6, "encadeia": False,
        },
        {
            "nome": "🃏 Pacto do Coringa",
            "tipo": "coringa",
            "recompensa_min": 25_000, "recompensa_max": 90_000,
            "descricao": "O Coringa escolhe um número de 1 a 10. Você também. Se bater — jackpot.",
            "consequencia": "Acertou o número: recompensa ×3. Errou: recompensa normal.",
            "rejeitar_custo": 4_500,
            "cor": 0xE74C3C, "encadeia": True,
        },
        {
            "nome": "🌊 Pacto da Maré",
            "tipo": "mare",
            "recompensa_min": 20_000, "recompensa_max": 60_000,
            "descricao": "A fortuna tem ciclos. Agora a maré pode estar a seu favor — ou não.",
            "consequencia": "Depende do seu saldo atual. Rico recebe menos. Pobre recebe mais.",
            "rejeitar_custo": 3_500,
            "cor": 0x2980B9, "encadeia": False,
        },
        {
            "nome": "👥 Pacto do Sócio",
            "tipo": "socio",
            "recompensa_min": 30_000, "recompensa_max": 70_000,
            "descricao": "O Cassino aponta um parceiro. Vocês dividem lucros — e riscos.",
            "consequencia": "Você e outro membro aleatório dividem a recompensa. Mas o risco também é duplo.",
            "rejeitar_custo": 3_000,
            "cor": 0x16A085, "encadeia": True,
        },
    ],

    # ── LENDÁRIOS ─────────────────────────────────────
    "lendario": [
        {
            "nome": "💀 Pacto da Ruína",
            "tipo": "bonus_puro",
            "recompensa_min": 500_000, "recompensa_max": 1_000_000,
            "descricao": "Uma proposta rara surgiu. Poucos recebem. Menos ainda aceitam.",
            "consequencia": "Apenas moedas. Uma raridade absoluta.",
            "rejeitar_custo": 10_000,
            "cor": 0xFFD700, "encadeia": True,
        },
        {
            "nome": "👑 Pacto do Rei",
            "tipo": "rei",
            "recompensa_min": 1_000_000, "recompensa_max": 2_000_000,
            "descricao": "O Cassino oferece poder e riqueza sem igual.",
            "consequencia": "Apenas moedas. Uma raridade.",
            "rejeitar_custo": 15_000,
            "cor": 0xFFD700, "encadeia": True,
        },
        {
            "nome": "🎰 Pacto do Jackpot Absoluto",
            "tipo": "jackpot",
            "recompensa_min": 800_000, "recompensa_max": 3_000_000,
            "descricao": "O maior prêmio que o Cassino já ofereceu. Mas a máquina decide.",
            "consequencia": "Gira 3 símbolos. 3 iguais: recompensa máxima. 2 iguais: metade. 0: nada.",
            "rejeitar_custo": 20_000,
            "cor": 0xFF6B35, "encadeia": False,
        },
        {
            "nome": "⚖️ Pacto da Balança",
            "tipo": "balanca",
            "recompensa_min": 300_000, "recompensa_max": 2_000_000,
            "descricao": "O Cassino pesa sua sorte contra a de toda a guilda.",
            "consequencia": "Compara seu saldo com a média da guilda. Rico paga. Pobre ganha muito.",
            "rejeitar_custo": 12_000,
            "cor": 0xAED6F1, "encadeia": True,
        },
        {
            "nome": "🌑 Pacto da Lua Negra",
            "tipo": "lua_negra",
            "recompensa_min": 600_000, "recompensa_max": 1_500_000,
            "descricao": "Acontece uma vez. Nunca duas. O Cassino abre uma exceção.",
            "consequencia": "Recebe a recompensa. E guarda um token de proteção de saldo por 24h.",
            "rejeitar_custo": 18_000,
            "cor": 0x2C3E50, "encadeia": False,
        },
    ],
}

PESOS   = {"comum": 60, "raro": 25, "epico": 12, "lendario": 3}
EMBLEMAS = {
    "comum":    "⚪ Comum",
    "raro":     "🔵 Raro",
    "epico":    "🟣 Épico",
    "lendario": "🟡 Lendário",
}
SIMBOLOS_SLOT = ["🍒", "🍋", "🔔", "⭐", "💎", "7️⃣"]


# ──────────────────────────────────────────────────────
#  ESTADO EM MEMÓRIA
# ──────────────────────────────────────────────────────

historico:   dict[int, dict]  = {}
seguros_saldo: dict[int, float] = {}   # uid → timestamp de expiração
cooldowns:   dict[int, float] = {}
dividas:     dict[int, dict]  = {}     # uid → {valor, vence_em, tipo}
protecoes:   dict[int, float] = {}     # uid → timestamp (lua negra)


def _hist(uid: int) -> dict:
    if uid not in historico:
        historico[uid] = {
            "aceitos": 0, "recusados": 0,
            "moedas_ganhas": 0, "lendarios": 0,
            "ultimo_pacto": 0.0,
        }
    return historico[uid]


def registrar(uid: int, raridade: str, resultado: str, moedas: int) -> None:
    h = _hist(uid)
    if resultado == "aceito":
        h["aceitos"]      += 1
        h["moedas_ganhas"] += moedas
        if raridade == "lendario":
            h["lendarios"] += 1
    else:
        h["recusados"] += 1
    h["ultimo_pacto"] = _now()


def _now() -> float:
    return datetime.now(timezone.utc).timestamp()


def em_cooldown(uid: int) -> bool:
    return _now() < cooldowns.get(uid, 0)


def set_cooldown(uid: int) -> None:
    cooldowns[uid] = _now() + COOLDOWN_AUTO


def saldo_protegido(uid: int) -> bool:
    return _now() < protecoes.get(uid, 0)


def sortear(raridade: str | None = None) -> tuple[dict, str]:
    if not raridade:
        raridade = random.choices(list(PESOS), weights=list(PESOS.values()), k=1)[0]
    p = random.choice(PACTOS[raridade]).copy()
    p["recompensa"] = random.randint(p["recompensa_min"], p["recompensa_max"])
    return p, raridade


# ──────────────────────────────────────────────────────
#  EXECUTORES DE TIPO
# ──────────────────────────────────────────────────────

async def executar_tipo(
    membro: discord.Member, pacto: dict
) -> tuple[str, int]:
    tipo       = pacto.get("tipo", "bonus_puro")
    recompensa = pacto["recompensa"]

    # ── BONUS PURO / REI / RUÍNA ─────────────────────
    if tipo in ("bonus_puro", "rei"):
        adicionar_moedas(membro.id, recompensa)
        linhas = {
            "bonus_puro": f"🎁 **O Cassino foi generoso.**\n\n🪙 **+{recompensa:,} Moedas do Diabo**\n\n> *Nem sempre há um preço.*",
            "rei":        f"👑 **O Cassino coroou você.**\n\n🪙 **+{recompensa:,} Moedas do Diabo**\n\n> *Poder real não precisa de sacrifícios.*",
        }
        return linhas[tipo], recompensa

    # ── PERDA SIMPLES (10%) ───────────────────────────
    elif tipo == "moedas_perda_simples":
        saldo = get_moedas(membro.id)
        perda = int(saldo * 0.10)
        remover_moedas(membro.id, perda)
        adicionar_moedas(membro.id, recompensa)
        liquido = recompensa - perda
        return (
            f"🌫️ **Troca registrada.**\n\n"
            f"🪙 **+{recompensa:,}** recebidas\n"
            f"📉 **-{perda:,}** cobradas (10% do saldo)\n\n"
            f"💰 Líquido: **{'+'if liquido>=0 else ''}{liquido:,}**",
            max(liquido, 0),
        )

    # ── APOSTA SIMPLES ────────────────────────────────
    elif tipo == "aposta_simples":
        if random.random() < 0.5:
            adicionar_moedas(membro.id, recompensa)
            return (
                f"🎯 **Você ganhou a aposta!**\n\n"
                f"🪙 **+{recompensa:,} Moedas do Diabo**\n\n> *O Cassino perdeu desta vez.*",
                recompensa,
            )
        else:
            perda = recompensa // 2
            saldo = get_moedas(membro.id)
            remover_moedas(membro.id, min(perda, saldo))
            return (
                f"🎯 **A casa ganhou.**\n\n"
                f"🪙 **-{min(perda, saldo):,} Moedas do Diabo**\n\n> *Tente novamente... se tiver coragem.*",
                0,
            )

    # ── DRENAGEM LENTA ────────────────────────────────
    elif tipo == "drenagem_lenta":
        adicionar_moedas(membro.id, recompensa)
        # Registra dívida de 5 dias
        dividas[membro.id] = {
            "tipo": "drenagem",
            "dias_restantes": 5,
            "percentual": 0.05,
            "vence_em": _now() + 86_400,
        }
        return (
            f"💧 **Contrato assinado.**\n\n"
            f"🪙 **+{recompensa:,} Moedas do Diabo** recebidas agora.\n\n"
            f"⚠️ O Cassino cobrará **5% do seu saldo** diariamente por **5 dias**.\n\n"
            f"> *A água corrói a pedra aos poucos.*",
            recompensa,
        )

    # ── ARMADILHA DOURADA ─────────────────────────────
    elif tipo == "armadilha_dourada":
        if random.random() < 0.70:
            adicionar_moedas(membro.id, recompensa)
            return (
                f"🪤 **A armadilha não disparou — desta vez.**\n\n"
                f"🪙 **+{recompensa:,} Moedas do Diabo**\n\n> *Sorte ou habilidade? Você decide.*",
                recompensa,
            )
        return (
            f"🪤 **A armadilha disparou.**\n\n"
            f"🚫 Você não recebe nada.\n\n> *O ouro era falso.*",
            0,
        )

    # ── DOBRO OU NADA ─────────────────────────────────
    elif tipo == "dobro_ou_nada":
        saldo = get_moedas(membro.id)
        if random.random() < 0.5:
            adicionar_moedas(membro.id, saldo)
            return (
                f"🎲 **A sorte sorriu!**\n\n"
                f"Suas moedas foram **dobradas**.\n🪙 **+{saldo:,}**",
                saldo,
            )
        remover_moedas(membro.id, saldo)
        return (
            f"💀 **A casa ganhou.**\n\nVocê perdeu **tudo**.\n🪙 **-{saldo:,}**",
            0,
        )

    # ── ROLETA RUSSA (moedas) ─────────────────────────
    elif tipo == "roleta_russa_moedas":
        if random.randint(1, 6) == 1:
            saldo = get_moedas(membro.id)
            if not saldo_protegido(membro.id):
                remover_moedas(membro.id, saldo)
                return (
                    f"🔫 **BANG! A câmara tinha bala.**\n\n"
                    f"Você perdeu todo o seu saldo.\n🪙 **-{saldo:,}**",
                    0,
                )
            return (
                f"🔫 **BANG! Mas você estava protegido.**\n\n"
                f"🌑 Seu escudo da Lua Negra absorveu o impacto.\n\n> *Desta vez.*",
                0,
            )
        adicionar_moedas(membro.id, recompensa)
        return (
            f"🎲 **Câmara vazia. Você sobreviveu.**\n\n"
            f"🪙 **+{recompensa:,} Moedas do Diabo**",
            recompensa,
        )

    # ── BOMBA-RELÓGIO ─────────────────────────────────
    elif tipo == "bomba_relogio":
        adicionar_moedas(membro.id, recompensa)
        atraso   = random.randint(3_600, 86_400)
        pct      = random.uniform(0.10, 0.40)
        dividas[membro.id] = {
            "tipo": "bomba",
            "percentual": pct,
            "vence_em": _now() + atraso,
        }
        import math
        h = math.floor(atraso / 3_600)
        m = math.floor((atraso % 3_600) / 60)
        return (
            f"🧨 **Você recebeu o dinheiro.**\n\n"
            f"🪙 **+{recompensa:,} Moedas do Diabo**\n\n"
            f"⚠️ Mas em **{h}h {m}min**, o Cassino cobrará "
            f"**{pct*100:.0f}% do seu saldo de volta**.\n\n"
            f"> *O relógio está correndo.*",
            recompensa,
        )

    # ── ESPECULAÇÃO ───────────────────────────────────
    elif tipo == "especulacao":
        roll = random.random()
        if roll < 0.33:
            ganho = recompensa * 3
            adicionar_moedas(membro.id, ganho)
            return (
                f"📈 **Mercado em alta! Investimento triplicou!**\n\n"
                f"🪙 **+{ganho:,} Moedas do Diabo**\n\n> *O risco valeu a pena.*",
                ganho,
            )
        elif roll < 0.66:
            adicionar_moedas(membro.id, recompensa)
            return (
                f"📊 **Mercado estável. Retorno normal.**\n\n"
                f"🪙 **+{recompensa:,} Moedas do Diabo**",
                recompensa,
            )
        else:
            saldo = get_moedas(membro.id)
            perda = int(saldo * 0.25)
            remover_moedas(membro.id, perda)
            return (
                f"📉 **Mercado despencou!**\n\n"
                f"🪙 **-{perda:,}** (25% do saldo perdido)\n\n> *Especulação tem preço.*",
                0,
            )

    # ── MENDIGO REI ───────────────────────────────────
    elif tipo == "mendigo_rei":
        saldo_proprio = get_moedas(membro.id)
        membros_validos = [
            m for m in membro.guild.members
            if not m.bot and m.id != membro.id
        ]
        random.shuffle(membros_validos)
        rico = None; pobre = None
        for m in membros_validos:
            s = get_moedas(m.id)
            if s > saldo_proprio and rico is None:
                rico = (m, s)
            elif s < saldo_proprio and pobre is None:
                pobre = (m, s)
            if rico and pobre:
                break

        if rico:
            transferencia = int(rico[1] * random.uniform(0.05, 0.15))
            remover_moedas(rico[0].id, transferencia)
            adicionar_moedas(membro.id, transferencia)
            try:
                av = discord.Embed(
                    title="🤲 Redistribuição de Riqueza",
                    description=(
                        f"O Cassino retirou **{transferencia:,} moedas** do seu saldo "
                        f"e transferiu para **{membro.display_name}**.\n\n"
                        f"> *A riqueza circula.*"
                    ),
                    color=0x8E44AD,
                )
                await rico[0].send(embed=av)
            except discord.Forbidden:
                pass
            return (
                f"🤲 **Riqueza redistribuída!**\n\n"
                f"🎯 Doador: **{rico[0].display_name}**\n"
                f"🪙 **+{transferencia:,} Moedas** transferidas para você.\n\n"
                f"> *A balança da fortuna inclinou-se a seu favor.*",
                transferencia,
            )
        # fallback: bônus direto
        adicionar_moedas(membro.id, recompensa)
        return (
            f"🤲 **O Cassino não encontrou alguém mais rico.**\n\n"
            f"🪙 **+{recompensa:,}** como compensação.",
            recompensa,
        )

    # ── MULTIPLICADOR DE TEMPO ────────────────────────
    elif tipo == "multiplicador_tempo":
        ultimo = _hist(membro.id).get("ultimo_pacto", 0)
        espera = max(0, _now() - ultimo)
        # Cada hora extra = +10% (máx 5×)
        mult = min(5.0, 1.0 + (espera / 3_600) * 0.1)
        ganho = int(recompensa * mult)
        adicionar_moedas(membro.id, ganho)
        return (
            f"⏳ **Paciência recompensada!**\n\n"
            f"🔢 Multiplicador: **{mult:.1f}×**\n"
            f"🪙 **+{ganho:,} Moedas do Diabo**\n\n"
            f"> *Quem espera, ganha mais.*",
            ganho,
        )

    # ── CAOS ──────────────────────────────────────────
    elif tipo == "caos":
        efeitos = [
            "mega_bonus", "perda_pesada", "dobro_saldo",
            "tributacao", "roubo_alvo", "chuva_moedas", "inversao_sorte",
        ]
        efeito = random.choice(efeitos)

        if efeito == "mega_bonus":
            b = random.randint(20_000, 80_000)
            adicionar_moedas(membro.id, b)
            return f"🌀 **O Caos foi absurdamente gentil.**\n\n🪙 **+{b:,}**", b

        elif efeito == "perda_pesada":
            saldo = get_moedas(membro.id)
            p = int(saldo * random.uniform(0.15, 0.35))
            remover_moedas(membro.id, p)
            return f"🌀 **O Caos cobrou seu preço.**\n\n🪙 **-{p:,}**", 0

        elif efeito == "dobro_saldo":
            saldo = get_moedas(membro.id)
            adicionar_moedas(membro.id, saldo)
            return f"🌀 **O Caos dobrou tudo!**\n\n🪙 **+{saldo:,}**", saldo

        elif efeito == "tributacao":
            saldo = get_moedas(membro.id)
            t = int(saldo * 0.05)
            remover_moedas(membro.id, t)
            b = random.randint(15_000, 50_000)
            adicionar_moedas(membro.id, b)
            return (
                f"🌀 **O Caos tributou e compensou.**\n\n"
                f"📉 **-{t:,}** (5% de imposto)\n"
                f"🪙 **+{b:,}** de bônus\n\n"
                f"💰 Líquido: **+{b-t:,}**",
                max(b - t, 0),
            )

        elif efeito == "roubo_alvo":
            alvos = [
                m for m in membro.guild.members
                if not m.bot and m.id != membro.id and get_moedas(m.id) > 0
            ]
            if alvos:
                alvo = random.choice(alvos)
                r    = int(get_moedas(alvo.id) * random.uniform(0.05, 0.20))
                remover_moedas(alvo.id, r)
                adicionar_moedas(membro.id, r)
                return (
                    f"🌀 **O Caos roubou para você.**\n\n"
                    f"🎯 Alvo: **{alvo.display_name}**\n🪙 **+{r:,}**",
                    r,
                )
            adicionar_moedas(membro.id, recompensa)
            return f"🌀 **Sem alvos. O Caos compensou.**\n\n🪙 **+{recompensa:,}**", recompensa

        elif efeito == "chuva_moedas":
            chuva = random.randint(5_000, 40_000)
            adicionar_moedas(membro.id, chuva)
            return (
                f"🌀 **O Caos faz chover!**\n\n"
                f"🪙 **+{chuva:,} Moedas** caíram do céu.",
                chuva,
            )

        elif efeito == "inversao_sorte":
            saldo = get_moedas(membro.id)
            media_guild = sum(
                get_moedas(m.id)
                for m in membro.guild.members if not m.bot
            ) // max(1, len([m for m in membro.guild.members if not m.bot]))
            if saldo > media_guild:
                diferenca = int((saldo - media_guild) * 0.1)
                remover_moedas(membro.id, diferenca)
                return (
                    f"🌀 **O Caos nivelou o campo.**\n\n"
                    f"📉 Você estava acima da média. **-{diferenca:,}** redistribuídas.",
                    0,
                )
            bonus = int((media_guild - saldo) * 0.5)
            adicionar_moedas(membro.id, bonus)
            return (
                f"🌀 **O Caos compensou sua desvantagem.**\n\n"
                f"🪙 **+{bonus:,}** para equilibrar o jogo.",
                bonus,
            )

        return "🌀 **O Caos não fez nada desta vez.**\n\n> *Ou fez? Ninguém sabe.*", 0

    # ── COFRE ────────────────────────────────────────
    elif tipo == "cofre":
        saldo = get_moedas(membro.id)
        taxa  = int(saldo * 0.20)
        remover_moedas(membro.id, taxa)
        adicionar_moedas(membro.id, recompensa)
        return (
            f"💎 **Cofre aberto!**\n\n"
            f"🪙 **+{recompensa:,} Moedas do Diabo**\n"
            f"📉 Taxa: **-{taxa:,}** (20% do saldo)\n\n"
            f"> *O Cassino cobra pelo acesso. Sempre.*",
            recompensa,
        )

    # ── BANQUEIRO ────────────────────────────────────
    elif tipo == "banqueiro":
        adicionar_moedas(membro.id, recompensa)
        juros    = int(recompensa * 0.50)
        divida   = recompensa + juros
        dividas[membro.id] = {
            "tipo": "banqueiro",
            "valor": divida,
            "vence_em": _now() + 1_800,  # 30 min
        }
        return (
            f"🏦 **Empréstimo liberado!**\n\n"
            f"🪙 **+{recompensa:,}** agora\n\n"
            f"⚠️ Em **30 minutos**, o Cassino cobrará **{divida:,}** (principal + 50% de juros).\n"
            f"Se não puder pagar, perderá o dobro do empréstimo.\n\n"
            f"> *O Cassino é o credor mais implacável que existe.*",
            recompensa,
        )

    # ── ORÁCULO ──────────────────────────────────────
    elif tipo == "oraculo":
        # Pré-calcula resultado e mostra antes
        vai_ganhar = random.random() < 0.60
        if vai_ganhar:
            adicionar_moedas(membro.id, recompensa)
            return (
                f"🔮 **O Oráculo viu um futuro favorável — e ele estava certo.**\n\n"
                f"🪙 **+{recompensa:,} Moedas do Diabo**\n\n"
                f"> *Conhecimento é poder.*",
                recompensa,
            )
        saldo = get_moedas(membro.id)
        perda = int(saldo * 0.10)
        remover_moedas(membro.id, perda)
        return (
            f"🔮 **O Oráculo viu escuridão — e ele estava certo.**\n\n"
            f"🪙 **-{perda:,}** (10% do saldo)\n\n"
            f"> *Às vezes é melhor não saber.*",
            0,
        )

    # ── CORINGA ───────────────────────────────────────
    elif tipo == "coringa":
        num_cassino = random.randint(1, 10)
        num_usuario = random.randint(1, 10)  # simula escolha do usuário
        if num_cassino == num_usuario:
            jackpot = recompensa * 3
            adicionar_moedas(membro.id, jackpot)
            return (
                f"🃏 **JACKPOT! O Coringa errou — você acertou!**\n\n"
                f"🔢 Número: **{num_cassino}** vs **{num_usuario}**\n"
                f"🪙 **+{jackpot:,} Moedas do Diabo** (×3!)\n\n"
                f"> *Impossível. E ainda assim.*",
                jackpot,
            )
        adicionar_moedas(membro.id, recompensa)
        return (
            f"🃏 **O Coringa apontou diferente.**\n\n"
            f"🔢 Cassino: **{num_cassino}** | Você: **{num_usuario}**\n"
            f"🪙 **+{recompensa:,}** mesmo assim.\n\n"
            f"> *A sorte tem limites. O Coringa, não.*",
            recompensa,
        )

    # ── MARÉ ──────────────────────────────────────────
    elif tipo == "mare":
        saldo = get_moedas(membro.id)
        membros_com_saldo = [
            get_moedas(m.id)
            for m in membro.guild.members if not m.bot
        ]
        media = sum(membros_com_saldo) // max(1, len(membros_com_saldo))

        if saldo > media * 1.5:
            # Rico → recebe menos
            ganho = int(recompensa * 0.5)
            adicionar_moedas(membro.id, ganho)
            return (
                f"🌊 **Maré baixa para quem tem muito.**\n\n"
                f"Você está acima da média. A maré trabalha contra os ricos.\n"
                f"🪙 **+{ganho:,}** (50% da recompensa)\n\n"
                f"> *Fortuna tem seus próprios ciclos.*",
                ganho,
            )
        elif saldo < media * 0.5:
            # Pobre → recebe muito mais
            ganho = int(recompensa * 2.5)
            adicionar_moedas(membro.id, ganho)
            return (
                f"🌊 **Maré alta para quem tem pouco!**\n\n"
                f"A maré favore os humildes. Você recebe o dobro.\n"
                f"🪙 **+{ganho:,}** (250% da recompensa)\n\n"
                f"> *O oceano equilibra tudo eventualmente.*",
                ganho,
            )
        # Normal
        adicionar_moedas(membro.id, recompensa)
        return (
            f"🌊 **Maré neutra.**\n\n"
            f"Você está próximo da média da guilda.\n"
            f"🪙 **+{recompensa:,}**",
            recompensa,
        )

    # ── SÓCIO ─────────────────────────────────────────
    elif tipo == "socio":
        alvos = [
            m for m in membro.guild.members
            if not m.bot and m.id != membro.id
        ]
        if alvos:
            socio  = random.choice(alvos)
            metade = recompensa // 2
            sucesso = random.random() < 0.55
            if sucesso:
                adicionar_moedas(membro.id, metade)
                adicionar_moedas(socio.id, metade)
                try:
                    av = discord.Embed(
                        title="👥 Você ganhou como sócio!",
                        description=(
                            f"**{membro.display_name}** assinou um **Pacto do Sócio** e indicou você.\n\n"
                            f"🪙 **+{metade:,} Moedas do Diabo** caíram na sua conta.\n\n"
                            f"> *O Cassino distribui. Aproveite.*"
                        ),
                        color=0x16A085,
                    )
                    await socio.send(embed=av)
                except discord.Forbidden:
                    pass
                return (
                    f"👥 **Parceria fechada!**\n\n"
                    f"🤝 Sócio: **{socio.display_name}**\n"
                    f"🪙 Cada um recebe **+{metade:,}**\n\n"
                    f"> *Dividir é multiplicar.*",
                    metade,
                )
            # Deu errado — perdem juntos
            saldo_proprio = get_moedas(membro.id)
            saldo_socio   = get_moedas(socio.id)
            perda_p = int(saldo_proprio * 0.05)
            perda_s = int(saldo_socio   * 0.05)
            remover_moedas(membro.id,  perda_p)
            remover_moedas(socio.id,   perda_s)
            return (
                f"👥 **A parceria falhou.**\n\n"
                f"🤝 Sócio: **{socio.display_name}**\n"
                f"📉 Ambos perderam **5% do saldo**.\n\n"
                f"> *Risco compartilhado, prejuízo também.*",
                0,
            )
        adicionar_moedas(membro.id, recompensa)
        return f"👥 **Nenhum sócio encontrado. Bônus direto.**\n\n🪙 **+{recompensa:,}**", recompensa

    # ── JACKPOT (SLOT MACHINE) ────────────────────────
    elif tipo == "jackpot":
        rolos = [random.choice(SIMBOLOS_SLOT) for _ in range(3)]
        display = " | ".join(rolos)
        iguais = len(set(rolos))
        if iguais == 1:
            ganho = pacto["recompensa_max"]
            adicionar_moedas(membro.id, ganho)
            return (
                f"🎰 **[ {display} ] — JACKPOT ABSOLUTO!**\n\n"
                f"🪙 **+{ganho:,} Moedas do Diabo** — recompensa máxima!\n\n"
                f"> *O Cassino perdeu hoje. Aproveite enquanto pode.*",
                ganho,
            )
        elif iguais == 2:
            ganho = recompensa // 2
            adicionar_moedas(membro.id, ganho)
            return (
                f"🎰 **[ {display} ] — Dois iguais!**\n\n"
                f"🪙 **+{ganho:,}** (metade da recompensa)\n\n"
                f"> *Quase lá.*",
                ganho,
            )
        return (
            f"🎰 **[ {display} ] — Sem combinação.**\n\n"
            f"🚫 Você não recebe nada desta vez.\n\n"
            f"> *A máquina sempre vence.*",
            0,
        )

    # ── BALANÇA ──────────────────────────────────────
    elif tipo == "balanca":
        saldo   = get_moedas(membro.id)
        salarios = [get_moedas(m.id) for m in membro.guild.members if not m.bot]
        media   = sum(salarios) // max(1, len(salarios))
        if saldo > media * 2:
            taxa = int(saldo * 0.15)
            remover_moedas(membro.id, taxa)
            adicionar_moedas(membro.id, recompensa // 2)
            return (
                f"⚖️ **Você é o mais rico. A balança pesa contra.**\n\n"
                f"📉 **-{taxa:,}** (15% do saldo)\n"
                f"🪙 **+{recompensa//2:,}** de compensação parcial\n\n"
                f"> *Noblesse oblige.*",
                max((recompensa // 2) - taxa, 0),
            )
        multiplicador = max(1.0, (media / max(saldo, 1)) * 0.5)
        ganho = min(int(recompensa * multiplicador), pacto["recompensa_max"] * 3)
        adicionar_moedas(membro.id, ganho)
        return (
            f"⚖️ **A balança favorece os humildes.**\n\n"
            f"🔢 Multiplicador: **{multiplicador:.1f}×**\n"
            f"🪙 **+{ganho:,} Moedas do Diabo**\n\n"
            f"> *O Cassino às vezes tem coração.*",
            ganho,
        )

    # ── LUA NEGRA ────────────────────────────────────
    elif tipo == "lua_negra":
        adicionar_moedas(membro.id, recompensa)
        protecoes[membro.id] = _now() + 86_400  # 24h
        return (
            f"🌑 **A Lua Negra brilhou para você.**\n\n"
            f"🪙 **+{recompensa:,} Moedas do Diabo**\n\n"
            f"🛡️ **Escudo ativo por 24 horas:**\n"
            f"Qualquer pacto que removeria todo seu saldo será bloqueado.\n\n"
            f"> *Acontece uma vez. Nunca duas.*",
            recompensa,
        )

    # ── FALLBACK ──────────────────────────────────────
    adicionar_moedas(membro.id, recompensa)
    return f"🪙 **+{recompensa:,} Moedas do Diabo**", recompensa


# ──────────────────────────────────────────────────────
#  TASK DE DÍVIDAS (roda em background)
# ──────────────────────────────────────────────────────

async def verificar_dividas(bot: commands.Bot) -> None:
    """Loop que processa dívidas ativas (bomba, banqueiro, drenagem)."""
    while True:
        await asyncio.sleep(60)
        agora = _now()
        for uid, d in list(dividas.items()):
            if agora < d.get("vence_em", float("inf")):
                continue

            tipo = d.get("tipo")

            if tipo == "bomba":
                saldo = get_moedas(uid)
                perda = int(saldo * d["percentual"])
                remover_moedas(uid, perda)
                del dividas[uid]
                log.info("Bomba-relógio detonada: uid=%d perda=%d", uid, perda)
                # Tenta notificar por DM
                for guild in bot.guilds:
                    membro = guild.get_member(uid)
                    if membro:
                        try:
                            await membro.send(
                                embed=discord.Embed(
                                    title="🧨 A Bomba Detonou!",
                                    description=(
                                        f"O prazo do **Pacto da Bomba-Relógio** chegou.\n\n"
                                        f"🪙 **-{perda:,} Moedas** cobradas automaticamente.\n\n"
                                        f"> *O Cassino sempre recebe o que é seu.*"
                                    ),
                                    color=0xE67E22,
                                )
                            )
                        except discord.Forbidden:
                            pass
                        break

            elif tipo == "banqueiro":
                saldo = get_moedas(uid)
                valor = d["valor"]
                if saldo >= valor:
                    remover_moedas(uid, valor)
                    msg = f"🏦 Dívida de **{valor:,}** quitada automaticamente."
                else:
                    penalidade = d.get("valor", 0) * 2
                    remover_moedas(uid, saldo)  # Zera saldo como penalidade máxima
                    msg = (
                        f"🏦 Você não tinha moedas suficientes.\n"
                        f"O Cassino tomou **tudo** como penalidade."
                    )
                del dividas[uid]
                for guild in bot.guilds:
                    membro = guild.get_member(uid)
                    if membro:
                        try:
                            await membro.send(
                                embed=discord.Embed(
                                    title="🏦 Cobrança do Banqueiro",
                                    description=msg,
                                    color=0xD4AC0D,
                                )
                            )
                        except discord.Forbidden:
                            pass
                        break

            elif tipo == "drenagem":
                saldo = get_moedas(uid)
                perda = int(saldo * d["percentual"])
                remover_moedas(uid, perda)
                d["dias_restantes"] -= 1
                if d["dias_restantes"] <= 0:
                    del dividas[uid]
                else:
                    d["vence_em"] = agora + 86_400
                log.info(
                    "Drenagem: uid=%d perda=%d dias_restantes=%d",
                    uid, perda, d.get("dias_restantes", 0),
                )


# ──────────────────────────────────────────────────────
#  VIEWS
# ──────────────────────────────────────────────────────

class PactoView(discord.ui.View):
    def __init__(
        self,
        membro: discord.Member,
        pacto: dict,
        raridade: str,
        cog: "Pactos",
    ):
        super().__init__(timeout=TIMEOUT_PACTO)
        self.membro     = membro
        self.pacto      = pacto
        self.raridade   = raridade
        self.cog        = cog
        self.respondido = False
        self.message: discord.Message | None = None

    async def on_timeout(self) -> None:
        if self.respondido:
            return
        for item in self.children:
            item.disabled = True
        embed = discord.Embed(
            title="⏳ PACTO EXPIRADO",
            description=(
                f"### {self.pacto['nome']}\n-# {EMBLEMAS[self.raridade]}\n\n"
                "O tempo acabou. O Cassino retirou a oferta.\n\n"
                "> *Quem hesita, perde.*"
            ),
            color=0x555555,
        )
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Expirado")
        embed.timestamp = discord.utils.utcnow()
        try:
            await self.message.edit(embed=embed, view=self)
        except Exception:
            pass

    @discord.ui.button(label="Assinar o Pacto", emoji="☠️", style=discord.ButtonStyle.danger)
    async def aceitar(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if interaction.user.id != self.membro.id:
            return await interaction.response.send_message(
                "❌ Este pacto não pertence a você.", ephemeral=True
            )
        if self.respondido:
            return await interaction.response.send_message(
                "⚠️ Este pacto já foi decidido.", ephemeral=True
            )
        self.respondido = True

        desc, moedas = await executar_tipo(self.membro, self.pacto)
        registrar(self.membro.id, self.raridade, "aceito", moedas)

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="☠️ PACTO ASSINADO",
            description=(
                f"### {self.pacto['nome']}\n-# {EMBLEMAS[self.raridade]}\n\n"
                f"{desc}\n\n{SEPARADOR}> *A casa sempre cobra.*"
            ),
            color=self.pacto["cor"],
        )
        embed.set_thumbnail(url=self.membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Proibido")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.edit_message(embed=embed, view=self)

        await self.cog.enviar_log(self.membro, self.pacto, self.raridade, "aceito", moedas)
        if self.raridade == "lendario":
            await self.cog.anuncio_publico(self.membro, self.pacto)
        if self.pacto.get("encadeia"):
            await asyncio.sleep(6)
            await self.cog.enviar_pacto_encadeado(self.membro)

    @discord.ui.button(label="Recusar", emoji="❌", style=discord.ButtonStyle.secondary)
    async def recusar(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if interaction.user.id != self.membro.id:
            return await interaction.response.send_message(
                "❌ Este pacto não pertence a você.", ephemeral=True
            )
        if self.respondido:
            return await interaction.response.send_message(
                "⚠️ Este pacto já foi decidido.", ephemeral=True
            )
        self.respondido = True

        custo  = self.pacto.get("rejeitar_custo", 0)
        saldo  = get_moedas(self.membro.id)
        cobrado = min(custo, saldo)
        if cobrado > 0:
            remover_moedas(self.membro.id, cobrado)

        registrar(self.membro.id, self.raridade, "recusado", 0)

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="📜 PACTO RECUSADO",
            description=(
                f"### {self.pacto['nome']}\n-# {EMBLEMAS[self.raridade]}\n\n"
                "Você recusou a proposta do Cassino.\n\n"
                + (f"💸 O Cassino cobrou **{cobrado:,} Moedas** pela recusa.\n\n" if cobrado else "")
                + f"{SEPARADOR}> *Talvez ele não ofereça novamente.*"
            ),
            color=0x2C2C2C,
        )
        embed.set_thumbnail(url=self.membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Proibido")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.edit_message(embed=embed, view=self)
        await self.cog.enviar_log(self.membro, self.pacto, self.raridade, "recusado", 0)


class PactoColetivoView(discord.ui.View):
    def __init__(self, pacto: dict, raridade: str, cog: "Pactos"):
        super().__init__(timeout=TIMEOUT_PACTO)
        self.pacto       = pacto
        self.raridade    = raridade
        self.cog         = cog
        self.reivindicado = False

    @discord.ui.button(label="Reivindicar", emoji="🤝", style=discord.ButtonStyle.success)
    async def reivindicar(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if self.reivindicado:
            return await interaction.response.send_message(
                "❌ Este pacto já foi reivindicado!", ephemeral=True
            )
        self.reivindicado = True
        membro = interaction.guild.get_member(interaction.user.id)
        desc, moedas = await executar_tipo(membro, self.pacto)
        registrar(membro.id, self.raridade, "aceito", moedas)

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="🤝 PACTO REIVINDICADO",
            description=(
                f"### {self.pacto['nome']}\n-# {EMBLEMAS[self.raridade]}\n\n"
                f"{membro.mention} assinou o pacto coletivo!\n\n"
                f"{desc}\n\n{SEPARADOR}> *A casa sempre encontra seu dono.*"
            ),
            color=self.pacto["cor"],
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Coletivo")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.edit_message(embed=embed, view=self)


# ──────────────────────────────────────────────────────
#  COG PRINCIPAL
# ──────────────────────────────────────────────────────

class Pactos(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._task_dividas = bot.loop.create_task(
            verificar_dividas(bot), name="dividas_loop"
        )

    def cog_unload(self) -> None:
        self._task_dividas.cancel()

    # ── Helpers de embed ──────────────────────────────

    def _embed_pacto(
        self, membro: discord.Member, pacto: dict, raridade: str
    ) -> discord.Embed:
        ts = int(discord.utils.utcnow().timestamp() + TIMEOUT_PACTO)
        embed = discord.Embed(
            title="☠️ UMA CARTA NEGRA APARECEU",
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
            color=pacto["cor"],
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Proibido")
        embed.timestamp = discord.utils.utcnow()
        return embed

    # ── Envio de pactos ───────────────────────────────

    async def enviar_pacto_dm(
        self, membro: discord.Member, raridade: str | None = None
    ) -> None:
        pacto, raridade = sortear(raridade)
        view = PactoView(membro, pacto, raridade, self)
        msg  = await membro.send(
            embed=self._embed_pacto(membro, pacto, raridade), view=view
        )
        view.message = msg

    async def enviar_pacto_encadeado(self, membro: discord.Member) -> None:
        pacto, raridade = sortear(random.choice(["epico", "lendario"]))
        ts = int(discord.utils.utcnow().timestamp() + TIMEOUT_PACTO)
        embed = discord.Embed(
            title="🔗 PACTO ENCADEADO DESBLOQUEADO",
            description=(
                f"### {pacto['nome']}\n-# {EMBLEMAS[raridade]}\n\n"
                "Sua ousadia chamou a atenção do Cassino. Uma segunda proposta.\n\n"
                f"{SEPARADOR}"
                f"📜 **Descrição**\n{pacto['descricao']}\n\n"
                f"🪙 **Recompensa**\n**{pacto['recompensa']:,} Moedas do Diabo**\n\n"
                f"🎭 **Consequência**\n{pacto['consequencia']}\n\n"
                f"{SEPARADOR}⏳ Expira <t:{ts}:R>\n\n"
                "> *O Cassino raramente oferece duas vezes.*"
            ),
            color=pacto["cor"],
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Encadeado")
        embed.timestamp = discord.utils.utcnow()
        view = PactoView(membro, pacto, raridade, self)
        msg  = await membro.send(embed=embed, view=view)
        view.message = msg

    async def enviar_log(
        self,
        membro: discord.Member,
        pacto: dict,
        raridade: str,
        resultado: str,
        moedas: int,
    ) -> None:
        if not ID_CANAL_LOG:
            return
        canal = membro.guild.get_channel(ID_CANAL_LOG)
        if not canal:
            return
        cor = 0x2ECC71 if resultado == "aceito" else 0xE74C3C
        embed = discord.Embed(
            title=f"{'✅' if resultado == 'aceito' else '❌'} Log — {EMBLEMAS[raridade]}",
            color=cor,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="👤 Membro",    value=membro.mention,          inline=True)
        embed.add_field(name="📜 Pacto",     value=pacto["nome"],           inline=True)
        embed.add_field(name="🎯 Resultado", value=resultado.capitalize(),  inline=True)
        if resultado == "aceito":
            embed.add_field(name="🪙 Moedas", value=f"{moedas:,}", inline=True)
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_footer(text="Cassino do Diabo  •  Sistema de Pactos")
        await canal.send(embed=embed)

    async def anuncio_publico(
        self, membro: discord.Member, pacto: dict
    ) -> None:
        if not ID_CANAL_PUBLICO:
            return
        canal = membro.guild.get_channel(ID_CANAL_PUBLICO)
        if not canal:
            return
        embed = discord.Embed(
            title="🟡 PACTO LENDÁRIO ACEITO",
            description=(
                f"{membro.mention} assinou um **Pacto Lendário**!\n\n"
                f"### {pacto['nome']}\n\n"
                "> *Poucos chegam até aqui. Menos ainda sobrevivem.*"
            ),
            color=0xFFD700,
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Lendário")
        embed.timestamp = discord.utils.utcnow()
        await canal.send(embed=embed)

    # ── Comandos ──────────────────────────────────────

    @commands.command(name="pacto")
    @commands.has_permissions(administrator=True)
    async def cmd_pacto(
        self, ctx: commands.Context,
        membro: discord.Member,
        raridade: str | None = None,
    ) -> None:
        try:
            await ctx.message.delete()
        except Exception:
            pass
        if membro.bot:
            return await ctx.send("❌ Bots não recebem pactos.", delete_after=8)
        if raridade and raridade not in PACTOS:
            return await ctx.send(
                "❌ Raridade inválida. Use: `comum` `raro` `epico` `lendario`",
                delete_after=8,
            )
        try:
            await self.enviar_pacto_dm(membro, raridade)
            await ctx.send(
                random.choice([
                    "☠️ O Dealer entregou uma carta negra.",
                    "🎰 Um novo contrato foi enviado.",
                    "👁️ O Cassino escolheu um novo alvo.",
                    "📜 Um pacto proibido encontrou seu destino.",
                    "💀 Nem todos recusam a oferta.",
                ]),
                delete_after=8,
            )
        except discord.Forbidden:
            await ctx.send("❌ O membro está com a DM fechada.", delete_after=8)

    @commands.command(name="pactos")
    @commands.has_permissions(administrator=True)
    async def cmd_pactos(self, ctx: commands.Context) -> None:
        try:
            await ctx.message.delete()
        except Exception:
            pass
        validos    = [m for m in ctx.guild.members if not m.bot]
        escolhidos = random.sample(validos, min(random.randint(3, 7), len(validos)))
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
                f"☠️ Cartas negras enviadas para **{enviados}** membro(s).",
                f"🎰 **{enviados}** contratos espalhados.",
                f"👁️ O Cassino escolheu **{enviados}** alvo(s).",
            ]),
            delete_after=10,
        )

    @commands.command(name="pacto_coletivo")
    @commands.has_permissions(administrator=True)
    async def cmd_pacto_coletivo(
        self, ctx: commands.Context, raridade: str | None = None
    ) -> None:
        try:
            await ctx.message.delete()
        except Exception:
            pass
        if raridade and raridade not in PACTOS:
            return await ctx.send("❌ Raridade inválida.", delete_after=8)
        pacto, raridade = sortear(raridade)
        embed = discord.Embed(
            title="🤝 PACTO COLETIVO APARECEU",
            description=(
                f"### {pacto['nome']}\n-# {EMBLEMAS[raridade]}\n\n"
                "O Cassino lançou uma oferta aberta. O **primeiro** leva tudo.\n\n"
                f"{SEPARADOR}"
                f"📜 **Descrição**\n{pacto['descricao']}\n\n"
                f"🪙 **Recompensa**\n**{pacto['recompensa']:,} Moedas do Diabo**\n\n"
                f"🎭 **Consequência**\n{pacto['consequencia']}\n\n"
                f"{SEPARADOR}> *A casa sempre encontra seu dono.*"
            ),
            color=pacto["cor"],
        )
        embed.set_image(url=IMAGEM_PADRAO)
        embed.set_footer(text="Cassino do Diabo  •  Pacto Coletivo")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed, view=PactoColetivoView(pacto, raridade, self))

    @commands.command(name="seguro_saldo")
    async def cmd_seguro_saldo(self, ctx: commands.Context) -> None:
        """Protege o saldo de ser zerado por 1 hora."""
        saldo = get_moedas(ctx.author.id)
        if saldo < CUSTO_SEGURO:
            return await ctx.send(
                f"❌ Você precisa de **{CUSTO_SEGURO:,}** moedas. Tem: **{saldo:,}**.",
                delete_after=10,
            )
        if saldo_protegido(ctx.author.id):
            expira = int(seguros_saldo.get(ctx.author.id, 0))
            return await ctx.send(
                f"🛡️ Seu saldo já está protegido até <t:{expira}:R>.",
                delete_after=10,
            )
        remover_moedas(ctx.author.id, CUSTO_SEGURO)
        expira = _now() + DURACAO_SEGURO
        protecoes[ctx.author.id] = expira
        seguros_saldo[ctx.author.id] = expira
        embed = discord.Embed(
            title="🛡️ Seguro de Saldo Contratado",
            description=(
                f"Seu saldo está protegido contra zeragem por pactos.\n\n"
                f"🪙 Custo: **{CUSTO_SEGURO:,} moedas**\n"
                f"⏳ Expira: <t:{int(expira)}:R>"
            ),
            color=0x2ECC71,
        )
        embed.set_footer(text="Cassino do Diabo  •  Seguro de Saldo")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="minha_divida")
    async def cmd_minha_divida(self, ctx: commands.Context) -> None:
        """Mostra sua dívida ativa, se houver."""
        d = dividas.get(ctx.author.id)
        if not d:
            return await ctx.send("✅ Você não tem dívidas ativas.", delete_after=10)
        vence = int(d["vence_em"])
        tipo  = d.get("tipo", "?")
        if tipo == "banqueiro":
            desc = f"🏦 **Banqueiro** — devolução de **{d['valor']:,} moedas** <t:{vence}:R>"
        elif tipo == "bomba":
            desc = f"🧨 **Bomba-Relógio** — cobrança de **{d['percentual']*100:.0f}%** do saldo <t:{vence}:R>"
        else:
            desc = f"💧 **Drenagem** — **{d.get('percentual',0)*100:.0f}%** ao dia, **{d.get('dias_restantes','?')} dias** restantes"
        embed = discord.Embed(
            title="💳 Sua Dívida Ativa",
            description=desc + "\n\n> *O Cassino sempre cobra o que é seu.*",
            color=0xE74C3C,
        )
        embed.set_footer(text="Cassino do Diabo  •  Dívidas")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="meus_pactos")
    async def cmd_meus_pactos(self, ctx: commands.Context) -> None:
        h = historico.get(ctx.author.id)
        if not h:
            return await ctx.send(
                "📜 Você ainda não participou de nenhum pacto.", delete_after=10
            )
        embed = discord.Embed(
            title="📜 Seus Pactos",
            description=(
                f"-# *\"O Cassino registra tudo.\"*\n\n"
                f"Histórico de **{ctx.author.display_name}**."
            ),
            color=0x8B0000,
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="✅ Aceitos",       value=str(h["aceitos"]),       inline=True)
        embed.add_field(name="❌ Recusados",     value=str(h["recusados"]),     inline=True)
        embed.add_field(name="🪙 Moedas Ganhas", value=f"{h['moedas_ganhas']:,}", inline=True)
        embed.add_field(name="🟡 Lendários",     value=str(h["lendarios"]),     inline=True)
        embed.set_footer(text="Cassino do Diabo  •  Histórico de Pactos")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="ranking_pactos")
    async def cmd_ranking(self, ctx: commands.Context) -> None:
        if not historico:
            return await ctx.send("📊 Nenhum pacto registrado ainda.", delete_after=10)
        top = sorted(
            historico.items(), key=lambda x: x[1]["moedas_ganhas"], reverse=True
        )[:10]
        medalhas = ["🥇", "🥈", "🥉"]
        linhas = []
        for i, (uid, h) in enumerate(top):
            m = ctx.guild.get_member(uid)
            nome = m.display_name if m else f"ID {uid}"
            pos  = medalhas[i] if i < 3 else f"`{i+1}.`"
            linhas.append(
                f"{pos} **{nome}** — 🪙 {h['moedas_ganhas']:,} | ✅ {h['aceitos']}"
            )
        embed = discord.Embed(
            title="🏆 Ranking de Pactos",
            description=(
                f"-# *\"Riqueza conquistada com risco.\"*\n\n{SEPARADOR}"
                + "\n".join(linhas)
            ),
            color=0xFFD700,
        )
        embed.set_footer(text="Cassino do Diabo  •  Ranking")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    # ── Listener: pacto automático ────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Pactos(bot))