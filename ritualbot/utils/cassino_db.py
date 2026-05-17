import sqlite3
from datetime import datetime

DB_PATH = "cassino.db"


def conectar():
    return sqlite3.connect(DB_PATH)


def criar_tabelas_cassino():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cassino_usuarios (
            user_id INTEGER PRIMARY KEY,
            moedas INTEGER DEFAULT 500,
            total_ganho INTEGER DEFAULT 0,
            total_perdido INTEGER DEFAULT 0,
            ultima_daily TEXT,
            ultima_roleta TEXT
        )
    """)

    conn.commit()
    conn.close()


def garantir_usuario(user_id: int):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO cassino_usuarios (user_id, moedas)
        VALUES (?, 500)
    """, (user_id,))

    conn.commit()
    conn.close()


def obter_usuario(user_id: int):
    garantir_usuario(user_id)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, moedas, total_ganho, total_perdido, ultima_daily, ultima_roleta
        FROM cassino_usuarios
        WHERE user_id = ?
    """, (user_id,))

    dados = cursor.fetchone()
    conn.close()
    return dados


def obter_saldo(user_id: int) -> int:
    dados = obter_usuario(user_id)
    return dados[1]


def adicionar_moedas(user_id: int, quantidade: int):
    garantir_usuario(user_id)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cassino_usuarios
        SET moedas = moedas + ?,
            total_ganho = total_ganho + ?
        WHERE user_id = ?
    """, (quantidade, quantidade, user_id))

    conn.commit()
    conn.close()


def remover_moedas(user_id: int, quantidade: int):
    garantir_usuario(user_id)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cassino_usuarios
        SET moedas = MAX(moedas - ?, 0),
            total_perdido = total_perdido + ?
        WHERE user_id = ?
    """, (quantidade, quantidade, user_id))

    conn.commit()
    conn.close()


def transferir_moedas(origem_id: int, destino_id: int, quantidade: int) -> bool:
    garantir_usuario(origem_id)
    garantir_usuario(destino_id)

    saldo_origem = obter_saldo(origem_id)

    if saldo_origem < quantidade:
        return False

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cassino_usuarios
        SET moedas = moedas - ?
        WHERE user_id = ?
    """, (quantidade, origem_id))

    cursor.execute("""
        UPDATE cassino_usuarios
        SET moedas = moedas + ?
        WHERE user_id = ?
    """, (quantidade, destino_id))

    conn.commit()
    conn.close()
    return True


def atualizar_daily(user_id: int):
    garantir_usuario(user_id)

    agora = datetime.utcnow().isoformat()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cassino_usuarios
        SET ultima_daily = ?
        WHERE user_id = ?
    """, (agora, user_id))

    conn.commit()
    conn.close()


def atualizar_roleta(user_id: int):
    garantir_usuario(user_id)

    agora = datetime.utcnow().isoformat()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cassino_usuarios
        SET ultima_roleta = ?
        WHERE user_id = ?
    """, (agora, user_id))

    conn.commit()
    conn.close()


def ranking_ricos(limit: int = 10):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, moedas
        FROM cassino_usuarios
        ORDER BY moedas DESC
        LIMIT ?
    """, (limit,))

    dados = cursor.fetchall()
    conn.close()
    return dados