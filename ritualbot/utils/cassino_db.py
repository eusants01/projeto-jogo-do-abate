import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL")


def conectar():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não encontrada nas variáveis de ambiente.")

    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def criar_tabelas_cassino():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cassino_usuarios (
            user_id BIGINT PRIMARY KEY,
            moedas BIGINT DEFAULT 500,
            total_ganho BIGINT DEFAULT 0,
            total_perdido BIGINT DEFAULT 0,
            ultima_daily TIMESTAMP,
            ultima_roleta TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


def garantir_usuario(user_id: int):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cassino_usuarios (user_id, moedas)
        VALUES (%s, 500)
        ON CONFLICT (user_id) DO NOTHING
    """, (user_id,))

    conn.commit()
    cursor.close()
    conn.close()


def obter_usuario(user_id: int):
    garantir_usuario(user_id)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, moedas, total_ganho, total_perdido, ultima_daily, ultima_roleta
        FROM cassino_usuarios
        WHERE user_id = %s
    """, (user_id,))

    dados = cursor.fetchone()

    cursor.close()
    conn.close()

    return (
        dados["user_id"],
        dados["moedas"],
        dados["total_ganho"],
        dados["total_perdido"],
        dados["ultima_daily"],
        dados["ultima_roleta"]
    )


def obter_saldo(user_id: int) -> int:
    dados = obter_usuario(user_id)
    return int(dados[1])


def adicionar_moedas(user_id: int, quantidade: int):
    garantir_usuario(user_id)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cassino_usuarios
        SET moedas = moedas + %s,
            total_ganho = total_ganho + %s
        WHERE user_id = %s
    """, (quantidade, quantidade, user_id))

    conn.commit()
    cursor.close()
    conn.close()


def remover_moedas(user_id: int, quantidade: int):
    garantir_usuario(user_id)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cassino_usuarios
        SET moedas = GREATEST(moedas - %s, 0),
            total_perdido = total_perdido + %s
        WHERE user_id = %s
    """, (quantidade, quantidade, user_id))

    conn.commit()
    cursor.close()
    conn.close()


def transferir_moedas(origem_id: int, destino_id: int, quantidade: int) -> bool:
    garantir_usuario(origem_id)
    garantir_usuario(destino_id)

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT moedas
            FROM cassino_usuarios
            WHERE user_id = %s
            FOR UPDATE
        """, (origem_id,))

        origem = cursor.fetchone()

        if not origem or origem["moedas"] < quantidade:
            conn.rollback()
            return False

        cursor.execute("""
            UPDATE cassino_usuarios
            SET moedas = moedas - %s
            WHERE user_id = %s
        """, (quantidade, origem_id))

        cursor.execute("""
            UPDATE cassino_usuarios
            SET moedas = moedas + %s
            WHERE user_id = %s
        """, (quantidade, destino_id))

        conn.commit()
        return True

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def atualizar_daily(user_id: int):
    garantir_usuario(user_id)

    agora = datetime.now(timezone.utc)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cassino_usuarios
        SET ultima_daily = %s
        WHERE user_id = %s
    """, (agora, user_id))

    conn.commit()
    cursor.close()
    conn.close()


def atualizar_roleta(user_id: int):
    garantir_usuario(user_id)

    agora = datetime.now(timezone.utc)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cassino_usuarios
        SET ultima_roleta = %s
        WHERE user_id = %s
    """, (agora, user_id))

    conn.commit()
    cursor.close()
    conn.close()


def ranking_ricos(limit: int = 10):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, moedas
        FROM cassino_usuarios
        ORDER BY moedas DESC
        LIMIT %s
    """, (limit,))

    dados = cursor.fetchall()

    cursor.close()
    conn.close()

    return [(dado["user_id"], dado["moedas"]) for dado in dados]