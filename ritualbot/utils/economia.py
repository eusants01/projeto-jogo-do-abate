from utils.db import conectar


def criar_tabelas_economia():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exorcistas (
            user_id BIGINT PRIMARY KEY,
            vitorias INTEGER DEFAULT 0,
            vitorias_semana INTEGER DEFAULT 0,
            vitorias_mes INTEGER DEFAULT 0,
            corrupcao INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            user_id BIGINT NOT NULL,
            item TEXT NOT NULL,
            quantidade INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, item)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS buffs (
            user_id BIGINT NOT NULL,
            buff TEXT NOT NULL,
            quantidade INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, buff)
        )
    """)

    conn.commit()
    conn.close()


def garantir_exorcista(user_id: int):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO exorcistas (
            user_id,
            vitorias,
            vitorias_semana,
            vitorias_mes,
            corrupcao
        )
        VALUES (%s, 0, 0, 0, 0)
        ON CONFLICT (user_id) DO NOTHING
    """, (user_id,))

    conn.commit()
    conn.close()


def adicionar_vitoria(user_id: int):
    criar_tabelas_economia()
    garantir_exorcista(user_id)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE exorcistas
        SET
            vitorias = vitorias + 1,
            vitorias_semana = vitorias_semana + 1,
            vitorias_mes = vitorias_mes + 1
        WHERE user_id = %s
    """, (user_id,))

    conn.commit()
    conn.close()


def pegar_vitorias(user_id: int):
    criar_tabelas_economia()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT vitorias FROM exorcistas WHERE user_id = %s",
        (user_id,)
    )

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else 0


def pegar_ranking(limit: int = 10, periodo: str = "geral"):
    criar_tabelas_economia()

    coluna = "vitorias"

    if periodo == "semanal":
        coluna = "vitorias_semana"
    elif periodo == "mensal":
        coluna = "vitorias_mes"

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT user_id, {coluna}
        FROM exorcistas
        WHERE {coluna} > 0
        ORDER BY {coluna} DESC
        LIMIT %s
    """, (limit,))

    resultado = cursor.fetchall()
    conn.close()

    return resultado


def resetar_ranking_periodo(periodo: str):
    criar_tabelas_economia()

    conn = conectar()
    cursor = conn.cursor()

    if periodo == "semanal":
        cursor.execute("UPDATE exorcistas SET vitorias_semana = 0")
    elif periodo == "mensal":
        cursor.execute("UPDATE exorcistas SET vitorias_mes = 0")

    conn.commit()
    conn.close()


def pegar_corrupcao(user_id: int):
    criar_tabelas_economia()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT corrupcao FROM exorcistas WHERE user_id = %s",
        (user_id,)
    )

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else 0


def adicionar_corrupcao(user_id: int, valor: int):
    criar_tabelas_economia()
    garantir_exorcista(user_id)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE exorcistas
        SET corrupcao = GREATEST(0, corrupcao + %s)
        WHERE user_id = %s
    """, (valor, user_id))

    conn.commit()
    conn.close()

    return pegar_corrupcao(user_id)


def reduzir_corrupcao(user_id: int, valor: int):
    return adicionar_corrupcao(user_id, -abs(valor))


def adicionar_item(user_id: int, item: str, quantidade: int = 1):
    criar_tabelas_economia()

    if quantidade <= 0:
        return

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO inventario (user_id, item, quantidade)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, item)
        DO UPDATE SET quantidade = inventario.quantidade + %s
    """, (user_id, item, quantidade, quantidade))

    conn.commit()
    conn.close()


def remover_item(user_id: int, item: str, quantidade: int = 1):
    criar_tabelas_economia()

    if quantidade <= 0:
        return False

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT quantidade
        FROM inventario
        WHERE user_id = %s AND item = %s
    """, (user_id, item))

    resultado = cursor.fetchone()

    if not resultado or resultado[0] < quantidade:
        conn.close()
        return False

    nova_qtd = resultado[0] - quantidade

    if nova_qtd <= 0:
        cursor.execute("""
            DELETE FROM inventario
            WHERE user_id = %s AND item = %s
        """, (user_id, item))
    else:
        cursor.execute("""
            UPDATE inventario
            SET quantidade = %s
            WHERE user_id = %s AND item = %s
        """, (nova_qtd, user_id, item))

    conn.commit()
    conn.close()
    return True


def quantidade_item(user_id: int, item: str):
    criar_tabelas_economia()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT quantidade
        FROM inventario
        WHERE user_id = %s AND item = %s
    """, (user_id, item))

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else 0


def pegar_inventario(user_id: int):
    criar_tabelas_economia()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT item, quantidade
        FROM inventario
        WHERE user_id = %s AND quantidade > 0
        ORDER BY item ASC
    """, (user_id,))

    resultado = cursor.fetchall()
    conn.close()

    return resultado


def adicionar_buff(user_id: int, buff: str, quantidade: int = 1):
    criar_tabelas_economia()

    if quantidade <= 0:
        return

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO buffs (user_id, buff, quantidade)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, buff)
        DO UPDATE SET quantidade = buffs.quantidade + %s
    """, (user_id, buff, quantidade, quantidade))

    conn.commit()
    conn.close()


def remover_buff(user_id: int, buff: str, quantidade: int = 1):
    criar_tabelas_economia()

    if quantidade <= 0:
        return False

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT quantidade
        FROM buffs
        WHERE user_id = %s AND buff = %s
    """, (user_id, buff))

    resultado = cursor.fetchone()

    if not resultado or resultado[0] < quantidade:
        conn.close()
        return False

    nova_qtd = resultado[0] - quantidade

    if nova_qtd <= 0:
        cursor.execute("""
            DELETE FROM buffs
            WHERE user_id = %s AND buff = %s
        """, (user_id, buff))
    else:
        cursor.execute("""
            UPDATE buffs
            SET quantidade = %s
            WHERE user_id = %s AND buff = %s
        """, (nova_qtd, user_id, buff))

    conn.commit()
    conn.close()
    return True


def consumir_buff(user_id: int, buff: str, quantidade: int = 1):
    return remover_buff(user_id, buff, quantidade)


def quantidade_buff(user_id: int, buff: str):
    criar_tabelas_economia()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT quantidade
        FROM buffs
        WHERE user_id = %s AND buff = %s
    """, (user_id, buff))

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else 0


def pegar_buffs(user_id: int):
    criar_tabelas_economia()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT buff, quantidade
        FROM buffs
        WHERE user_id = %s AND quantidade > 0
        ORDER BY buff ASC
    """, (user_id,))

    resultado = cursor.fetchall()
    conn.close()

    return resultado