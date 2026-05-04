import os
import psycopg2
from psycopg2.extras import RealDictCursor

VIDAS_MAXIMAS = 300

DATABASE_URL = os.getenv("DATABASE_URL")


def conectar():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jogadores (
        user_id BIGINT PRIMARY KEY,
        username TEXT NOT NULL,
        vidas INTEGER DEFAULT 300,
        abates INTEGER DEFAULT 0,
        contratos INTEGER DEFAULT 0,
        status TEXT DEFAULT 'vivo',
        alvo_id BIGINT,
        familia TEXT DEFAULT 'Livre'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS eventos (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        descricao TEXT NOT NULL,
        multiplicador_abate INTEGER DEFAULT 1,
        dano_extra INTEGER DEFAULT 0,
        ativo BOOLEAN DEFAULT FALSE
    )
    """)

    conn.commit()
    conn.close()


def registrar_jogador(user_id, username):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO jogadores (user_id, username, vidas)
    VALUES (%s, %s, %s)
    ON CONFLICT (user_id) DO NOTHING
    """, (user_id, username, VIDAS_MAXIMAS))

    conn.commit()
    conn.close()


def buscar_jogador(user_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jogadores WHERE user_id = %s", (user_id,))
    jogador = cursor.fetchone()

    conn.close()
    return jogador


def listar_jogadores_vivos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM jogadores
    WHERE status = 'vivo'
    ORDER BY username
    """)

    dados = cursor.fetchall()
    conn.close()
    return dados


def listar_ranking():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM jogadores
    ORDER BY abates DESC, contratos DESC, vidas DESC
    LIMIT 10
    """)

    dados = cursor.fetchall()
    conn.close()
    return dados


def adicionar_abate(user_id, quantidade=1):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE jogadores
    SET abates = abates + %s
    WHERE user_id = %s
    """, (quantidade, user_id))

    conn.commit()
    conn.close()


def remover_vida(user_id, quantidade=1):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE jogadores
    SET vidas = vidas - %s
    WHERE user_id = %s AND status = 'vivo'
    """, (quantidade, user_id))

    cursor.execute("SELECT vidas FROM jogadores WHERE user_id = %s", (user_id,))
    vida = cursor.fetchone()

    if vida and vida["vidas"] <= 0:
        cursor.execute("""
        UPDATE jogadores
        SET vidas = 0, status = 'eliminado', alvo_id = NULL
        WHERE user_id = %s
        """, (user_id,))

    conn.commit()
    conn.close()

    return buscar_jogador(user_id)


def resetar_jogo():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM jogadores")
    cursor.execute("UPDATE eventos SET ativo = FALSE")

    conn.commit()
    conn.close()


def restaurar_vidas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE jogadores
    SET vidas = %s, status = 'vivo', alvo_id = NULL
    """, (VIDAS_MAXIMAS,))

    conn.commit()
    conn.close()