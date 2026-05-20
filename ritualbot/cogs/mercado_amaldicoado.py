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
)

from utils.db import buscar_jogador, conectar


# =====================================================
# CONFIGURAÇÕES
# =====================================================

VIDAS_MAXIMAS = 750
ITEM_FRAGMENTO = "Fragmento Amaldiçoado"

NOME_LOJA = "Mercado dos Feiticeiros"
BANNER_FEITICEIROS = "https://cdn.discordapp.com/attachments/961677475191078992/1506549974622666813/content.png?ex=6a0eab80&is=6a0d5a00&hm=48b8e598e9a422590deec4a97dcb2fce7ed7b81c19549b7334868f56c8deca02&COLOQUE_AQUI_O_LINK_DO_BANNER"

COR_AZUL = 0x3498DB
COR_AZUL_CLARO = 0x5DADE2
COR_DOURADA = 0xF1C40F
COR_BRANCA = 0xECF0F1
COR_VERDE = 0x2ECC71
COR_VERMELHA = 0xE63946
COR_ROXA = 0x6A00FF
COR_PRETA = 0x111111


# =====================================================
# RARIDADES
# =====================================================

RARIDADES = {
    "comum": {"nome": "Comum", "emoji": "⚪", "cor": COR_BRANCA},
    "raro": {"nome": "Raro", "emoji": "🔵", "cor": COR_AZUL},
    "epico": {"nome": "Épico", "emoji": "🟣", "cor": COR_ROXA},
    "lendario": {"nome": "Lendário", "emoji": "🟡", "cor": COR_DOURADA},
    "supremo": {"nome": "Supremo", "emoji": "👑", "cor": COR_DOURADA},
    "classe_s": {"nome": "Classe Especial", "emoji": "💠", "cor": COR_AZUL_CLARO},
}


# =====================================================
# ITENS
# =====================================================

LOJA_FEITICEIROS = {
    # DEFESA
    "selo_protecao": {
        "nome": "Selo de Proteção",
        "emoji": "🛡️",
        "categoria": "defesa",
        "descricao": "Recebe 1 carga de escudo.",
        "lore": "Um selo básico utilizado por feiticeiros em missões de risco.",
        "preco": 45,
        "tipo": "buff",
        "buff": "escudo",
        "quantidade": 1,
        "raridade": "comum",
    },
    "manto_exorcista": {
        "nome": "Manto Exorcista",
        "emoji": "🥋",
        "categoria": "defesa",
        "descricao": "Recebe 2 cargas de escudo.",
        "lore": "Um manto preparado para resistir a impactos de energia amaldiçoada.",
        "preco": 120,
        "tipo": "buff",
        "buff": "escudo",
        "quantidade": 2,
        "raridade": "raro",
    },
    "barreira_suprema": {
        "nome": "Barreira Suprema",
        "emoji": "🔷",
        "categoria": "defesa",
        "descricao": "Recebe 4 cargas de escudo.",
        "lore": "Uma barreira refinada usada por feiticeiros de elite.",
        "preco": 230,
        "tipo": "buff",
        "buff": "escudo",
        "quantidade": 4,
        "raridade": "epico",
    },
    "infinito_defensivo": {
        "nome": "Infinito Defensivo",
        "emoji": "♾️",
        "categoria": "defesa",
        "descricao": "Recebe 7 cargas de escudo.",
        "lore": "Uma defesa quase inalcançável. Poucos conseguem sustentar essa técnica.",
        "preco": 620,
        "tipo": "buff",
        "buff": "escudo",
        "quantidade": 7,
        "raridade": "classe_s",
    },

    # TÉCNICAS
    "fluxo_energia": {
        "nome": "Fluxo de Energia",
        "emoji": "✨",
        "categoria": "tecnica",
        "descricao": "Recebe 1 carga de fúria.",
        "lore": "Controle refinado da energia amaldiçoada para aumentar o próximo ataque.",
        "preco": 85,
        "tipo": "buff",
        "buff": "furia",
        "quantidade": 1,
        "raridade": "raro",
    },
    "amplificacao_tecnica": {
        "nome": "Amplificação de Técnica",
        "emoji": "💠",
        "categoria": "tecnica",
        "descricao": "Recebe 2 cargas de fúria.",
        "lore": "A energia do usuário é comprimida e liberada com precisão.",
        "preco": 190,
        "tipo": "buff",
        "buff": "furia",
        "quantidade": 2,
        "raridade": "epico",
    },
    "expansao_refinada": {
        "nome": "Expansão Refinada",
        "emoji": "🌀",
        "categoria": "tecnica",
        "descricao": "Recebe 2 cargas de fúria, 1 crítico e 1 sorte.",
        "lore": "Uma expansão estável, criada para dominar o campo sem cair na corrupção.",
        "preco": 520,
        "tipo": "multi_buff",
        "buffs": [
            {"buff": "furia", "quantidade": 2},
            {"buff": "critico", "quantidade": 1},
            {"buff": "sorte", "quantidade": 1},
        ],
        "raridade": "lendario",
    },
    "seis_olhos": {
        "nome": "Seis Olhos",
        "emoji": "👁️",
        "categoria": "tecnica",
        "descricao": "Recebe 6 cargas de sorte.",
        "lore": "Uma técnica raríssima capaz de enxergar o fluxo da energia com precisão absurda.",
        "preco": 750,
        "tipo": "buff",
        "buff": "sorte",
        "quantidade": 6,
        "raridade": "classe_s",
    },

    # ARMAS
    "katana_ritualistica": {
        "nome": "Katana Ritualística",
        "emoji": "🗡️",
        "categoria": "armas",
        "descricao": "Recebe 1 carga de crítico.",
        "lore": "Uma lâmina usada em exorcismos contra maldições resistentes.",
        "preco": 145,
        "tipo": "buff",
        "buff": "critico",
        "quantidade": 1,
        "raridade": "raro",
    },
    "corrente_exorcista": {
        "nome": "Corrente Exorcista",
        "emoji": "⛓️",
        "categoria": "armas",
        "descricao": "Recebe 2 cargas de crítico.",
        "lore": "Correntes preparadas para prender e enfraquecer entidades amaldiçoadas.",
        "preco": 260,
        "tipo": "buff",
        "buff": "critico",
        "quantidade": 2,
        "raridade": "epico",
    },
    "lanca_celestial": {
        "nome": "Lança Celestial",
        "emoji": "⚔️",
        "categoria": "armas",
        "descricao": "Recebe 3 cargas de crítico.",
        "lore": "Uma arma lendária forjada para perfurar defesas amaldiçoadas.",
        "preco": 430,
        "tipo": "buff",
        "buff": "critico",
        "quantidade": 3,
        "raridade": "lendario",
    },
    "arsenal_classe_especial": {
        "nome": "Arsenal Classe Especial",
        "emoji": "💎",
        "categoria": "armas",
        "descricao": "Recebe 2 críticos, 2 fúrias e 2 escudos.",
        "lore": "Um conjunto reservado apenas para feiticeiros de prestígio extremo.",
        "preco": 900,
        "tipo": "multi_buff",
        "buffs": [
            {"buff": "critico", "quantidade": 2},
            {"buff": "furia", "quantidade": 2},
            {"buff": "escudo", "quantidade": 2},
        ],
        "raridade": "classe_s",
    },

    # SELOS
    "selo_purificacao": {
        "nome": "Selo de Purificação",
        "emoji": "📜",
        "categoria": "selos",
        "descricao": "Remove 10 pontos de corrupção.",
        "lore": "Um selo simples para limpar resíduos amaldiçoados.",
        "preco": 70,
        "tipo": "purificar",
        "valor": 10,
        "raridade": "comum",
    },
    "selo_ancestral": {
        "nome": "Selo Ancestral",
        "emoji": "🧿",
        "categoria": "selos",
        "descricao": "Remove 25 pontos de corrupção.",
        "lore": "Um selo antigo preservado por gerações de feiticeiros.",
        "preco": 170,
        "tipo": "purificar",
        "valor": 25,
        "raridade": "epico",
    },
    "ritual_supremo": {
        "nome": "Ritual Supremo",
        "emoji": "🌕",
        "categoria": "selos",
        "descricao": "Remove 50 pontos de corrupção.",
        "lore": "Um ritual raro capaz de restaurar quase toda a estabilidade da alma.",
        "preco": 350,
        "tipo": "purificar",
        "valor": 50,
        "raridade": "lendario",
    },

    # SUPORTE
    "tecnica_reversa": {
        "nome": "Técnica Reversa",
        "emoji": "❤️",
        "categoria": "suporte",
        "descricao": "Restaura sua vida completamente no Jogo do Abate.",
        "lore": "Uma técnica refinada de cura usada por feiticeiros de alto nível.",
        "preco": 90,
        "tipo": "cura",
        "valor": VIDAS_MAXIMAS,
        "raridade": "raro",
    },
    "talisma_supremo": {
        "nome": "Talismã Supremo",
        "emoji": "📿",
        "categoria": "suporte",
        "descricao": "Recebe 2 escudos e 1 sorte.",
        "lore": "Combina proteção espiritual com controle preciso de energia.",
        "preco": 300,
        "tipo": "multi_buff",
        "buffs": [
            {"buff": "escudo", "quantidade": 2},
            {"buff": "sorte", "quantidade": 1},
        ],
        "raridade": "lendario",
    },
    "controle_absoluto": {
        "nome": "Controle Absoluto",
        "emoji": "💠",
        "categoria": "suporte",
        "descricao": "Recebe 2 sortes e remove 20 de corrupção.",
        "lore": "Uma preparação avançada para missões longas e confrontos decisivos.",
        "preco": 470,
        "tipo": "buff_purificar",
        "buff": "sorte",
        "quantidade": 2,
        "valor": 20,
        "raridade": "classe_s",
    },
}


CATEGORIAS = {
    "defesa": {
        "titulo": "🛡️ Defesa dos Feiticeiros",
        "descricao": "Proteções refinadas para sobreviver contra maldições poderosas.",
        "cor": COR_AZUL,
    },
    "tecnica": {
        "titulo": "✨ Técnicas Jujutsu",
        "descricao": "Técnicas de controle, precisão e domínio de energia.",
        "cor": COR_DOURADA,
    },
    "armas": {
        "titulo": "⚔️ Armas Ritualísticas",
        "descricao": "Ferramentas refinadas para exorcismo e combate direto.",
        "cor": COR_BRANCA,
    },
    "selos": {
        "titulo": "📜 Selos e Purificação",
        "descricao": "Rituais usados para reduzir corrupção e estabilizar a alma.",
        "cor": COR_ROXA,
    },
    "suporte": {
        "titulo": "❤️ Suporte e Preparação",
        "descricao": "Cura, suporte e fortalecimento antes do combate.",
        "cor": COR_VERDE,
    },
}


# =====================================================
# FUNÇÕES
# =====================================================

def restaurar_vida_total(user_id: int):
    jogador = buscar_jogador(user_id)

    if not jogador:
        return False

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE jogadores
        SET vidas = %s, status = 'vivo'
        WHERE user_id = %s
        """,
        (VIDAS_MAXIMAS, user_id)
    )
    conn.commit()
    conn.close()
    return True


def itens_por_categoria(categoria: str):
    return {
        codigo: item
        for codigo, item in LOJA_FEITICEIROS.items()
        if item["categoria"] == categoria
    }


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


def classe_do_feiticeiro(saldo: int, corrupcao: int):
    if saldo >= 1000 and corrupcao <= 20:
        return "👑 Classe Especial"
    if saldo >= 600:
        return "💠 Feiticeiro de Elite"
    if saldo >= 300:
        return "🔵 Feiticeiro Avançado"
    return "⚪ Feiticeiro Iniciante"


async def enviar_ephemeral(interaction: discord.Interaction, content=None, embed=None, view=None):
    if interaction.response.is_done():
        await interaction.followup.send(content=content, embed=embed, view=view, ephemeral=True)
    else:
        await interaction.response.send_message(content=content, embed=embed, view=view, ephemeral=True)


# =====================================================
# EMBEDS
# =====================================================

def criar_embed_loja_feiticeiros():
    embed = discord.Embed(
        title=f"⚔️ {NOME_LOJA}",
        description=(
            "```ansi\n"
            "\u001b[36m╔══════════════════════════════╗\n"
            "\u001b[36m║    MERCADO DOS FEITICEIROS   ║\n"
            "\u001b[36m╚══════════════════════════════╝\n"
            "```\n"
            "Técnicas refinadas. Selos protegidos. Armas ritualísticas.\n\n"
            "Este mercado não vende caos.\n"
            "Ele entrega **controle, prestígio e precisão**.\n\n"
            "🧩 **Moeda:** Fragmentos Amaldiçoados\n"
            "⚔️ **Foco:** defesa, técnica, armas, selos e suporte\n"
            "👑 **Prestígio:** itens Classe Especial para feiticeiros de elite\n\n"
            "Escolha uma categoria abaixo."
        ),
        color=COR_AZUL,
    )

    embed.add_field(name="🛡️ Defesa", value="Barreiras, mantos e proteção.", inline=True)
    embed.add_field(name="✨ Técnicas", value="Controle e amplificação.", inline=True)
    embed.add_field(name="⚔️ Armas", value="Ferramentas de exorcismo.", inline=True)
    embed.add_field(name="📜 Selos", value="Purificação e estabilidade.", inline=True)
    embed.add_field(name="❤️ Suporte", value="Cura e preparação.", inline=True)
    embed.add_field(name="🎒 Inventário", value="Status do feiticeiro.", inline=True)

    if BANNER_FEITICEIROS != "COLOQUE_AQUI_O_LINK_DO_BANNER":
        embed.set_image(url=BANNER_FEITICEIROS)

    embed.set_footer(text="Família Sant's • Mercado dos Feiticeiros")
    return embed


def criar_embed_categoria(categoria: str):
    dados = CATEGORIAS[categoria]
    itens = itens_por_categoria(categoria)

    embed = discord.Embed(
        title=dados["titulo"],
        description=(
            f"{dados['descricao']}\n\n"
            "Clique no item desejado para abrir a confirmação de compra."
        ),
        color=dados["cor"],
    )

    for codigo, item in itens.items():
        raridade = pegar_raridade(item)

        embed.add_field(
            name=f"{item['emoji']} {item['nome']}",
            value=(
                f"{raridade['emoji']} **{raridade['nome']}**\n"
                f"🧩 Preço: **{item['preco']}**\n"
                f"📜 {item['descricao']}\n"
                f"`{codigo}`"
            ),
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
            f"🎖️ **Classe atual:** {classe_do_feiticeiro(saldo, corrupcao)}\n\n"
            f"**Efeito:**\n{item['descricao']}\n\n"
            f"**Registro Jujutsu:**\n*{item.get('lore', 'Nenhuma informação registrada.')}*"
        ),
        color=raridade["cor"],
    )

    if item["raridade"] == "classe_s":
        embed.add_field(
            name="👑 Item Classe Especial",
            value="Este item representa o maior nível de prestígio do mercado.",
            inline=False,
        )

    embed.set_footer(text=f"Código do item: {codigo}")
    return embed


def criar_embed_inventario(membro: discord.Member | discord.User):
    itens = pegar_inventario(membro.id)
    buffs = pegar_buffs(membro.id)
    corrupcao = pegar_corrupcao(membro.id)
    saldo = quantidade_item(membro.id, ITEM_FRAGMENTO)

    texto_itens = "Nenhum item encontrado."
    if itens:
        texto_itens = "\n".join([f"• **{item}** x{qtd}" for item, qtd in itens])

    texto_buffs = "Nenhum buff ativo."
    if buffs:
        texto_buffs = "\n".join([f"• **{buff}** x{qtd}" for buff, qtd in buffs])

    embed = discord.Embed(
        title=f"🎒 Registro do Feiticeiro — {membro.display_name}",
        description=(
            f"🎖️ **Classe:** {classe_do_feiticeiro(saldo, corrupcao)}\n"
            f"🧩 **Fragmentos:** `{saldo}`\n"
            f"🩸 **Corrupção:** {barra_corrupcao(corrupcao)}"
        ),
        color=COR_AZUL,
    )

    embed.add_field(name="📦 Itens", value=texto_itens[:1024], inline=False)
    embed.add_field(name="✨ Técnicas/Buffs Ativos", value=texto_buffs[:1024], inline=False)
    embed.set_footer(text="Família Sant's • Registro dos Feiticeiros")
    return embed


# =====================================================
# COMPRA
# =====================================================

async def executar_compra_feiticeiro(interaction: discord.Interaction, codigo: str):
    item = LOJA_FEITICEIROS.get(codigo)

    if not item:
        await enviar_ephemeral(interaction, "❌ Item não encontrado.")
        return

    saldo = quantidade_item(interaction.user.id, ITEM_FRAGMENTO)
    preco = item["preco"]

    if saldo < preco:
        embed = discord.Embed(
            title="❌ Fragmentos insuficientes",
            description=(
                f"Você tentou adquirir {item['emoji']} **{item['nome']}**.\n\n"
                f"🧩 Necessário: **{preco}**\n"
                f"🧩 Você possui: **{saldo}**"
            ),
            color=COR_VERMELHA,
        )
        await enviar_ephemeral(interaction, embed=embed)
        return

    if not remover_item(interaction.user.id, ITEM_FRAGMENTO, preco):
        await enviar_ephemeral(interaction, "❌ Não foi possível concluir a compra.")
        return

    tipo = item["tipo"]

    if tipo == "purificar":
        nova_corrupcao = reduzir_corrupcao(interaction.user.id, item["valor"])

        embed = discord.Embed(
            title="📜 Selo ativado",
            description=(
                f"Você utilizou **{item['nome']}**.\n\n"
                f"🩸 Corrupção atual:\n{barra_corrupcao(nova_corrupcao)}"
            ),
            color=COR_ROXA,
        )
        await enviar_ephemeral(interaction, embed=embed)
        return

    if tipo == "cura":
        if restaurar_vida_total(interaction.user.id):
            embed = discord.Embed(
                title="❤️ Técnica Reversa Concluída",
                description=(
                    "Sua vida foi restaurada completamente.\n\n"
                    f"❤️ Vida atual: `{VIDAS_MAXIMAS}/{VIDAS_MAXIMAS}`"
                ),
                color=COR_VERDE,
            )
            await enviar_ephemeral(interaction, embed=embed)
        else:
            adicionar_item(interaction.user.id, ITEM_FRAGMENTO, preco)
            await enviar_ephemeral(
                interaction,
                "❌ Você não está registrado no **Jogo do Abate**.\nSeus fragmentos foram devolvidos."
            )
        return

    if tipo == "buff":
        adicionar_buff(interaction.user.id, item["buff"], item["quantidade"])
        raridade = pegar_raridade(item)

        embed = discord.Embed(
            title="✨ Técnica adquirida",
            description=(
                f"{item['emoji']} **{item['nome']}** foi registrado no seu domínio.\n\n"
                f"{raridade['emoji']} Raridade: **{raridade['nome']}**\n"
                f"📦 Quantidade: **x{item['quantidade']}**\n"
                f"🧩 Fragmentos gastos: **{preco}**"
            ),
            color=raridade["cor"],
        )
        await enviar_ephemeral(interaction, embed=embed)
        return

    if tipo == "multi_buff":
        for buff_data in item["buffs"]:
            adicionar_buff(interaction.user.id, buff_data["buff"], buff_data["quantidade"])

        buffs_texto = "\n".join(
            [f"• **{b['buff']}** x{b['quantidade']}" for b in item["buffs"]]
        )

        raridade = pegar_raridade(item)

        embed = discord.Embed(
            title="👑 Técnica composta ativada",
            description=(
                f"{item['emoji']} **{item['nome']}** foi ativado com sucesso.\n\n"
                f"{raridade['emoji']} Raridade: **{raridade['nome']}**\n"
                f"✨ Buffs recebidos:\n{buffs_texto}\n\n"
                f"🧩 Fragmentos gastos: **{preco}**"
            ),
            color=raridade["cor"],
        )
        await enviar_ephemeral(interaction, embed=embed)
        return

    if tipo == "buff_purificar":
        adicionar_buff(interaction.user.id, item["buff"], item["quantidade"])
        nova_corrupcao = reduzir_corrupcao(interaction.user.id, item["valor"])
        raridade = pegar_raridade(item)

        embed = discord.Embed(
            title="💠 Controle absoluto estabilizado",
            description=(
                f"{item['emoji']} **{item['nome']}** foi usado.\n\n"
                f"✨ Buff recebido: **{item['buff']} x{item['quantidade']}**\n"
                f"🩸 Corrupção atual:\n{barra_corrupcao(nova_corrupcao)}\n\n"
                f"🧩 Fragmentos gastos: **{preco}**"
            ),
            color=raridade["cor"],
        )
        await enviar_ephemeral(interaction, embed=embed)
        return


# =====================================================
# VIEWS
# =====================================================

class ConfirmarCompraFeiticeiroView(discord.ui.View):
    def __init__(self, codigo: str):
        super().__init__(timeout=60)
        self.codigo = codigo

    @discord.ui.button(label="Confirmar", emoji="✅", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await executar_compra_feiticeiro(interaction, self.codigo)

    @discord.ui.button(label="Cancelar", emoji="❌", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await enviar_ephemeral(
            interaction,
            embed=discord.Embed(
                title="❌ Compra cancelada",
                description="Nenhum fragmento foi gasto.",
                color=COR_VERMELHA,
            )
        )


class BotaoItemFeiticeiro(discord.ui.Button):
    def __init__(self, codigo: str, item: dict):
        raridade = item.get("raridade", "comum")
        style = discord.ButtonStyle.secondary

        if raridade in ["lendario", "supremo", "classe_s"]:
            style = discord.ButtonStyle.primary
        elif item["categoria"] == "defesa":
            style = discord.ButtonStyle.success
        elif item["categoria"] == "armas":
            style = discord.ButtonStyle.danger

        super().__init__(
            label=item["nome"][:80],
            emoji=item["emoji"],
            style=style,
        )

        self.codigo = codigo
        self.item = item

    async def callback(self, interaction: discord.Interaction):
        await enviar_ephemeral(
            interaction,
            embed=criar_embed_item(self.codigo, self.item, interaction.user),
            view=ConfirmarCompraFeiticeiroView(self.codigo)
        )


class CategoriaFeiticeiroView(discord.ui.View):
    def __init__(self, categoria: str):
        super().__init__(timeout=120)

        for codigo, item in list(itens_por_categoria(categoria).items())[:20]:
            self.add_item(BotaoItemFeiticeiro(codigo, item))


class LojaFeiticeirosView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def abrir_categoria(self, interaction: discord.Interaction, categoria: str):
        await enviar_ephemeral(
            interaction,
            embed=criar_embed_categoria(categoria),
            view=CategoriaFeiticeiroView(categoria)
        )

    @discord.ui.button(label="Defesa", emoji="🛡️", style=discord.ButtonStyle.success, custom_id="feiticeiros_defesa_v2", row=0)
    async def defesa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_categoria(interaction, "defesa")

    @discord.ui.button(label="Técnicas", emoji="✨", style=discord.ButtonStyle.primary, custom_id="feiticeiros_tecnicas_v2", row=0)
    async def tecnicas(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_categoria(interaction, "tecnica")

    @discord.ui.button(label="Armas", emoji="⚔️", style=discord.ButtonStyle.danger, custom_id="feiticeiros_armas_v2", row=0)
    async def armas(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_categoria(interaction, "armas")

    @discord.ui.button(label="Selos", emoji="📜", style=discord.ButtonStyle.secondary, custom_id="feiticeiros_selos_v2", row=1)
    async def selos(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_categoria(interaction, "selos")

    @discord.ui.button(label="Suporte", emoji="❤️", style=discord.ButtonStyle.success, custom_id="feiticeiros_suporte_v2", row=1)
    async def suporte(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_categoria(interaction, "suporte")

    @discord.ui.button(label="Registro", emoji="🎒", style=discord.ButtonStyle.secondary, custom_id="feiticeiros_registro_v2", row=1)
    async def inventario(self, interaction: discord.Interaction, button: discord.ui.Button):
        await enviar_ephemeral(interaction, embed=criar_embed_inventario(interaction.user))


# =====================================================
# COG
# =====================================================

class LojaFeiticeiros(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        criar_tabelas_economia()

    @commands.command(name="painel_feiticeiros")
    @commands.has_permissions(administrator=True)
    async def painel_feiticeiros(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        await ctx.send(
            embed=criar_embed_loja_feiticeiros(),
            view=LojaFeiticeirosView()
        )

    @commands.command(name="feiticeiros")
    async def feiticeiros(self, ctx):
        await ctx.send(
            embed=criar_embed_loja_feiticeiros(),
            view=LojaFeiticeirosView()
        )

    @commands.command(name="inv_feiticeiro")
    async def inv_feiticeiro(self, ctx, membro: discord.Member = None):
        membro = membro or ctx.author
        await ctx.send(embed=criar_embed_inventario(membro))

    @commands.command(name="comprar_feiticeiro")
    async def comprar_feiticeiro(self, ctx, codigo: str = None):
        if not codigo:
            codigos = ", ".join([f"`{c}`" for c in LOJA_FEITICEIROS.keys()])
            await ctx.reply(f"❌ Use `!comprar_feiticeiro <código>`.\n\n{codigos}")
            return

        codigo = codigo.lower().strip()

        if codigo not in LOJA_FEITICEIROS:
            await ctx.reply("❌ Item não encontrado. Use `!feiticeiros`.")
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

        await executar_compra_feiticeiro(InteracaoManual(), codigo)

    @painel_feiticeiros.error
    async def painel_feiticeiros_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ Apenas administradores podem criar o painel dos feiticeiros.", delete_after=8)
        else:
            await ctx.reply("⚠️ Ocorreu um erro ao criar o painel dos feiticeiros.", delete_after=8)
            print(f"[ERRO PAINEL FEITICEIROS] {error}")


async def setup(bot):
    bot.add_view(LojaFeiticeirosView())
    await bot.add_cog(LojaFeiticeiros(bot))