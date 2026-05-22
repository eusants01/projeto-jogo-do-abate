
import discord
from discord.ext import commands

from utils.economia import (
    criar_tabelas_economia,
    pegar_inventario,
    pegar_buffs,
    pegar_corrupcao,
    quantidade_item,
    remover_item,
    adicionar_item,
    adicionar_buff,
    reduzir_corrupcao,
    adicionar_corrupcao,
)

from utils.db import buscar_jogador, conectar


VIDAS_MAXIMAS = 750
ITEM_FRAGMENTO = "Fragmento Amaldiçoado"

NOME_LOJA = "Mercado Amaldiçoado"
BANNER_LOJA = "https://cdn.discordapp.com/attachments/1500528332008325281/1507438369196478675/content.png?ex=6a11e6e2&is=6a109562&hm=d5d0b8cc07bdbede9db04a5b48670ad52e9a679dcf1ba807f2d355eda330c890&"

COR_ROXA = 0x6A00FF
COR_ROXA_ESCURO = 0x240046
COR_VERMELHA = 0xE63946
COR_VERDE = 0x2ECC71
COR_DOURADA = 0xF1C40F
COR_PRETA = 0x111111
COR_CINZA = 0x95A5A6


RARIDADES = {
    "comum": {"nome": "Comum", "emoji": "⚪", "cor": COR_CINZA},
    "raro": {"nome": "Raro", "emoji": "🟣", "cor": COR_ROXA},
    "epico": {"nome": "Épico", "emoji": "🔴", "cor": COR_VERMELHA},
    "lendario": {"nome": "Lendário", "emoji": "🟡", "cor": COR_DOURADA},
    "proibido": {"nome": "Proibido", "emoji": "☠️", "cor": COR_PRETA},
    "classe_s": {"nome": "Classe Especial Amaldiçoada", "emoji": "👑", "cor": COR_DOURADA},
}


LOJA_AMALDICOADA = {
    "furia_amaldicoada": {
        "nome": "Fúria Amaldiçoada",
        "emoji": "🔥",
        "categoria": "poder",
        "descricao": "Recebe 2 cargas de fúria.",
        "lore": "Energia amaldiçoada explode no corpo do usuário, aumentando o dano em combate.",
        "preco": 120,
        "tipo": "buff",
        "buff": "furia",
        "quantidade": 2,
        "corrupcao": 1,
        "raridade": "raro",
    },
    "black_flash_corrompido": {
        "nome": "Black Flash Corrompido",
        "emoji": "⚫",
        "categoria": "poder",
        "descricao": "Recebe 3 cargas de crítico.",
        "lore": "Uma distorção do espaço contaminada por energia instável.",
        "preco": 280,
        "tipo": "buff",
        "buff": "critico",
        "quantidade": 3,
        "corrupcao": 2,
        "raridade": "epico",
    },
    "berserk_amaldicoado": {
        "nome": "Berserk Amaldiçoado",
        "emoji": "🩸",
        "categoria": "poder",
        "descricao": "Recebe 2 cargas de berserk.",
        "lore": "Poder bruto em troca de sanidade. Excelente contra bosses.",
        "preco": 420,
        "tipo": "buff",
        "buff": "berserk",
        "quantidade": 2,
        "corrupcao": 4,
        "raridade": "lendario",
    },
    "colapso_dominio": {
        "nome": "Colapso do Domínio",
        "emoji": "🌑",
        "categoria": "poder",
        "descricao": "Recebe 2 fúrias, 2 críticos e 1 berserk.",
        "lore": "Um domínio instável quebrado por dentro.",
        "preco": 950,
        "tipo": "multi_buff",
        "buffs": [
            {"buff": "furia", "quantidade": 2},
            {"buff": "critico", "quantidade": 2},
            {"buff": "berserk", "quantidade": 1},
        ],
        "corrupcao": 8,
        "raridade": "classe_s",
    },
    "manto_maldicao": {
        "nome": "Manto de Maldição",
        "emoji": "🛡️",
        "categoria": "defesa",
        "descricao": "Recebe 2 cargas de escudo.",
        "lore": "Um manto coberto por energia amaldiçoada condensada.",
        "preco": 100,
        "tipo": "buff",
        "buff": "escudo",
        "quantidade": 2,
        "corrupcao": 1,
        "raridade": "raro",
    },
    "carapaca_especial": {
        "nome": "Carapaça Especial",
        "emoji": "🐚",
        "categoria": "defesa",
        "descricao": "Recebe 4 cargas de escudo.",
        "lore": "Proteção feita com restos de maldições especiais.",
        "preco": 260,
        "tipo": "buff",
        "buff": "escudo",
        "quantidade": 4,
        "corrupcao": 2,
        "raridade": "epico",
    },
    "voto_sobrevivencia": {
        "nome": "Voto de Sobrevivência",
        "emoji": "📜",
        "categoria": "defesa",
        "descricao": "Restaura toda sua vida e recebe 1 escudo.",
        "lore": "Um pacto de emergência para sobreviver ao impossível.",
        "preco": 300,
        "tipo": "cura_buff",
        "buff": "escudo",
        "quantidade": 1,
        "valor": VIDAS_MAXIMAS,
        "corrupcao": 3,
        "raridade": "lendario",
    },
    "dedo_sukuna": {
        "nome": "Dedo do Sukuna",
        "emoji": "☠️",
        "categoria": "reliquias",
        "descricao": "Recebe 5 cargas de berserk e equipa a relíquia.",
        "lore": "Um artefato que jamais deveria estar nas mãos de alguém comum.",
        "preco": 1250,
        "tipo": "reliquia_buff",
        "reliquia": "Dedo do Sukuna",
        "buff": "berserk",
        "quantidade": 5,
        "corrupcao": 12,
        "raridade": "classe_s",
    },
    "roda_adaptacao": {
        "nome": "Roda da Adaptação",
        "emoji": "☸️",
        "categoria": "reliquias",
        "descricao": "Equipa a relíquia e recebe 6 escudos.",
        "lore": "A roda gira. A maldição aprende. O corpo resiste.",
        "preco": 1100,
        "tipo": "reliquia_buff",
        "reliquia": "Roda da Adaptação",
        "buff": "escudo",
        "quantidade": 6,
        "corrupcao": 6,
        "raridade": "classe_s",
    },
    "nucleo_caos": {
        "nome": "Núcleo do Caos",
        "emoji": "🧿",
        "categoria": "reliquias",
        "descricao": "Recebe 3 sorte, 2 crítico e equipa a relíquia.",
        "lore": "Um núcleo que pulsa como se estivesse vivo.",
        "preco": 1000,
        "tipo": "reliquia_multi",
        "reliquia": "Núcleo do Caos",
        "buffs": [{"buff": "sorte", "quantidade": 3}, {"buff": "critico", "quantidade": 2}],
        "corrupcao": 7,
        "raridade": "proibido",
    },
    "alma_transfigurada": {
        "nome": "Alma Transfigurada",
        "emoji": "🫀",
        "categoria": "reliquias",
        "descricao": "Recebe 2 berserk e 2 sorte.",
        "lore": "Uma alma alterada por uma maldição de forma irreversível.",
        "preco": 850,
        "tipo": "multi_buff",
        "buffs": [{"buff": "berserk", "quantidade": 2}, {"buff": "sorte", "quantidade": 2}],
        "corrupcao": 6,
        "raridade": "proibido",
    },
    "ritual_sangue": {
        "nome": "Ritual de Sangue",
        "emoji": "🩸",
        "categoria": "rituais",
        "descricao": "Recebe 3 fúrias e 1 crítico.",
        "lore": "Um ritual agressivo usado antes de raids perigosas.",
        "preco": 360,
        "tipo": "multi_buff",
        "buffs": [{"buff": "furia", "quantidade": 3}, {"buff": "critico", "quantidade": 1}],
        "corrupcao": 5,
        "raridade": "epico",
    },
    "pacto_proibido": {
        "nome": "Pacto Proibido",
        "emoji": "✍️",
        "categoria": "rituais",
        "descricao": "Recebe 2 berserk, 2 crítico e 2 sorte.",
        "lore": "Assinar este pacto significa aceitar que o preço virá depois.",
        "preco": 780,
        "tipo": "multi_buff",
        "buffs": [
            {"buff": "berserk", "quantidade": 2},
            {"buff": "critico", "quantidade": 2},
            {"buff": "sorte", "quantidade": 2},
        ],
        "corrupcao": 9,
        "raridade": "lendario",
    },
    "purificacao_instavel": {
        "nome": "Purificação Instável",
        "emoji": "🧪",
        "categoria": "rituais",
        "descricao": "Remove 20 de corrupção, mas concede 1 berserk.",
        "lore": "Limpa a alma, mas deixa uma rachadura perigosa.",
        "preco": 260,
        "tipo": "purificar_buff",
        "valor": 20,
        "buff": "berserk",
        "quantidade": 1,
        "raridade": "epico",
    },
    "rei_maldicoes": {
        "nome": "Marca do Rei das Maldições",
        "emoji": "👑",
        "categoria": "secreto",
        "descricao": "Recebe 6 berserk e 3 crítico.",
        "lore": "A marca daqueles que aceitaram o abismo completamente.",
        "preco": 1800,
        "tipo": "multi_buff",
        "buffs": [{"buff": "berserk", "quantidade": 6}, {"buff": "critico", "quantidade": 3}],
        "corrupcao": 18,
        "requer_corrupcao": 70,
        "raridade": "classe_s",
    },
    "santuario_malevolente": {
        "nome": "Santuário Malevolente",
        "emoji": "⛩️",
        "categoria": "secreto",
        "descricao": "Recebe 4 fúrias, 4 críticos, 2 berserk e equipa relíquia.",
        "lore": "Um domínio aberto sem barreiras. Tudo dentro dele pode ser cortado.",
        "preco": 2500,
        "tipo": "reliquia_multi",
        "reliquia": "Santuário Malevolente",
        "buffs": [
            {"buff": "furia", "quantidade": 4},
            {"buff": "critico", "quantidade": 4},
            {"buff": "berserk", "quantidade": 2},
        ],
        "corrupcao": 25,
        "requer_corrupcao": 80,
        "raridade": "classe_s",
    },
}


CATEGORIAS = {
    "poder": {"titulo": "🔥 Poder Bruto", "descricao": "Buffs agressivos para aumentar dano em bosses e maldições.", "cor": COR_VERMELHA},
    "defesa": {"titulo": "🛡️ Defesa Profana", "descricao": "Proteções contaminadas por energia amaldiçoada.", "cor": COR_ROXA},
    "reliquias": {"titulo": "☠️ Relíquias Proibidas", "descricao": "Artefatos raros que podem ser equipados e integrados às raids.", "cor": COR_DOURADA},
    "rituais": {"titulo": "📜 Rituais e Corrupção", "descricao": "Rituais instáveis que manipulam poder e corrupção.", "cor": COR_ROXA_ESCURO},
    "secreto": {"titulo": "🌑 Mercado Secreto", "descricao": "Itens liberados apenas para usuários altamente corrompidos.", "cor": COR_PRETA},
}


def criar_tabelas_amaldicoadas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reliquias_equipadas (
            user_id BIGINT PRIMARY KEY,
            reliquia TEXT,
            atualizado_em TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    conn.close()


def salvar_reliquia(user_id: int, reliquia: str):
    criar_tabelas_amaldicoadas()
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reliquias_equipadas (user_id, reliquia, atualizado_em)
        VALUES (%s, %s, NOW())
        ON CONFLICT (user_id) DO UPDATE SET reliquia = EXCLUDED.reliquia, atualizado_em = NOW()
    """, (user_id, reliquia))
    conn.commit()
    conn.close()


def pegar_reliquia(user_id: int):
    try:
        criar_tabelas_amaldicoadas()
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT reliquia FROM reliquias_equipadas WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return row[0] if not isinstance(row, dict) else row.get("reliquia")
    except Exception as e:
        print(f"[MERCADO AMALDIÇOADO] Erro ao pegar relíquia: {e}")
        return None


def restaurar_vida_total(user_id: int):
    jogador = buscar_jogador(user_id)
    if not jogador:
        return False
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE jogadores SET vidas = %s, status = 'vivo' WHERE user_id = %s", (VIDAS_MAXIMAS, user_id))
    conn.commit()
    conn.close()
    return True


def itens_por_categoria(categoria: str):
    return {codigo: item for codigo, item in LOJA_AMALDICOADA.items() if item["categoria"] == categoria}


def pegar_raridade(item: dict):
    return RARIDADES.get(item.get("raridade", "comum"), RARIDADES["comum"])


def barra_corrupcao(valor: int):
    valor = max(0, min(int(valor or 0), 100))
    preenchidos = valor // 10
    vazios = 10 - preenchidos
    if valor < 30:
        status = "Estável"
    elif valor < 60:
        status = "Instável"
    elif valor < 85:
        status = "Perigosa"
    else:
        status = "Crítica"
    return f"`{'█' * preenchidos}{'░' * vazios}` **{valor}%** — {status}"


def classe_amaldicoada(corrupcao: int):
    if corrupcao >= 85:
        return "👑 Receptáculo Classe Especial"
    if corrupcao >= 70:
        return "🌑 Portador do Abismo"
    if corrupcao >= 45:
        return "☠️ Marcado pela Maldição"
    if corrupcao >= 20:
        return "🩸 Instável"
    return "🧿 Controlado"


async def enviar_ephemeral(interaction: discord.Interaction, content=None, embed=None, view=None):
    if interaction.response.is_done():
        await interaction.followup.send(content=content, embed=embed, view=view, ephemeral=True)
    else:
        await interaction.response.send_message(content=content, embed=embed, view=view, ephemeral=True)


def criar_embed_loja():
    embed = discord.Embed(
        title=f"☠️ {NOME_LOJA}",
        description=(
            "```ansi\n"
            "\u001b[35m╔══════════════════════════════╗\n"
            "\u001b[31m║      MERCADO AMALDIÇOADO     ║\n"
            "\u001b[35m╚══════════════════════════════╝\n"
            "```\n"
            "Poder bruto. Corrupção. Artefatos proibidos.\n\n"
            "Aqui não existe segurança. Cada compra entrega poder, mas também deixa uma marca.\n\n"
            "🧩 **Moeda:** Fragmentos Amaldiçoados\n"
            "🩸 **Risco:** itens podem aumentar corrupção\n"
            "☠️ **Foco:** dano extremo, relíquias e pactos proibidos\n"
            "🌑 **Mercado Secreto:** liberado para corrupção elevada"
        ),
        color=COR_ROXA,
    )
    embed.add_field(name="🔥 Poder", value="Fúria, crítico e berserk.", inline=True)
    embed.add_field(name="🛡️ Defesa", value="Proteções corrompidas.", inline=True)
    embed.add_field(name="☠️ Relíquias", value="Itens equipáveis proibidos.", inline=True)
    embed.add_field(name="📜 Rituais", value="Pactos e corrupção.", inline=True)
    embed.add_field(name="🌑 Secreto", value="Somente corrompidos.", inline=True)
    embed.add_field(name="🎒 Registro", value="Inventário e relíquia.", inline=True)
    if BANNER_LOJA != "COLOQUE_AQUI_O_LINK_DO_BANNER":
        embed.set_image(url=BANNER_LOJA)
    embed.set_footer(text="Família Sant's • Mercado Amaldiçoado")
    return embed


def criar_embed_categoria(categoria: str, user_id: int = None):
    dados = CATEGORIAS[categoria]
    itens = itens_por_categoria(categoria)
    embed = discord.Embed(title=dados["titulo"], description=f"{dados['descricao']}\n\nClique no item desejado para confirmar a compra.", color=dados["cor"])
    corrupcao = pegar_corrupcao(user_id) if user_id else 0
    for codigo, item in itens.items():
        requisito = item.get("requer_corrupcao")
        bloqueado = requisito is not None and corrupcao < requisito
        raridade = pegar_raridade(item)
        req_txt = f"🔒 Requer corrupção **{requisito}**\n" if bloqueado else ""
        embed.add_field(
            name=f"{item['emoji']} {item['nome']}{' 🔒' if bloqueado else ''}",
            value=f"{raridade['emoji']} **{raridade['nome']}**\n🧩 Preço: **{item['preco']}**\n🩸 Corrupção: **+{item.get('corrupcao', 0)}**\n📜 {item['descricao']}\n{req_txt}`{codigo}`",
            inline=False,
        )
    embed.set_footer(text=f"Família Sant's • {NOME_LOJA}")
    return embed


def criar_embed_item(codigo: str, item: dict, usuario: discord.Member | discord.User):
    raridade = pegar_raridade(item)
    saldo = quantidade_item(usuario.id, ITEM_FRAGMENTO)
    corrupcao = pegar_corrupcao(usuario.id)
    embed = discord.Embed(
        title=f"{item['emoji']} {item['nome']}",
        description=(
            f"{raridade['emoji']} **Raridade:** `{raridade['nome']}`\n"
            f"🧩 **Preço:** `{item['preco']}` Fragmentos\n"
            f"💰 **Seu saldo:** `{saldo}` Fragmentos\n"
            f"🩸 **Corrupção atual:** `{corrupcao}`\n"
            f"☠️ **Classe:** {classe_amaldicoada(corrupcao)}\n\n"
            f"**Efeito:**\n{item['descricao']}\n\n"
            f"**Registro Proibido:**\n*{item.get('lore', 'Nenhuma informação registrada.')}*"
        ),
        color=raridade["cor"],
    )
    if item.get("requer_corrupcao"):
        embed.add_field(name="🌑 Requisito Secreto", value=f"Requer corrupção mínima: **{item['requer_corrupcao']}**", inline=False)
    if item.get("corrupcao", 0) > 0:
        embed.add_field(name="🩸 Aviso de Corrupção", value=f"Esta compra adiciona **+{item.get('corrupcao', 0)}** de corrupção.", inline=False)
    embed.set_footer(text=f"Código do item: {codigo}")
    return embed


def criar_embed_inventario(membro: discord.Member | discord.User):
    itens = pegar_inventario(membro.id)
    buffs = pegar_buffs(membro.id)
    corrupcao = pegar_corrupcao(membro.id)
    saldo = quantidade_item(membro.id, ITEM_FRAGMENTO)
    reliquia = pegar_reliquia(membro.id) or "Nenhuma relíquia equipada"
    texto_itens = "Nenhum item encontrado." if not itens else "\n".join([f"• **{item}** x{qtd}" for item, qtd in itens])
    texto_buffs = "Nenhum buff ativo." if not buffs else "\n".join([f"• **{buff}** x{qtd}" for buff, qtd in buffs])
    embed = discord.Embed(
        title=f"🎒 Registro Amaldiçoado — {membro.display_name}",
        description=f"☠️ **Classe:** {classe_amaldicoada(corrupcao)}\n🧩 **Fragmentos:** `{saldo}`\n🩸 **Corrupção:** {barra_corrupcao(corrupcao)}\n🌑 **Relíquia Equipada:** `{reliquia}`",
        color=COR_ROXA,
    )
    embed.add_field(name="📦 Itens", value=texto_itens[:1024], inline=False)
    embed.add_field(name="🔥 Buffs Ativos", value=texto_buffs[:1024], inline=False)
    embed.set_footer(text="Família Sant's • Registro Amaldiçoado")
    return embed


async def executar_compra_amaldicoada(interaction: discord.Interaction, codigo: str):
    item = LOJA_AMALDICOADA.get(codigo)
    if not item:
        await enviar_ephemeral(interaction, "❌ Item não encontrado.")
        return

    saldo = quantidade_item(interaction.user.id, ITEM_FRAGMENTO)
    preco = item["preco"]
    corrupcao_atual = pegar_corrupcao(interaction.user.id)
    requisito = item.get("requer_corrupcao")

    if requisito is not None and corrupcao_atual < requisito:
        await enviar_ephemeral(interaction, embed=discord.Embed(title="🔒 Mercado Secreto Bloqueado", description=f"Este item exige corrupção mínima de **{requisito}**.\nSua corrupção atual: **{corrupcao_atual}**.", color=COR_VERMELHA))
        return

    if saldo < preco:
        await enviar_ephemeral(interaction, embed=discord.Embed(title="❌ Fragmentos insuficientes", description=f"Necessário: **{preco}**\nVocê possui: **{saldo}**", color=COR_VERMELHA))
        return

    if not remover_item(interaction.user.id, ITEM_FRAGMENTO, preco):
        await enviar_ephemeral(interaction, "❌ Não foi possível concluir a compra.")
        return

    tipo = item["tipo"]
    corrupcao_ganha = item.get("corrupcao", 0)
    if corrupcao_ganha > 0:
        corrupcao_atual = adicionar_corrupcao(interaction.user.id, corrupcao_ganha)

    raridade = pegar_raridade(item)

    if tipo == "buff":
        adicionar_buff(interaction.user.id, item["buff"], item["quantidade"])
        desc = f"🔥 Buff: **{item['buff']} x{item['quantidade']}**\n🩸 Corrupção atual: **{corrupcao_atual}**"
    elif tipo == "multi_buff":
        for buff in item["buffs"]:
            adicionar_buff(interaction.user.id, buff["buff"], buff["quantidade"])
        desc = "\n".join([f"• **{b['buff']}** x{b['quantidade']}" for b in item["buffs"]]) + f"\n\n🩸 Corrupção atual: **{corrupcao_atual}**"
    elif tipo == "cura_buff":
        if not restaurar_vida_total(interaction.user.id):
            adicionar_item(interaction.user.id, ITEM_FRAGMENTO, preco)
            await enviar_ephemeral(interaction, "❌ Você não está registrado no Jogo do Abate. Fragmentos devolvidos.")
            return
        adicionar_buff(interaction.user.id, item["buff"], item["quantidade"])
        desc = f"❤️ Vida restaurada para **{VIDAS_MAXIMAS}/{VIDAS_MAXIMAS}**\nBuff: **{item['buff']} x{item['quantidade']}**\n🩸 Corrupção atual: **{corrupcao_atual}**"
    elif tipo == "purificar_buff":
        corrupcao_atual = reduzir_corrupcao(interaction.user.id, item["valor"])
        adicionar_buff(interaction.user.id, item["buff"], item["quantidade"])
        desc = f"🩸 Corrupção atual: {barra_corrupcao(corrupcao_atual)}\nBuff: **{item['buff']} x{item['quantidade']}**"
    elif tipo == "reliquia_buff":
        salvar_reliquia(interaction.user.id, item["reliquia"])
        adicionar_buff(interaction.user.id, item["buff"], item["quantidade"])
        desc = f"🌑 Relíquia equipada: **{item['reliquia']}**\nBuff: **{item['buff']} x{item['quantidade']}**\n🩸 Corrupção atual: **{corrupcao_atual}**"
    elif tipo == "reliquia_multi":
        salvar_reliquia(interaction.user.id, item["reliquia"])
        for buff in item["buffs"]:
            adicionar_buff(interaction.user.id, buff["buff"], buff["quantidade"])
        desc = f"🌑 Relíquia equipada: **{item['reliquia']}**\n" + "\n".join([f"• **{b['buff']}** x{b['quantidade']}" for b in item["buffs"]]) + f"\n\n🩸 Corrupção atual: **{corrupcao_atual}**"
    else:
        desc = "Compra concluída."

    embed = discord.Embed(title=f"{item['emoji']} Compra concluída", description=f"**{item['nome']}** foi absorvido.\n\n{desc}", color=raridade["cor"])
    embed.set_footer(text="Família Sant's • Mercado Amaldiçoado")
    await enviar_ephemeral(interaction, embed=embed)


class ConfirmarCompraAmaldicoadaView(discord.ui.View):
    def __init__(self, codigo: str):
        super().__init__(timeout=60)
        self.codigo = codigo

    @discord.ui.button(label="Confirmar", emoji="✅", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await executar_compra_amaldicoada(interaction, self.codigo)

    @discord.ui.button(label="Cancelar", emoji="❌", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await enviar_ephemeral(interaction, embed=discord.Embed(title="❌ Compra cancelada", description="Nenhum fragmento foi gasto.", color=COR_VERMELHA))


class BotaoItemAmaldicoado(discord.ui.Button):
    def __init__(self, codigo: str, item: dict):
        style = discord.ButtonStyle.danger if item["categoria"] in ["poder", "reliquias", "secreto"] else discord.ButtonStyle.secondary
        if item["categoria"] == "defesa":
            style = discord.ButtonStyle.success
        super().__init__(label=item["nome"][:80], emoji=item["emoji"], style=style)
        self.codigo = codigo
        self.item = item

    async def callback(self, interaction: discord.Interaction):
        await enviar_ephemeral(interaction, embed=criar_embed_item(self.codigo, self.item, interaction.user), view=ConfirmarCompraAmaldicoadaView(self.codigo))


class CategoriaAmaldicoadaView(discord.ui.View):
    def __init__(self, categoria: str, user_id: int):
        super().__init__(timeout=120)
        corrupcao = pegar_corrupcao(user_id)
        for codigo, item in list(itens_por_categoria(categoria).items())[:20]:
            requisito = item.get("requer_corrupcao")
            if requisito is not None and corrupcao < requisito:
                continue
            self.add_item(BotaoItemAmaldicoado(codigo, item))


class LojaAmaldicoadaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def abrir_categoria(self, interaction: discord.Interaction, categoria: str):
        await enviar_ephemeral(interaction, embed=criar_embed_categoria(categoria, interaction.user.id), view=CategoriaAmaldicoadaView(categoria, interaction.user.id))

    @discord.ui.button(label="Poder", emoji="🔥", style=discord.ButtonStyle.danger, custom_id="amal_poder_v1", row=0)
    async def poder(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_categoria(interaction, "poder")

    @discord.ui.button(label="Defesa", emoji="🛡️", style=discord.ButtonStyle.success, custom_id="amal_defesa_v1", row=0)
    async def defesa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_categoria(interaction, "defesa")

    @discord.ui.button(label="Relíquias", emoji="☠️", style=discord.ButtonStyle.danger, custom_id="amal_reliquias_v1", row=0)
    async def reliquias(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_categoria(interaction, "reliquias")

    @discord.ui.button(label="Rituais", emoji="📜", style=discord.ButtonStyle.primary, custom_id="amal_rituais_v1", row=1)
    async def rituais(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_categoria(interaction, "rituais")

    @discord.ui.button(label="Secreto", emoji="🌑", style=discord.ButtonStyle.secondary, custom_id="amal_secreto_v1", row=1)
    async def secreto(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_categoria(interaction, "secreto")

    @discord.ui.button(label="Registro", emoji="🎒", style=discord.ButtonStyle.secondary, custom_id="amal_registro_v1", row=1)
    async def registro(self, interaction: discord.Interaction, button: discord.ui.Button):
        await enviar_ephemeral(interaction, embed=criar_embed_inventario(interaction.user))


class MercadoAmaldicoado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        criar_tabelas_economia()
        criar_tabelas_amaldicoadas()

    @commands.command(name="painel_loja")
    @commands.has_permissions(administrator=True)
    async def painel_loja(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.send(embed=criar_embed_loja(), view=LojaAmaldicoadaView())

    @commands.command(name="loja")
    async def loja(self, ctx):
        await ctx.send(embed=criar_embed_loja(), view=LojaAmaldicoadaView())

    @commands.command(name="inv", aliases=["inventario"])
    async def inventario(self, ctx, membro: discord.Member = None):
        membro = membro or ctx.author
        await ctx.send(embed=criar_embed_inventario(membro))

    @commands.command(name="comprar")
    async def comprar(self, ctx, codigo: str = None):
        if not codigo:
            codigos = ", ".join([f"`{c}`" for c in LOJA_AMALDICOADA.keys()])
            await ctx.reply(f"❌ Use `!comprar <código>`.\n\n{codigos}")
            return
        codigo = codigo.lower().strip()
        if codigo not in LOJA_AMALDICOADA:
            await ctx.reply("❌ Item não encontrado. Use `!loja`.")
            return

        class RespostaManual:
            def is_done(self):
                return False
            async def send_message(self, content=None, embed=None, ephemeral=False, view=None):
                await ctx.reply(content or "", embed=embed)

        class InteracaoManual:
            user = ctx.author
            response = RespostaManual()
            class Followup:
                async def send(self, content=None, embed=None, view=None, ephemeral=False):
                    await ctx.reply(content or "", embed=embed)
            followup = Followup()

        await executar_compra_amaldicoada(InteracaoManual(), codigo)

    @commands.command(name="reliquia")
    async def reliquia(self, ctx, membro: discord.Member = None):
        membro = membro or ctx.author
        reliquia = pegar_reliquia(membro.id) or "Nenhuma relíquia equipada"
        await ctx.reply(f"🌑 Relíquia de {membro.mention}: **{reliquia}**")

    @commands.command(name="corrupcao")
    async def corrupcao(self, ctx, membro: discord.Member = None):
        membro = membro or ctx.author
        valor = pegar_corrupcao(membro.id)
        await ctx.reply(f"🩸 Corrupção de {membro.mention}:\n{barra_corrupcao(valor)}\n☠️ Classe: {classe_amaldicoada(valor)}")

    @painel_loja.error
    async def painel_loja_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ Apenas administradores podem criar o painel da loja.", delete_after=8)
        else:
            await ctx.reply("⚠️ Ocorreu um erro ao criar o painel da loja.", delete_after=8)
            print(f"[ERRO PAINEL LOJA] {error}")


async def setup(bot):
    bot.add_view(LojaAmaldicoadaView())
    await bot.add_cog(MercadoAmaldicoado(bot))
