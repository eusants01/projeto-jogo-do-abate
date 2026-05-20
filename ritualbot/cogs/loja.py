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


# =========================
# CONFIGURAÇÕES VISUAIS
# =========================

COR_ROXA = 0x6A00FF
COR_ROXA_ESCURO = 0x2B0057
COR_VERDE = 0x2ECC71
COR_VERMELHA = 0xE63946
COR_DOURADA = 0xF1C40F
COR_PRETA = 0x090909
COR_AZUL = 0x3498DB

VIDAS_MAXIMAS = 750

ITEM_FRAGMENTO = "Fragmento Amaldiçoado"

BANNER_LOJA = "https://cdn.discordapp.com/attachments/961677475191078992/1506544174059491409/content.png?ex=6a0ea619&is=6a0d5499&hm=772c937612494c96511043a17468745e2245b6f8e2dd6faa00d4fde920b20cad&"

NOME_LOJA = "Mercado Amaldiçoado"


# =========================
# RARIDADES
# =========================

RARIDADES = {
    "comum": {
        "nome": "Comum",
        "emoji": "🟢",
        "cor": 0x95A5A6,
    },
    "raro": {
        "nome": "Raro",
        "emoji": "🟣",
        "cor": COR_ROXA,
    },
    "epico": {
        "nome": "Épico",
        "emoji": "🔴",
        "cor": COR_VERMELHA,
    },
    "lendario": {
        "nome": "Lendário",
        "emoji": "🟡",
        "cor": COR_DOURADA,
    },
    "proibido": {
        "nome": "Proibido",
        "emoji": "☠️",
        "cor": COR_PRETA,
    },
}


# =========================
# ITENS DA LOJA
# =========================

LOJA = {
    # =====================
    # DEFESA
    # =====================
    "cura": {
        "nome": "Cura Reversa",
        "emoji": "❤️",
        "categoria": "defesa",
        "descricao": "Restaura sua vida completamente no Jogo do Abate.",
        "lore": "Uma técnica reversa instável capaz de restaurar o corpo antes da queda final.",
        "preco": 75,
        "tipo": "cura",
        "valor": VIDAS_MAXIMAS,
        "raridade": "raro",
    },
    "escudo": {
        "nome": "Talismã de Proteção",
        "emoji": "🛡️",
        "categoria": "defesa",
        "descricao": "Reduz o próximo dano recebido em maldição ou boss.",
        "lore": "Um selo defensivo simples, mas eficiente contra energia amaldiçoada.",
        "preco": 50,
        "tipo": "buff",
        "buff": "escudo",
        "quantidade": 1,
        "raridade": "comum",
    },
    "barreira": {
        "nome": "Barreira Amaldiçoada",
        "emoji": "🔷",
        "categoria": "defesa",
        "descricao": "Recebe 3 cargas de escudo.",
        "lore": "Uma barreira condensada capaz de resistir a múltiplos impactos.",
        "preco": 140,
        "tipo": "buff",
        "buff": "escudo",
        "quantidade": 3,
        "raridade": "epico",
    },
    "dominio_reverso": {
        "nome": "Domínio Reverso",
        "emoji": "🌀",
        "categoria": "defesa",
        "descricao": "Recebe 5 cargas de escudo.",
        "lore": "Uma proteção rara usada apenas por feiticeiros que dominam energia reversa.",
        "preco": 260,
        "tipo": "buff",
        "buff": "escudo",
        "quantidade": 5,
        "raridade": "lendario",
    },

    # =====================
    # ATAQUE
    # =====================
    "furia": {
        "nome": "Fúria Amaldiçoada",
        "emoji": "🔥",
        "categoria": "ataque",
        "descricao": "Aumenta o dano do próximo ataque no boss.",
        "lore": "Sua energia explode por alguns segundos, aumentando o impacto do próximo golpe.",
        "preco": 90,
        "tipo": "buff",
        "buff": "furia",
        "quantidade": 1,
        "raridade": "raro",
    },
    "critico": {
        "nome": "Golpe Crítico",
        "emoji": "💥",
        "categoria": "ataque",
        "descricao": "Dobra o dano do próximo ataque no boss.",
        "lore": "Um golpe concentrado em um ponto vital da maldição.",
        "preco": 160,
        "tipo": "buff",
        "buff": "critico",
        "quantidade": 1,
        "raridade": "epico",
    },
    "berserk": {
        "nome": "Berserk Amaldiçoado",
        "emoji": "☠️",
        "categoria": "ataque",
        "descricao": "Grande dano extra no boss.",
        "lore": "Uma técnica perigosa que troca controle por poder bruto.",
        "preco": 220,
        "tipo": "buff",
        "buff": "berserk",
        "quantidade": 1,
        "raridade": "lendario",
    },
    "colapso_negro": {
        "nome": "Colapso Negro",
        "emoji": "⚫",
        "categoria": "ataque",
        "descricao": "Recebe 2 cargas de crítico.",
        "lore": "Um impacto distorcido entre espaço, força e energia amaldiçoada.",
        "preco": 310,
        "tipo": "buff",
        "buff": "critico",
        "quantidade": 2,
        "raridade": "lendario",
    },

    # =====================
    # SORTE
    # =====================
    "sorte": {
        "nome": "Amuleto de Sorte",
        "emoji": "🍀",
        "categoria": "sorte",
        "descricao": "Melhora a próxima tentativa ou drop de maldição.",
        "lore": "Um pequeno amuleto usado por caçadores antes de enfrentar o desconhecido.",
        "preco": 120,
        "tipo": "buff",
        "buff": "sorte",
        "quantidade": 1,
        "raridade": "raro",
    },
    "sorte_maior": {
        "nome": "Benção da Sorte",
        "emoji": "🌟",
        "categoria": "sorte",
        "descricao": "Recebe 3 cargas de sorte.",
        "lore": "Uma bênção rara capaz de alterar discretamente o destino.",
        "preco": 300,
        "tipo": "buff",
        "buff": "sorte",
        "quantidade": 3,
        "raridade": "lendario",
    },
    "olho_destino": {
        "nome": "Olho do Destino",
        "emoji": "👁️",
        "categoria": "sorte",
        "descricao": "Recebe 5 cargas de sorte.",
        "lore": "Dizem que este olho enxerga recompensas antes mesmo delas existirem.",
        "preco": 450,
        "tipo": "buff",
        "buff": "sorte",
        "quantidade": 5,
        "raridade": "proibido",
    },

    # =====================
    # CORRUPÇÃO
    # =====================
    "purificar": {
        "nome": "Purificação",
        "emoji": "🧿",
        "categoria": "corrupcao",
        "descricao": "Remove 5 pontos de corrupção.",
        "lore": "Um ritual simples para limpar pequenas marcas amaldiçoadas.",
        "preco": 35,
        "tipo": "purificar",
        "valor": 5,
        "raridade": "comum",
    },
    "purificar_maior": {
        "nome": "Purificação Maior",
        "emoji": "✨",
        "categoria": "corrupcao",
        "descricao": "Remove 15 pontos de corrupção.",
        "lore": "Um ritual mais forte, usado quando a alma já está próxima do limite.",
        "preco": 95,
        "tipo": "purificar",
        "valor": 15,
        "raridade": "raro",
    },
    "exorcismo_total": {
        "nome": "Exorcismo Total",
        "emoji": "🌕",
        "categoria": "corrupcao",
        "descricao": "Remove 40 pontos de corrupção.",
        "lore": "Um ritual avançado que separa a alma da energia contaminada.",
        "preco": 240,
        "tipo": "purificar",
        "valor": 40,
        "raridade": "lendario",
    },

    # =====================
    # PROIBIDOS
    # =====================
    "dedo_sukuna": {
        "nome": "Dedo de Sukuna",
        "emoji": "🩸",
        "categoria": "proibido",
        "descricao": "Recebe 3 cargas de berserk.",
        "lore": "Um artefato amaldiçoado que jamais deveria estar à venda.",
        "preco": 600,
        "tipo": "buff",
        "buff": "berserk",
        "quantidade": 3,
        "raridade": "proibido",
    },
    "roda_mahoraga": {
        "nome": "Roda da Adaptação",
        "emoji": "☸️",
        "categoria": "proibido",
        "descricao": "Recebe 4 cargas de escudo.",
        "lore": "A roda gira. A técnica se adapta. O inimigo perde vantagem.",
        "preco": 520,
        "tipo": "buff",
        "buff": "escudo",
        "quantidade": 4,
        "raridade": "proibido",
    },
}


CATEGORIAS = {
    "defesa": {
        "titulo": "🛡️ Defesa e Sobrevivência",
        "descricao": "Itens para resistir, recuperar vida e sobreviver por mais tempo.",
        "cor": COR_VERDE,
        "emoji": "🛡️",
    },
    "ataque": {
        "titulo": "🔥 Ataque e Dano",
        "descricao": "Buffs para causar mais dano em bosses e maldições.",
        "cor": COR_VERMELHA,
        "emoji": "🔥",
    },
    "sorte": {
        "titulo": "🍀 Sorte e Drops",
        "descricao": "Itens para melhorar tentativas, recompensas e drops.",
        "cor": COR_DOURADA,
        "emoji": "🍀",
    },
    "corrupcao": {
        "titulo": "🧿 Corrupção e Purificação",
        "descricao": "Controle sua corrupção antes que ela controle você.",
        "cor": COR_ROXA,
        "emoji": "🧿",
    },
    "proibido": {
        "titulo": "☠️ Itens Proibidos",
        "descricao": "Artefatos instáveis, raros e extremamente perigosos.",
        "cor": COR_PRETA,
        "emoji": "☠️",
    },
}


# =========================
# FUNÇÕES AUXILIARES
# =========================

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
        for codigo, item in LOJA.items()
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


def formatar_item(codigo: str, item: dict):
    raridade = pegar_raridade(item)

    return (
        f"{item['emoji']} **{item['nome']}**\n"
        f"{raridade['emoji']} `{raridade['nome']}` • 🧩 **{item['preco']} fragmentos**\n"
        f"╰ {item['descricao']}\n"
        f"╰ Código: `{codigo}`"
    )


def criar_embed_loja():
    embed = discord.Embed(
        title=f"🛒 {NOME_LOJA}",
        description=(
            "```ansi\n"
            "\u001b[35m╔══════════════════════════════╗\n"
            "\u001b[35m║      MERCADO AMALDIÇOADO     ║\n"
            "\u001b[35m╚══════════════════════════════╝\n"
            "```\n"
            "Fragmentos amaldiçoados circulam por este domínio.\n"
            "Aqui, cada item pode decidir quem sobrevive ao próximo confronto.\n\n"
            "🧩 **Moeda:** Fragmentos Amaldiçoados\n"
            "🩸 **Risco:** Corrupção elevada pode se tornar perigosa\n"
            "☠️ **Aviso:** itens proibidos não são para feiticeiros fracos\n\n"
            "Use os botões abaixo para navegar pela loja."
        ),
        color=COR_ROXA,
    )

    embed.add_field(
        name="🛡️ Defesa",
        value="Cura, escudos e barreiras.",
        inline=True,
    )
    embed.add_field(
        name="🔥 Ataque",
        value="Fúria, crítico e berserk.",
        inline=True,
    )
    embed.add_field(
        name="🍀 Sorte",
        value="Drops e tentativas melhores.",
        inline=True,
    )
    embed.add_field(
        name="🧿 Purificação",
        value="Redução de corrupção.",
        inline=True,
    )
    embed.add_field(
        name="☠️ Proibidos",
        value="Artefatos raros e perigosos.",
        inline=True,
    )
    embed.add_field(
        name="🎒 Inventário",
        value="Veja seus recursos e buffs.",
        inline=True,
    )

    embed.set_image(url=BANNER_LOJA)
    embed.set_footer(text="Família Sant's • Sistema de Economia Amaldiçoada")
    return embed


def criar_embed_categoria(categoria: str):
    dados = CATEGORIAS[categoria]
    itens = itens_por_categoria(categoria)

    embed = discord.Embed(
        title=dados["titulo"],
        description=(
            f"{dados['descricao']}\n\n"
            "Selecione um item nos botões abaixo para abrir a confirmação de compra.\n"
        ),
        color=dados["cor"],
    )

    for codigo, item in itens.items():
        embed.add_field(
            name=f"{item['emoji']} {item['nome']}",
            value=(
                f"{pegar_raridade(item)['emoji']} **{pegar_raridade(item)['nome']}**\n"
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

    embed = discord.Embed(
        title=f"{item['emoji']} {item['nome']}",
        description=(
            f"{raridade['emoji']} **Raridade:** `{raridade['nome']}`\n"
            f"🧩 **Preço:** `{item['preco']}` Fragmentos Amaldiçoados\n"
            f"💰 **Seu saldo:** `{saldo}` Fragmentos\n\n"
            f"**Efeito:**\n{item['descricao']}\n\n"
            f"**Lore:**\n*{item.get('lore', 'Nenhuma lore registrada.')}*"
        ),
        color=raridade["cor"],
    )

    if item["raridade"] == "proibido":
        embed.add_field(
            name="☠️ Aviso Proibido",
            value="Este item carrega energia instável. Use com responsabilidade dentro do domínio.",
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
        texto_itens = "\n".join(
            [f"• **{item}** x{qtd}" for item, qtd in itens]
        )

    texto_buffs = "Nenhum buff ativo."
    if buffs:
        texto_buffs = "\n".join(
            [f"• **{buff}** x{qtd}" for buff, qtd in buffs]
        )

    embed = discord.Embed(
        title=f"🎒 Inventário Amaldiçoado — {membro.display_name}",
        description=(
            f"🧩 **Fragmentos:** `{saldo}`\n"
            f"🩸 **Corrupção:** {barra_corrupcao(corrupcao)}"
        ),
        color=COR_ROXA,
    )

    embed.add_field(
        name="📦 Itens",
        value=texto_itens[:1024],
        inline=False,
    )

    embed.add_field(
        name="✨ Buffs Ativos",
        value=texto_buffs[:1024],
        inline=False,
    )

    embed.set_footer(text="Família Sant's • Inventário RPG")
    return embed


async def enviar_ephemeral(interaction: discord.Interaction, content=None, embed=None, view=None):
    if interaction.response.is_done():
        await interaction.followup.send(content=content, embed=embed, view=view, ephemeral=True)
    else:
        await interaction.response.send_message(content=content, embed=embed, view=view, ephemeral=True)


# =========================
# COMPRA
# =========================

async def executar_compra(interaction: discord.Interaction, codigo: str):
    item = LOJA.get(codigo)

    if not item:
        await enviar_ephemeral(interaction, "❌ Item não encontrado.")
        return

    saldo = quantidade_item(interaction.user.id, ITEM_FRAGMENTO)
    preco = item["preco"]

    if saldo < preco:
        embed = discord.Embed(
            title="❌ Fragmentos insuficientes",
            description=(
                f"Você tentou comprar {item['emoji']} **{item['nome']}**.\n\n"
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
            title="🧿 Purificação concluída",
            description=(
                f"Você usou **{item['nome']}**.\n\n"
                f"🩸 Corrupção atual:\n{barra_corrupcao(nova_corrupcao)}"
            ),
            color=COR_ROXA,
        )
        await enviar_ephemeral(interaction, embed=embed)
        return

    if tipo == "cura":
        if restaurar_vida_total(interaction.user.id):
            embed = discord.Embed(
                title="❤️ Técnica Reversa Ativada",
                description=(
                    "Sua vida foi completamente restaurada.\n\n"
                    f"❤️ Vida atual: `{VIDAS_MAXIMAS}/{VIDAS_MAXIMAS}`"
                ),
                color=COR_VERDE,
            )
            await enviar_ephemeral(interaction, embed=embed)
        else:
            adicionar_item(interaction.user.id, ITEM_FRAGMENTO, preco)

            embed = discord.Embed(
                title="❌ Compra cancelada",
                description=(
                    "Você não está registrado no **Jogo do Abate**.\n\n"
                    "Seus fragmentos foram devolvidos."
                ),
                color=COR_VERMELHA,
            )
            await enviar_ephemeral(interaction, embed=embed)
        return

    if tipo == "buff":
        adicionar_buff(interaction.user.id, item["buff"], item["quantidade"])

        raridade = pegar_raridade(item)

        embed = discord.Embed(
            title="✨ Item adquirido",
            description=(
                f"{item['emoji']} **{item['nome']}** foi adicionado ao seu domínio.\n\n"
                f"{raridade['emoji']} Raridade: **{raridade['nome']}**\n"
                f"📦 Quantidade: **x{item['quantidade']}**\n"
                f"🧩 Fragmentos gastos: **{preco}**"
            ),
            color=raridade["cor"],
        )

        if item["raridade"] == "proibido":
            embed.add_field(
                name="☠️ Energia Proibida Detectada",
                value="A presença deste item foi registrada dentro do domínio.",
                inline=False,
            )

        await enviar_ephemeral(interaction, embed=embed)
        return


# =========================
# VIEWS
# =========================

class ConfirmarCompraView(discord.ui.View):
    def __init__(self, codigo: str):
        super().__init__(timeout=60)
        self.codigo = codigo

    @discord.ui.button(label="Confirmar Compra", emoji="✅", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await executar_compra(interaction, self.codigo)

    @discord.ui.button(label="Cancelar", emoji="❌", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❌ Compra cancelada",
            description="Nenhum fragmento foi gasto.",
            color=COR_VERMELHA,
        )
        await enviar_ephemeral(interaction, embed=embed)


class BotaoItem(discord.ui.Button):
    def __init__(self, codigo: str, item: dict):
        raridade = item.get("raridade", "comum")

        style = discord.ButtonStyle.secondary

        if raridade == "lendario":
            style = discord.ButtonStyle.primary
        elif raridade == "proibido":
            style = discord.ButtonStyle.danger
        elif item["categoria"] == "defesa":
            style = discord.ButtonStyle.success

        super().__init__(
            label=item["nome"][:80],
            emoji=item["emoji"],
            style=style,
        )

        self.codigo = codigo
        self.item = item

    async def callback(self, interaction: discord.Interaction):
        embed = criar_embed_item(self.codigo, self.item, interaction.user)
        await enviar_ephemeral(
            interaction,
            embed=embed,
            view=ConfirmarCompraView(self.codigo)
        )


class CategoriaView(discord.ui.View):
    def __init__(self, categoria: str):
        super().__init__(timeout=120)

        itens = list(itens_por_categoria(categoria).items())

        for codigo, item in itens[:20]:
            self.add_item(BotaoItem(codigo, item))


class LojaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def abrir_categoria(self, interaction: discord.Interaction, categoria: str):
        embed = criar_embed_categoria(categoria)
        await enviar_ephemeral(
            interaction,
            embed=embed,
            view=CategoriaView(categoria)
        )

    @discord.ui.button(label="Defesa", emoji="🛡️", style=discord.ButtonStyle.success, custom_id="loja_defesa_v3", row=0)
    async def defesa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_categoria(interaction, "defesa")

    @discord.ui.button(label="Ataque", emoji="🔥", style=discord.ButtonStyle.danger, custom_id="loja_ataque_v3", row=0)
    async def ataque(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_categoria(interaction, "ataque")

    @discord.ui.button(label="Sorte", emoji="🍀", style=discord.ButtonStyle.primary, custom_id="loja_sorte_v3", row=0)
    async def sorte(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_categoria(interaction, "sorte")

    @discord.ui.button(label="Purificação", emoji="🧿", style=discord.ButtonStyle.primary, custom_id="loja_corrupcao_v3", row=1)
    async def corrupcao(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_categoria(interaction, "corrupcao")

    @discord.ui.button(label="Proibidos", emoji="☠️", style=discord.ButtonStyle.danger, custom_id="loja_proibidos_v3", row=1)
    async def proibidos(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.abrir_categoria(interaction, "proibido")

    @discord.ui.button(label="Inventário", emoji="🎒", style=discord.ButtonStyle.secondary, custom_id="loja_inventario_v3", row=1)
    async def inventario(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = criar_embed_inventario(interaction.user)
        await enviar_ephemeral(interaction, embed=embed)


# =========================
# COG
# =========================

class Loja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        criar_tabelas_economia()

    @commands.command(name="painel_loja")
    @commands.has_permissions(administrator=True)
    async def painel_loja(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        await ctx.send(
            embed=criar_embed_loja(),
            view=LojaView()
        )

    @commands.command(name="loja")
    async def loja(self, ctx):
        await ctx.send(
            embed=criar_embed_loja(),
            view=LojaView()
        )

    @commands.command(name="inventario", aliases=["inv"])
    async def inventario(self, ctx, membro: discord.Member = None):
        membro = membro or ctx.author
        embed = criar_embed_inventario(membro)
        await ctx.send(embed=embed)

    @commands.command(name="comprar")
    async def comprar(self, ctx, codigo: str = None):
        if not codigo:
            codigos = ", ".join([f"`{codigo}`" for codigo in LOJA.keys()])
            await ctx.reply(
                f"❌ Use `!comprar <código>`.\n\nCódigos disponíveis:\n{codigos}"
            )
            return

        codigo = codigo.lower().strip()

        if codigo not in LOJA:
            await ctx.reply("❌ Item não encontrado. Use `!loja` para ver as opções.")
            return

        item = LOJA[codigo]
        saldo = quantidade_item(ctx.author.id, ITEM_FRAGMENTO)

        if saldo < item["preco"]:
            await ctx.reply(
                f"❌ Fragmentos insuficientes.\n\n"
                f"🧩 Necessário: **{item['preco']}**\n"
                f"🧩 Você possui: **{saldo}**"
            )
            return

        class RespostaManual:
            async def send_message(self, content=None, embed=None, ephemeral=False, view=None):
                await ctx.reply(content or "", embed=embed)

            async def is_done(self):
                return False

        class InteracaoManual:
            user = ctx.author
            response = RespostaManual()

            class Followup:
                async def send(self, content=None, embed=None, view=None, ephemeral=False):
                    await ctx.reply(content or "", embed=embed)

            followup = Followup()

        await executar_compra(InteracaoManual(), codigo)

    @painel_loja.error
    async def painel_loja_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply(
                "❌ Apenas administradores podem criar o painel da loja.",
                delete_after=8
            )
        else:
            await ctx.reply(
                "⚠️ Ocorreu um erro ao criar o painel da loja.",
                delete_after=8
            )
            print(f"[ERRO PAINEL LOJA] {error}")


async def setup(bot):
    bot.add_view(LojaView())
    await bot.add_cog(Loja(bot))