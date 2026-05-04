import sqlite3
from pathlib import Path

DB_PATH = Path("ritualbot.db")
VIDAS_MAXIMAS = 300


def conectar():
    return sqlite3.connect(DB_PATH)


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jogadores (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        vidas INTEGER DEFAULT 300,
        abates INTEGER DEFAULT 0,
        contratos INTEGER DEFAULT 0,
        status TEXT DEFAULT 'vivo',
        alvo_id INTEGER DEFAULT NULL,
        familia TEXT DEFAULT 'Livre'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS eventos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT NOT NULL,
        multiplicador_abate INTEGER DEFAULT 1,
        dano_extra INTEGER DEFAULT 0,
        ativo INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


def registrar_jogador(user_id: int, username: str):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO jogadores (user_id, username, vidas)
        VALUES (?, ?, ?)
        """,
        (user_id, username, VIDAS_MAXIMAS)
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


def listar_jogadores_vivos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT user_id, username, vidas, abates, contratos, status, alvo_id, familia
    FROM jogadores
    WHERE status = 'vivo'
    ORDER BY username ASC
    """)

    jogadores = cursor.fetchall()
    conn.close()
    return jogadores


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


def definir_alvo(user_id: int, alvo_id: int | None):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE jogadores SET alvo_id = ? WHERE user_id = ?",
        (alvo_id, user_id)
    )

    conn.commit()
    conn.close()


def limpar_alvos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("UPDATE jogadores SET alvo_id = NULL")

    conn.commit()
    conn.close()


def adicionar_abate(vencedor_id: int, quantidade: int = 1):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE jogadores SET abates = abates + ? WHERE user_id = ?",
        (quantidade, vencedor_id)
    )

    conn.commit()
    conn.close()


def remover_vida(user_id: int, quantidade: int = 1):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE jogadores
        SET vidas = vidas - ?
        WHERE user_id = ? AND status = 'vivo'
        """,
        (quantidade, user_id)
    )

    cursor.execute(
        "SELECT vidas FROM jogadores WHERE user_id = ?",
        (user_id,)
    )

    resultado = cursor.fetchone()

    if resultado and resultado[0] <= 0:
        cursor.execute(
            """
            UPDATE jogadores
            SET vidas = 0, status = 'eliminado', alvo_id = NULL
            WHERE user_id = ?
            """,
            (user_id,)
        )

    conn.commit()
    conn.close()

    return buscar_jogador(user_id)


def criar_evento(nome: str, descricao: str, multiplicador_abate: int = 1, dano_extra: int = 0):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO eventos (nome, descricao, multiplicador_abate, dano_extra, ativo)
        VALUES (?, ?, ?, ?, 0)
        """,
        (nome, descricao, multiplicador_abate, dano_extra)
    )

    conn.commit()
    conn.close()


def listar_eventos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, nome, descricao, multiplicador_abate, dano_extra, ativo
    FROM eventos
    ORDER BY id DESC
    """)

    eventos = cursor.fetchall()
    conn.close()
    return eventos


def buscar_evento_ativo():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, nome, descricao, multiplicador_abate, dano_extra, ativo
    FROM eventos
    WHERE ativo = 1
    ORDER BY id DESC
    LIMIT 1
    """)

    evento = cursor.fetchone()
    conn.close()
    return evento


def ativar_evento(evento_id: int):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("UPDATE eventos SET ativo = 0")
    cursor.execute("UPDATE eventos SET ativo = 1 WHERE id = ?", (evento_id,))

    conn.commit()
    conn.close()


def encerrar_eventos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("UPDATE eventos SET ativo = 0")

    conn.commit()
    conn.close()


def resetar_jogo():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM jogadores")
    cursor.execute("UPDATE eventos SET ativo = 0")

    conn.commit()
    conn.close()


def restaurar_vidas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE jogadores
        SET vidas = ?, status = 'vivo', alvo_id = NULL
        """,
        (VIDAS_MAXIMAS,)
    )

    conn.commit()
    conn.close()
