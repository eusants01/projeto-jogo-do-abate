import os
import psycopg2

VIDAS_MAXIMAS = 750
DATABASE_URL = os.getenv("DATABASE_URL")


def conectar():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não encontrada nas variáveis do Railway.")
    return psycopg2.connect(DATABASE_URL)


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
        alvo_id BIGINT DEFAULT NULL,
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


def registrar_jogador(user_id: int, username: str):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO jogadores (user_id, username, vidas)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING
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
        WHERE user_id = %s
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
        "UPDATE jogadores SET alvo_id = %s WHERE user_id = %s",
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
        "UPDATE jogadores SET abates = abates + %s WHERE user_id = %s",
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
        SET vidas = GREATEST(vidas - %s, 0)
        WHERE user_id = %s AND status = 'vivo'
        """,
        (quantidade, user_id)
    )

    cursor.execute(
        "SELECT vidas FROM jogadores WHERE user_id = %s",
        (user_id,)
    )

    resultado = cursor.fetchone()

    if resultado and resultado[0] <= 0:
        cursor.execute(
            """
            UPDATE jogadores
            SET vidas = 0, status = 'eliminado', alvo_id = NULL
            WHERE user_id = %s
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
        VALUES (%s, %s, %s, %s, FALSE)
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
    WHERE ativo = TRUE
    ORDER BY id DESC
    LIMIT 1
    """)

    evento = cursor.fetchone()
    conn.close()
    return evento


def ativar_evento(evento_id: int):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("UPDATE eventos SET ativo = FALSE")
    cursor.execute("UPDATE eventos SET ativo = TRUE WHERE id = %s", (evento_id,))

    conn.commit()
    conn.close()


def encerrar_eventos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("UPDATE eventos SET ativo = FALSE")

    conn.commit()
    conn.close()


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

    cursor.execute(
        """
        UPDATE jogadores
        SET vidas = %s, status = 'vivo', alvo_id = NULL
        """,
        (VIDAS_MAXIMAS,)
    )

    conn.commit()
    conn.close()
