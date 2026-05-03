import sqlite3
from pathlib import Path

DB_PATH = Path("ritualbot.db")


def conectar():
    return sqlite3.connect(DB_PATH)


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jogadores (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        vidas INTEGER DEFAULT 3,
        abates INTEGER DEFAULT 0,
        contratos INTEGER DEFAULT 0,
        status TEXT DEFAULT 'vivo',
        alvo_id INTEGER DEFAULT NULL,
        familia TEXT DEFAULT 'Livre'
    )
    """)

    conn.commit()
    conn.close()


def registrar_jogador(user_id: int, username: str):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO jogadores (user_id, username)
        VALUES (?, ?)
        """,
        (user_id, username)
    )

    conn.commit()
    conn.close()


def buscar_jogador(user_id: int):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user_id, username, vidas, abates, contratos, status, alvo_id, familia
        FROM jogadores
        WHERE user_id = ?
        """,
        (user_id,)
    )

    jogador = cursor.fetchone()
    conn.close()
    return jogador


def listar_ranking():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT user_id, username, vidas, abates, contratos, status, familia
    FROM jogadores
    ORDER BY abates DESC, contratos DESC, vidas DESC
    LIMIT 10
    """)

    jogadores = cursor.fetchall()
    conn.close()
    return jogadores


def adicionar_abate(vencedor_id: int):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE jogadores SET abates = abates + 1 WHERE user_id = ?",
        (vencedor_id,)
    )

    conn.commit()
    conn.close()


def remover_vida(user_id: int):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE jogadores SET vidas = vidas - 1 WHERE user_id = ? AND status = 'vivo'",
        (user_id,)
    )

    cursor.execute(
        "SELECT vidas FROM jogadores WHERE user_id = ?",
        (user_id,)
    )

    resultado = cursor.fetchone()

    if resultado and resultado[0] <= 0:
        cursor.execute(
            "UPDATE jogadores SET vidas = 0, status = 'eliminado' WHERE user_id = ?",
            (user_id,)
        )

    conn.commit()
    conn.close()

    return buscar_jogador(user_id)


def resetar_jogo():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM jogadores")

    conn.commit()
    conn.close()
