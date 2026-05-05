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

VIDAS_MAXIMAS = 750
ITEM_FRAGMENTO = "Fragmento Amaldiçoado"

BANNER_LOJA = "https://i.imgur.com/ypNuTwX.png"


LOJA = {
    "purificar": {
        "nome": "Purificação",
        "descricao": "Remove 5 pontos de corrupção.",
        "preco": 35,
        "tipo": "purificar",
        "valor": 5,
    },
    "cura": {
        "nome": "Cura Total",
        "descricao": "Restaura sua vida no Jogo do Abate.",
        "preco": 75,
        "tipo": "cura",
        "valor": VIDAS_MAXIMAS,
    },
    "escudo": {
        "nome": "Talismã de Proteção",
        "descricao": "Reduz o próximo dano recebido em maldição/boss.",
        "preco": 50,
        "tipo": "buff",
        "buff": "escudo",
        "quantidade": 1,
    },
    "furia": {
        "nome": "Fúria Amaldiçoada",
        "descricao": "Aumenta o dano do próximo ataque no boss.",
        "preco": 90,
        "tipo": "buff",
        "buff": "furia",
        "quantidade": 1,
    },
    "sorte": {
        "nome": "Amuleto de Sorte",
        "descricao": "Melhora a próxima tentativa/drop de maldição.",
        "preco": 120,
        "tipo": "buff",
        "buff": "sorte",
        "quantidade": 1,
    },
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


def texto_loja():
    return (
        "🧿 **Purificação** — 🧩 35 fragmentos\n"
        "Remove **5 pontos de corrupção**.\n\n"
        "❤️ **Cura Total** — 🧩 75 fragmentos\n"
        "Restaura sua vida no **Jogo do Abate**.\n\n"
        "🛡️ **Talismã de Proteção** — 🧩 50 fragmentos\n"
        "Reduz o próximo dano recebido.\n\n"
        "🔥 **Fúria Amaldiçoada** — 🧩 90 fragmentos\n"
        "Aumenta o dano do próximo ataque no boss.\n\n"
        "🍀 **Amuleto de Sorte** — 🧩 120 fragmentos\n"
        "Melhora a próxima tentativa/drop de maldição."
    )


class LojaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def mostrar_inventario(self, interaction: discord.Interaction):
        itens = pegar_inventario(interaction.user.id)
        buffs = pegar_buffs(interaction.user.id)
        corrupcao = pegar_corrupcao(interaction.user.id)
        saldo = quantidade_item(interaction.user.id, ITEM_FRAGMENTO)

        texto_itens = ""
        if itens:
            for item, qtd in itens:
                texto_itens += f"• **{item}** x{qtd}\n"
        else:
            texto_itens = "Nenhum item."

        texto_buffs = ""
        if buffs:
            for buff, qtd in buffs:
                texto_buffs += f"• **{buff}** x{qtd}\n"
        else:
            texto_buffs = "Nenhum buff ativo."

        embed = discord.Embed(
            title="🎒 Seu Inventário Amaldiçoado",
            description=f"🧩 Fragmentos: **{saldo}**",
            color=COR_ROXA_JUJUTSU
        )

        embed.add_field(name="📦 Itens", value=texto_itens, inline=False)
        embed.add_field(name="✨ Buffs", value=texto_buffs, inline=False)
        embed.add_field(name="🩸 Corrupção", value=f"**{corrupcao}** ponto(s)", inline=False)
        embed.set_footer(text="Família Sant's • Inventário")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def comprar_item(self, interaction: discord.Interaction, codigo: str):
        item = LOJA.get(codigo)

        if not item:
            await interaction.response.send_message("❌ Item não encontrado.", ephemeral=True)
            return

        saldo = quantidade_item(interaction.user.id, ITEM_FRAGMENTO)
        preco = item["preco"]

        if saldo < preco:
            await interaction.response.send_message(
                f"❌ Fragmentos insuficientes.\n\n"
                f"🧩 Necessário: **{preco}**\n"
                f"🧩 Você possui: **{saldo}**",
                ephemeral=True
            )
            return

        if not remover_item(interaction.user.id, ITEM_FRAGMENTO, preco):
            await interaction.response.send_message(
                "❌ Não foi possível concluir a compra.",
                ephemeral=True
            )
            return

        tipo = item["tipo"]

        if tipo == "purificar":
            nova_corrupcao = reduzir_corrupcao(interaction.user.id, item["valor"])

            await interaction.response.send_message(
                f"🧿 **Purificação concluída!**\n\n"
                f"🩸 Corrupção atual: **{nova_corrupcao}**",
                ephemeral=True
            )
            return

        if tipo == "cura":
            if restaurar_vida_total(interaction.user.id):
                await interaction.response.send_message(
                    f"❤️ **Cura realizada com sucesso!**\n\n"
                    f"Sua vida foi restaurada para `{VIDAS_MAXIMAS}/{VIDAS_MAXIMAS}`.",
                    ephemeral=True
                )
            else:
                adicionar_item(interaction.user.id, ITEM_FRAGMENTO, preco)

                await interaction.response.send_message(
                    "❌ Você não está registrado no **Jogo do Abate**.\n\n"
                    "Seus fragmentos foram devolvidos.",
                    ephemeral=True
                )
            return

        if tipo == "buff":
            adicionar_buff(interaction.user.id, item["buff"], item["quantidade"])

            await interaction.response.send_message(
                f"✨ **Compra concluída!**\n\n"
                f"Você recebeu: **{item['nome']}** x{item['quantidade']}",
                ephemeral=True
            )
            return

    @discord.ui.button(
        label="Ver Loja",
        emoji="🛒",
        style=discord.ButtonStyle.secondary,
        custom_id="loja_ver"
    )
    async def ver_loja(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🛒 Loja Amaldiçoada",
            description=texto_loja(),
            color=COR_ROXA_JUJUTSU
        )

        embed.set_image(url=BANNER_LOJA)
        embed.set_footer(text="Família Sant's • Loja")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Inventário",
        emoji="🎒",
        style=discord.ButtonStyle.secondary,
        custom_id="loja_inventario"
    )
    async def inventario_botao(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.mostrar_inventario(interaction)

    @discord.ui.button(
        label="Purificar",
        emoji="🧿",
        style=discord.ButtonStyle.success,
        custom_id="comprar_purificar"
    )
    async def comprar_purificar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.comprar_item(interaction, "purificar")

    @discord.ui.button(
        label="Cura",
        emoji="❤️",
        style=discord.ButtonStyle.success,
        custom_id="comprar_cura"
    )
    async def comprar_cura(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.comprar_item(interaction, "cura")

    @discord.ui.button(
        label="Escudo",
        emoji="🛡️",
        style=discord.ButtonStyle.primary,
        custom_id="comprar_escudo"
    )
    async def comprar_escudo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.comprar_item(interaction, "escudo")

    @discord.ui.button(
        label="Fúria",
        emoji="🔥",
        style=discord.ButtonStyle.danger,
        custom_id="comprar_furia"
    )
    async def comprar_furia(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.comprar_item(interaction, "furia")

    @discord.ui.button(
        label="Sorte",
        emoji="🍀",
        style=discord.ButtonStyle.primary,
        custom_id="comprar_sorte"
    )
    async def comprar_sorte(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.comprar_item(interaction, "sorte")


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

        embed = discord.Embed(
            title="🛒 Loja Amaldiçoada",
            description=(
                "Bem-vindo(a) à **Loja Amaldiçoada** da Família Sant's.\n\n"
                "Aqui você pode trocar seus **Fragmentos Amaldiçoados** por itens, buffs e purificações.\n\n"
                "🧩 **Fragmentos** são obtidos derrotando maldições e participando de bosses.\n"
                "🩸 **Corrupção** aumenta quando você falha contra maldições.\n"
                "✨ **Buffs** podem ajudar em maldições e bosses.\n\n"
                "Use os botões abaixo para comprar ou consultar seu inventário."
            ),
            color=COR_ROXA_JUJUTSU
        )

        embed.add_field(
            name="📦 Itens disponíveis",
            value=(
                "🧿 **Purificação** — reduz corrupção\n"
                "❤️ **Cura Total** — restaura vida\n"
                "🛡️ **Escudo** — reduz próximo dano\n"
                "🔥 **Fúria** — aumenta próximo dano no boss\n"
                "🍀 **Sorte** — melhora próxima tentativa/drop"
            ),
            inline=False
        )

        embed.add_field(
            name="📌 Como usar",
            value=(
                "Clique nos botões abaixo para comprar.\n"
                "As respostas aparecem apenas para você."
            ),
            inline=False
        )

        embed.set_image(url=BANNER_LOJA)
        embed.set_footer(text="Família Sant's • Loja Amaldiçoada")

        await ctx.send(embed=embed, view=LojaView())

    @commands.command(name="loja")
    async def loja(self, ctx):
        embed = discord.Embed(
            title="🛒 Loja Amaldiçoada",
            description=texto_loja(),
            color=COR_ROXA_JUJUTSU
        )

        embed.set_image(url=BANNER_LOJA)
        embed.set_footer(text="Família Sant's • Loja")

        await ctx.send(embed=embed)

    @commands.command(name="inventario", aliases=["inv"])
    async def inventario(self, ctx, membro: discord.Member = None):
        membro = membro or ctx.author

        itens = pegar_inventario(membro.id)
        buffs = pegar_buffs(membro.id)
        corrupcao = pegar_corrupcao(membro.id)
        saldo = quantidade_item(membro.id, ITEM_FRAGMENTO)

        texto_itens = ""
        if itens:
            for item, qtd in itens:
                texto_itens += f"• **{item}** x{qtd}\n"
        else:
            texto_itens = "Nenhum item."

        texto_buffs = ""
        if buffs:
            for buff, qtd in buffs:
                texto_buffs += f"• **{buff}** x{qtd}\n"
        else:
            texto_buffs = "Nenhum buff ativo."

        embed = discord.Embed(
            title=f"🎒 Inventário de {membro.display_name}",
            description=f"🧩 Fragmentos: **{saldo}**",
            color=COR_ROXA_JUJUTSU
        )

        embed.add_field(name="📦 Itens", value=texto_itens, inline=False)
        embed.add_field(name="✨ Buffs", value=texto_buffs, inline=False)
        embed.add_field(name="🩸 Corrupção", value=f"**{corrupcao}** ponto(s)", inline=False)
        embed.set_footer(text="Família Sant's • Inventário")

        await ctx.send(embed=embed)

    @commands.command(name="comprar")
    async def comprar(self, ctx, codigo: str = None):
        if not codigo:
            await ctx.reply(
                "❌ Use: `!comprar purificar`, `!comprar cura`, `!comprar escudo`, `!comprar furia` ou `!comprar sorte`."
            )
            return

        codigo = codigo.lower().strip()
        item = LOJA.get(codigo)

        if not item:
            await ctx.reply("❌ Item não encontrado. Use `!loja` para ver as opções.")
            return

        saldo = quantidade_item(ctx.author.id, ITEM_FRAGMENTO)
        preco = item["preco"]

        if saldo < preco:
            await ctx.reply(
                f"❌ Fragmentos insuficientes.\n"
                f"🧩 Necessário: **{preco}**\n"
                f"🧩 Você possui: **{saldo}**"
            )
            return

        if not remover_item(ctx.author.id, ITEM_FRAGMENTO, preco):
            await ctx.reply("❌ Não foi possível concluir a compra.")
            return

        tipo = item["tipo"]

        if tipo == "purificar":
            nova_corrupcao = reduzir_corrupcao(ctx.author.id, item["valor"])

            await ctx.reply(
                f"🧿 **Purificação concluída!**\n"
                f"🩸 Corrupção atual: **{nova_corrupcao}**"
            )
            return

        if tipo == "cura":
            if restaurar_vida_total(ctx.author.id):
                await ctx.reply(
                    f"❤️ **Vida restaurada:** `{VIDAS_MAXIMAS}/{VIDAS_MAXIMAS}`"
                )
            else:
                adicionar_item(ctx.author.id, ITEM_FRAGMENTO, preco)

                await ctx.reply(
                    "❌ Você não está registrado no Jogo do Abate.\n"
                    "Os fragmentos foram devolvidos."
                )
            return

        if tipo == "buff":
            adicionar_buff(ctx.author.id, item["buff"], item["quantidade"])

            await ctx.reply(
                f"✨ **Compra concluída!**\n"
                f"Você recebeu: **{item['nome']}** x{item['quantidade']}"
            )
            return

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