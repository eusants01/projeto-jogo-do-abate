
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

COR_ROXA_JUJUTSU = 0x6A00FF
COR_VERDE = 0x2ECC71
COR_VERMELHA = 0xE63946
COR_DOURADA = 0xF1C40F

VIDAS_MAXIMAS = 750
ITEM_FRAGMENTO = "Fragmento Amaldiçoado"
BANNER_LOJA = "https://i.imgur.com/ypNuTwX.png"

LOJA = {
    "purificar": {
        "nome": "Purificação",
        "emoji": "🧿",
        "categoria": "corrupcao",
        "descricao": "Remove 5 pontos de corrupção.",
        "preco": 35,
        "tipo": "purificar",
        "valor": 5,
    },
    "purificar_maior": {
        "nome": "Purificação Maior",
        "emoji": "✨",
        "categoria": "corrupcao",
        "descricao": "Remove 15 pontos de corrupção.",
        "preco": 95,
        "tipo": "purificar",
        "valor": 15,
    },
    "cura": {
        "nome": "Cura Total",
        "emoji": "❤️",
        "categoria": "defesa",
        "descricao": "Restaura sua vida no Jogo do Abate.",
        "preco": 75,
        "tipo": "cura",
        "valor": VIDAS_MAXIMAS,
    },
    "escudo": {
        "nome": "Talismã de Proteção",
        "emoji": "🛡️",
        "categoria": "defesa",
        "descricao": "Reduz o próximo dano recebido em maldição/boss.",
        "preco": 50,
        "tipo": "buff",
        "buff": "escudo",
        "quantidade": 1,
    },
    "barreira": {
        "nome": "Barreira Amaldiçoada",
        "emoji": "🔷",
        "categoria": "defesa",
        "descricao": "Recebe 3 cargas de escudo.",
        "preco": 140,
        "tipo": "buff",
        "buff": "escudo",
        "quantidade": 3,
    },
    "furia": {
        "nome": "Fúria Amaldiçoada",
        "emoji": "🔥",
        "categoria": "ataque",
        "descricao": "Aumenta o dano do próximo ataque no boss.",
        "preco": 90,
        "tipo": "buff",
        "buff": "furia",
        "quantidade": 1,
    },
    "critico": {
        "nome": "Golpe Crítico",
        "emoji": "💥",
        "categoria": "ataque",
        "descricao": "Dobra o dano do próximo ataque no boss.",
        "preco": 160,
        "tipo": "buff",
        "buff": "critico",
        "quantidade": 1,
    },
    "berserk": {
        "nome": "Berserk Amaldiçoado",
        "emoji": "☠️",
        "categoria": "ataque",
        "descricao": "Grande dano extra no boss, mas causa dano de retorno.",
        "preco": 220,
        "tipo": "buff",
        "buff": "berserk",
        "quantidade": 1,
    },
    "sorte": {
        "nome": "Amuleto de Sorte",
        "emoji": "🍀",
        "categoria": "sorte",
        "descricao": "Melhora a próxima tentativa/drop de maldição.",
        "preco": 120,
        "tipo": "buff",
        "buff": "sorte",
        "quantidade": 1,
    },
    "sorte_maior": {
        "nome": "Benção da Sorte",
        "emoji": "🌟",
        "categoria": "sorte",
        "descricao": "Recebe 3 cargas de sorte.",
        "preco": 300,
        "tipo": "buff",
        "buff": "sorte",
        "quantidade": 3,
    },
}

CATEGORIAS = {
    "defesa": ("🛡️ Defesa e Sobrevivência", "Itens para reduzir dano, restaurar vida e permanecer vivo.", COR_VERDE),
    "ataque": ("🔥 Ataque e Dano", "Buffs para causar mais dano contra bosses.", COR_VERMELHA),
    "sorte": ("🍀 Sorte e Drops", "Itens para melhorar tentativas e recompensas.", COR_DOURADA),
    "corrupcao": ("🧿 Corrupção e Purificação", "Controle sua corrupção e evite penalidades.", COR_ROXA_JUJUTSU),
}


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
    return {codigo: item for codigo, item in LOJA.items() if item["categoria"] == categoria}


def texto_categoria(categoria: str):
    itens = itens_por_categoria(categoria)
    texto = ""

    for codigo, item in itens.items():
        texto += (
            f"{item['emoji']} **{item['nome']}** — 🧩 **{item['preco']}**\n"
            f"└ {item['descricao']}\n"
            f"└ Código: `{codigo}`\n\n"
        )

    return texto or "Nenhum item nesta categoria."


async def enviar_resposta_compra(interaction, texto: str):
    await interaction.response.send_message(texto, ephemeral=True)


async def executar_compra(interaction: discord.Interaction, codigo: str):
    item = LOJA.get(codigo)

    if not item:
        await enviar_resposta_compra(interaction, "❌ Item não encontrado.")
        return

    saldo = quantidade_item(interaction.user.id, ITEM_FRAGMENTO)
    preco = item["preco"]

    if saldo < preco:
        await enviar_resposta_compra(
            interaction,
            f"❌ Fragmentos insuficientes.\n\n🧩 Necessário: **{preco}**\n🧩 Você possui: **{saldo}**"
        )
        return

    if not remover_item(interaction.user.id, ITEM_FRAGMENTO, preco):
        await enviar_resposta_compra(interaction, "❌ Não foi possível concluir a compra.")
        return

    tipo = item["tipo"]

    if tipo == "purificar":
        nova_corrupcao = reduzir_corrupcao(interaction.user.id, item["valor"])
        await enviar_resposta_compra(
            interaction,
            f"🧿 **Purificação concluída!**\n\n🩸 Corrupção atual: **{nova_corrupcao}**"
        )
        return

    if tipo == "cura":
        if restaurar_vida_total(interaction.user.id):
            await enviar_resposta_compra(
                interaction,
                f"❤️ **Cura realizada com sucesso!**\n\nSua vida foi restaurada para `{VIDAS_MAXIMAS}/{VIDAS_MAXIMAS}`."
            )
        else:
            adicionar_item(interaction.user.id, ITEM_FRAGMENTO, preco)
            await enviar_resposta_compra(
                interaction,
                "❌ Você não está registrado no **Jogo do Abate**.\n\nSeus fragmentos foram devolvidos."
            )
        return

    if tipo == "buff":
        adicionar_buff(interaction.user.id, item["buff"], item["quantidade"])
        await enviar_resposta_compra(
            interaction,
            f"✨ **Compra concluída!**\n\nVocê recebeu: {item['emoji']} **{item['nome']}** x{item['quantidade']}"
        )
        return


class CategoriaSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Defesa e Sobrevivência", emoji="🛡️", value="defesa"),
            discord.SelectOption(label="Ataque e Dano", emoji="🔥", value="ataque"),
            discord.SelectOption(label="Sorte e Drops", emoji="🍀", value="sorte"),
            discord.SelectOption(label="Corrupção e Purificação", emoji="🧿", value="corrupcao"),
        ]
        super().__init__(
            placeholder="Escolha uma categoria da Loja Amaldiçoada...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="loja_categoria_select_v2"
        )

    async def callback(self, interaction: discord.Interaction):
        categoria = self.values[0]
        await enviar_categoria(interaction, categoria)


class BotaoComprar(discord.ui.Button):
    def __init__(self, codigo: str, item: dict):
        super().__init__(
            label=item["nome"][:80],
            emoji=item["emoji"],
            style=discord.ButtonStyle.primary,
        )
        self.codigo = codigo

    async def callback(self, interaction: discord.Interaction):
        await executar_compra(interaction, self.codigo)


class CompraCategoriaView(discord.ui.View):
    def __init__(self, categoria: str):
        super().__init__(timeout=120)
        itens = list(itens_por_categoria(categoria).items())[:5]
        for codigo, item in itens:
            self.add_item(BotaoComprar(codigo, item))


async def enviar_categoria(interaction: discord.Interaction, categoria: str):
    titulo, descricao, cor = CATEGORIAS[categoria]
    embed = discord.Embed(
        title=titulo,
        description=f"{descricao}\n\n{texto_categoria(categoria)}",
        color=cor
    )
    embed.set_footer(text="Família Sant's • Loja Amaldiçoada")
    await interaction.response.send_message(embed=embed, view=CompraCategoriaView(categoria), ephemeral=True)


class LojaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CategoriaSelect())

    async def mostrar_inventario(self, interaction: discord.Interaction):
        itens = pegar_inventario(interaction.user.id)
        buffs = pegar_buffs(interaction.user.id)
        corrupcao = pegar_corrupcao(interaction.user.id)
        saldo = quantidade_item(interaction.user.id, ITEM_FRAGMENTO)

        texto_itens = "Nenhum item."
        if itens:
            texto_itens = "\n".join([f"• **{item}** x{qtd}" for item, qtd in itens])

        texto_buffs = "Nenhum buff ativo."
        if buffs:
            texto_buffs = "\n".join([f"• **{buff}** x{qtd}" for buff, qtd in buffs])

        embed = discord.Embed(
            title="🎒 Seu Inventário Amaldiçoado",
            description=f"🧩 Fragmentos: **{saldo}**",
            color=COR_ROXA_JUJUTSU
        )
        embed.add_field(name="📦 Itens", value=texto_itens[:1024], inline=False)
        embed.add_field(name="✨ Buffs", value=texto_buffs[:1024], inline=False)
        embed.add_field(name="🩸 Corrupção", value=f"**{corrupcao}** ponto(s)", inline=False)
        embed.set_footer(text="Família Sant's • Inventário")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Ver Loja", emoji="🛒", style=discord.ButtonStyle.secondary, custom_id="loja_ver_v2", row=1)
    async def ver_loja(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=criar_embed_loja(), ephemeral=True)

    @discord.ui.button(label="Inventário", emoji="🎒", style=discord.ButtonStyle.secondary, custom_id="loja_inventario_v2", row=1)
    async def inventario_botao(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.mostrar_inventario(interaction)


def criar_embed_loja():
    embed = discord.Embed(
        title="🛒 Loja Amaldiçoada",
        description=(
            "Troque seus **Fragmentos Amaldiçoados** por itens, buffs e purificações.\n\n"
            "🧩 **Fragmentos** são obtidos derrotando maldições e participando de bosses.\n"
            "🩸 **Corrupção** aumenta ao falhar contra maldições.\n"
            "✨ **Buffs** ajudam em maldições e bosses.\n\n"
            "Use o menu abaixo para escolher uma categoria ou clique nos botões rápidos."
        ),
        color=COR_ROXA_JUJUTSU
    )
    embed.add_field(name="🛡️ Defesa", value="Cura, escudo e barreiras.", inline=True)
    embed.add_field(name="🔥 Ataque", value="Fúria, crítico e berserk.", inline=True)
    embed.add_field(name="🍀 Sorte", value="Melhore drops e tentativas.", inline=True)
    embed.add_field(name="🧿 Corrupção", value="Purificações e controle de risco.", inline=True)
    embed.set_image(url=BANNER_LOJA)
    embed.set_footer(text="Família Sant's • Loja Amaldiçoada")
    return embed


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
        await ctx.send(embed=criar_embed_loja(), view=LojaView())

    @commands.command(name="loja")
    async def loja(self, ctx):
        await ctx.send(embed=criar_embed_loja())

    @commands.command(name="inventario", aliases=["inv"])
    async def inventario(self, ctx, membro: discord.Member = None):
        membro = membro or ctx.author
        itens = pegar_inventario(membro.id)
        buffs = pegar_buffs(membro.id)
        corrupcao = pegar_corrupcao(membro.id)
        saldo = quantidade_item(membro.id, ITEM_FRAGMENTO)

        texto_itens = "Nenhum item."
        if itens:
            texto_itens = "\n".join([f"• **{item}** x{qtd}" for item, qtd in itens])

        texto_buffs = "Nenhum buff ativo."
        if buffs:
            texto_buffs = "\n".join([f"• **{buff}** x{qtd}" for buff, qtd in buffs])

        embed = discord.Embed(
            title=f"🎒 Inventário de {membro.display_name}",
            description=f"🧩 Fragmentos: **{saldo}**",
            color=COR_ROXA_JUJUTSU
        )
        embed.add_field(name="📦 Itens", value=texto_itens[:1024], inline=False)
        embed.add_field(name="✨ Buffs", value=texto_buffs[:1024], inline=False)
        embed.add_field(name="🩸 Corrupção", value=f"**{corrupcao}** ponto(s)", inline=False)
        embed.set_footer(text="Família Sant's • Inventário")
        await ctx.send(embed=embed)

    @commands.command(name="comprar")
    async def comprar(self, ctx, codigo: str = None):
        if not codigo:
            codigos = ", ".join([f"`{codigo}`" for codigo in LOJA.keys()])
            await ctx.reply(f"❌ Use `!comprar <código>`.\nCódigos: {codigos}")
            return

        codigo = codigo.lower().strip()

        if codigo not in LOJA:
            await ctx.reply("❌ Item não encontrado. Use `!loja` para ver as opções.")
            return

        class RespostaManual:
            async def send_message(self, content=None, embed=None, ephemeral=False):
                await ctx.reply(content or "", embed=embed)

        class InteracaoManual:
            user = ctx.author
            response = RespostaManual()

        await executar_compra(InteracaoManual(), codigo)

    @painel_loja.error
    async def painel_loja_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ Apenas administradores podem criar o painel da loja.", delete_after=8)
        else:
            await ctx.reply("⚠️ Ocorreu um erro ao criar o painel da loja.", delete_after=8)
            print(f"[ERRO PAINEL LOJA] {error}")


async def setup(bot):
    bot.add_view(LojaView())
    await bot.add_cog(Loja(bot))
