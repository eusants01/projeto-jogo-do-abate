# =========================================
# LOJA DOS FEITICEIROS — NÍVEL PRO
# Família Sant's
# =========================================

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

# =========================================
# CONFIGURAÇÕES
# =========================================

VIDAS_MAXIMAS = 750
ITEM_FRAGMENTO = "Fragmento Amaldiçoado"

NOME_LOJA = "Mercado dos Feiticeiros"

BANNER_FEITICEIROS = "https://cdn.discordapp.com/attachments/961677475191078992/1506549974622666813/content.png?ex=6a0f5440&is=6a0e02c0&hm=722e6468b6a94330e0b2a3d910cc6443a6618246a303fdc65b351d476ce7f5c6&"

COR_AZUL = 0x3498DB
COR_AZUL_CLARO = 0x5DADE2
COR_DOURADA = 0xF1C40F
COR_BRANCA = 0xECF0F1
COR_VERDE = 0x2ECC71
COR_VERMELHA = 0xE63946
COR_ROXA = 0x6A00FF
COR_PRETA = 0x111111

# =========================================
# RARIDADES
# =========================================

RARIDADES = {
    "comum": {"nome": "Comum", "emoji": "⚪", "cor": COR_BRANCA},
    "raro": {"nome": "Raro", "emoji": "🔵", "cor": COR_AZUL},
    "epico": {"nome": "Épico", "emoji": "🟣", "cor": COR_ROXA},
    "lendario": {"nome": "Lendário", "emoji": "🟡", "cor": COR_DOURADA},
    "classe_s": {"nome": "Classe Especial", "emoji": "👑", "cor": COR_DOURADA},
}

# =========================================
# ITENS
# =========================================

LOJA_FEITICEIROS = {

    # =========================================
    # TÉCNICAS
    # =========================================

    "seis_olhos": {
        "nome": "Seis Olhos",
        "emoji": "👁️",
        "categoria": "tecnica",
        "descricao": "+6 sorte e bônus contra bosses.",
        "lore": "A técnica suprema de percepção.",
        "preco": 850,
        "tipo": "buff",
        "buff": "sorte",
        "quantidade": 6,
        "raridade": "classe_s",
    },

    "black_flash": {
        "nome": "Black Flash",
        "emoji": "⚫",
        "categoria": "tecnica",
        "descricao": "+4 crítico.",
        "lore": "Uma distorção espacial gerada em milésimos.",
        "preco": 720,
        "tipo": "buff",
        "buff": "critico",
        "quantidade": 4,
        "raridade": "lendario",
    },

    "manipulacao_sangue": {
        "nome": "Manipulação de Sangue",
        "emoji": "🩸",
        "categoria": "tecnica",
        "descricao": "+3 fúria.",
        "lore": "Controle absoluto do sangue amaldiçoado.",
        "preco": 540,
        "tipo": "buff",
        "buff": "furia",
        "quantidade": 3,
        "raridade": "epico",
    },

    "dez_sombras": {
        "nome": "10 Sombras",
        "emoji": "🌑",
        "categoria": "tecnica",
        "descricao": "+2 crítico e +2 sorte.",
        "lore": "Uma técnica ancestral extremamente rara.",
        "preco": 900,
        "tipo": "multi_buff",
        "buffs": [
            {"buff": "critico", "quantidade": 2},
            {"buff": "sorte", "quantidade": 2},
        ],
        "raridade": "classe_s",
    },

    # =========================================
    # RELÍQUIAS
    # =========================================

    "roda_adaptacao": {
        "nome": "Roda da Adaptação",
        "emoji": "☸️",
        "categoria": "reliquia",
        "descricao": "+4 escudos.",
        "lore": "Mahoraga observa. Mahoraga aprende.",
        "preco": 780,
        "tipo": "buff",
        "buff": "escudo",
        "quantidade": 4,
        "raridade": "classe_s",
    },

    "dedo_sukuna": {
        "nome": "Dedo do Sukuna",
        "emoji": "☠️",
        "categoria": "reliquia",
        "descricao": "+5 fúria e +5 corrupção.",
        "lore": "Uma relíquia proibida.",
        "preco": 950,
        "tipo": "corrupcao_buff",
        "buff": "furia",
        "quantidade": 5,
        "corrupcao": 5,
        "raridade": "classe_s",
    },

    # =========================================
    # DEFESA
    # =========================================

    "infinito_defensivo": {
        "nome": "Infinito Defensivo",
        "emoji": "♾️",
        "categoria": "defesa",
        "descricao": "+7 escudos.",
        "lore": "O infinito entre você e o ataque.",
        "preco": 620,
        "tipo": "buff",
        "buff": "escudo",
        "quantidade": 7,
        "raridade": "classe_s",
    },

    # =========================================
    # ARMAS
    # =========================================

    "lanca_celestial": {
        "nome": "Lança Celestial",
        "emoji": "⚔️",
        "categoria": "armas",
        "descricao": "+3 crítico.",
        "lore": "Uma arma criada para destruir maldições.",
        "preco": 430,
        "tipo": "buff",
        "buff": "critico",
        "quantidade": 3,
        "raridade": "lendario",
    },

    # =========================================
    # SUPORTE
    # =========================================

    "tecnica_reversa": {
        "nome": "Técnica Reversa",
        "emoji": "❤️",
        "categoria": "suporte",
        "descricao": "Restaura toda sua vida.",
        "lore": "Uma técnica avançada de cura.",
        "preco": 120,
        "tipo": "cura",
        "valor": VIDAS_MAXIMAS,
        "raridade": "raro",
    },

    # =========================================
    # MERCADO SECRETO
    # =========================================

    "berserk_supremo": {
        "nome": "Berserk Supremo",
        "emoji": "🔥",
        "categoria": "mercado_secreto",
        "descricao": "+5 berserk.",
        "lore": "O caos absoluto.",
        "preco": 1300,
        "tipo": "buff",
        "buff": "berserk",
        "quantidade": 5,
        "raridade": "classe_s",
    },
}

# =========================================
# FUNÇÕES
# =========================================

def barra_corrupcao(valor: int):
    valor = max(0, min(valor, 100))
    preenchidos = valor // 10
    vazios = 10 - preenchidos

    return f"`{'█'*preenchidos}{'░'*vazios}` {valor}%"

def classe_feiticeiro(fragmentos: int):
    if fragmentos >= 3000:
        return "👑 Classe Especial"
    elif fragmentos >= 1500:
        return "💠 Elite"
    elif fragmentos >= 700:
        return "🔵 Avançado"
    return "⚪ Iniciante"

# =========================================
# EMBED PRINCIPAL
# =========================================

def criar_embed_loja():
    embed = discord.Embed(
        title="⚔️ Mercado dos Feiticeiros",
        description=(
            "```ansi\n"
            "╔══════════════════════════════╗\n"
            "║    MERCADO DOS FEITICEIROS   ║\n"
            "╚══════════════════════════════╝\n"
            "```\n"
            "Técnicas proibidas.\n"
            "Relíquias ancestrais.\n"
            "Armas ritualísticas.\n\n"
            "👁️ Apenas os feiticeiros mais fortes sobrevivem."
        ),
        color=COR_AZUL
    )

    embed.add_field(
        name="✨ Técnicas",
        value="Black Flash\nSeis Olhos\n10 Sombras",
        inline=True
    )

    embed.add_field(
        name="☠️ Relíquias",
        value="Dedo do Sukuna\nRoda da Adaptação",
        inline=True
    )

    embed.add_field(
        name="⚔️ Arsenal",
        value="Lança Celestial\nInfinito Defensivo",
        inline=True
    )

    embed.set_image(url=BANNER_FEITICEIROS)
    embed.set_footer(text="Família Sant's • Mercado dos Feiticeiros")

    return embed

# =========================================
# VIEW
# =========================================

class LojaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎒 Inventário", style=discord.ButtonStyle.secondary)
    async def inventario(self, interaction: discord.Interaction, button: discord.ui.Button):

        itens = pegar_inventario(interaction.user.id)
        buffs = pegar_buffs(interaction.user.id)
        corrupcao = pegar_corrupcao(interaction.user.id)
        fragmentos = quantidade_item(interaction.user.id, ITEM_FRAGMENTO)

        texto_itens = "Nenhum item."
        if itens:
            texto_itens = "\n".join(
                [f"• {nome} x{qtd}" for nome, qtd in itens]
            )

        texto_buffs = "Nenhum buff."
        if buffs:
            texto_buffs = "\n".join(
                [f"• {nome} x{qtd}" for nome, qtd in buffs]
            )

        embed = discord.Embed(
            title=f"🎒 Inventário — {interaction.user.display_name}",
            description=(
                f"🎖️ Classe: {classe_feiticeiro(fragmentos)}\n"
                f"🧩 Fragmentos: {fragmentos}\n"
                f"🩸 Corrupção:\n{barra_corrupcao(corrupcao)}"
            ),
            color=COR_AZUL
        )

        embed.add_field(
            name="📦 Itens",
            value=texto_itens[:1024],
            inline=False
        )

        embed.add_field(
            name="✨ Buffs",
            value=texto_buffs[:1024],
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

# =========================================
# COG
# =========================================

class LojaFeiticeiros(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        criar_tabelas_economia()

    @commands.command(name="feiticeiros")
    async def feiticeiros(self, ctx):

        try:
            await ctx.message.delete()
        except:
            pass

        embed = criar_embed_loja()

        await ctx.send(
            embed=embed,
            view=LojaView()
        )

async def setup(bot):
    await bot.add_cog(LojaFeiticeiros(bot))