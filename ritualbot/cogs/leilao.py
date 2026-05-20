import asyncio
import time
import discord
from discord.ext import commands

from utils.cassino_db import obter_saldo, remover_moedas, adicionar_moedas

CANAL_LEILAO_ID = 1503972510285168691
BANNER_LEILAO = "https://cdn.discordapp.com/attachments/961677475191078992/1506536746278719578/48a63abb-0e0c-4859-8518-5846b51ed4c1.png?ex=6a0e9f2e&is=6a0d4dae&hm=b5a3fd40fd1837ad3d509aaa155495be8927e6ba290619d850c7d0d36732e22c&"

TEMPO_PADRAO = 10 * 60
ANTI_SNIPER_SEGUNDOS = 30
EXTENSAO_ANTI_SNIPER = 60

COR_LEILAO = 0x8B0000
COR_DOURADO = 0xD4AF37
COR_ESCURO = 0x1A0000

CARGOS_CRIAR_LEILAO = [
    # coloque IDs de cargos aqui depois
    # 123456789012345678,
]


def pode_criar_leilao(membro: discord.Member) -> bool:
    if membro.guild_permissions.administrator:
        return True

    cargos_usuario = [cargo.id for cargo in membro.roles]

    return any(cargo_id in cargos_usuario for cargo_id in CARGOS_CRIAR_LEILAO)


class CriarLeilaoModal(discord.ui.Modal, title="🎰 Criar Leilão do Diabo"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        self.item = discord.ui.TextInput(
            label="Item do leilão",
            placeholder="Ex: Cargo VIP, Gamepass, Nitro, Cargo personalizado...",
            required=True,
            max_length=80
        )

        self.descricao = discord.ui.TextInput(
            label="Descrição do item",
            placeholder="Explique o que será entregue ao vencedor.",
            required=True,
            style=discord.TextStyle.paragraph,
            max_length=700
        )

        self.lance_inicial = discord.ui.TextInput(
            label="Lance inicial",
            placeholder="Ex: 1000",
            required=True,
            max_length=12
        )

        self.add_item(self.item)
        self.add_item(self.descricao)
        self.add_item(self.lance_inicial)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            lance_inicial = int(
                str(self.lance_inicial.value)
                .replace(".", "")
                .replace(",", "")
                .strip()
            )
        except ValueError:
            await interaction.response.send_message(
                "❌ O lance inicial precisa ser um número válido.",
                ephemeral=True
            )
            return

        if lance_inicial <= 0:
            await interaction.response.send_message(
                "❌ O lance inicial precisa ser maior que zero.",
                ephemeral=True
            )
            return

        canal = interaction.guild.get_channel(CANAL_LEILAO_ID)

        if not canal:
            await interaction.response.send_message(
                "❌ Canal de leilão não encontrado.",
                ephemeral=True
            )
            return

        view = LeilaoView(
            item=str(self.item.value),
            descricao=str(self.descricao.value),
            lance_inicial=lance_inicial,
            autor_id=interaction.user.id
        )

        msg = await canal.send(embed=view.embed(), view=view)
        view.mensagem = msg

        asyncio.create_task(view.finalizar())

        await interaction.response.send_message(
            f"🎰 Leilão criado com sucesso em <#{CANAL_LEILAO_ID}>.",
            ephemeral=True
        )


class PainelLeilaoView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Criar Leilão",
        emoji="🎰",
        style=discord.ButtonStyle.danger,
        custom_id="leilao_criar"
    )
    async def criar_leilao(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not pode_criar_leilao(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas administradores ou cargos autorizados podem iniciar leilões.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(CriarLeilaoModal(self.bot))

    @discord.ui.button(
        label="Como Funciona",
        emoji="📜",
        style=discord.ButtonStyle.secondary,
        custom_id="leilao_info"
    )
    async def como_funciona(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📜 Como funciona o Leilão do Diabo",
            description=(
                "No **Leilão do Diabo**, cada lance é uma aposta real usando **🪙 Moedas do Diabo**.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💰 **Lances cobrados na hora**\n"
                "Ao dar um lance, o valor é removido imediatamente do seu saldo.\n\n"
                "↩️ **Devolução automática**\n"
                "Se outro membro superar seu lance, suas moedas são devolvidas.\n\n"
                "⏳ **Anti-sniper**\n"
                "Se alguém apostar nos últimos segundos, o tempo pode ser estendido.\n\n"
                "🏆 **Vencedor automático**\n"
                "Quando o tempo acabar, o maior apostador vence.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "> A casa aceita lances, mas nunca perdoa indecisão."
            ),
            color=COR_LEILAO
        )
        embed.set_image(url=BANNER_LEILAO)
        embed.set_footer(text="Família Sant’s • Leilão do Diabo")

        await interaction.response.send_message(embed=embed, ephemeral=True)


class LanceModal(discord.ui.Modal, title="💰 Dar Lance"):
    def __init__(self, view):
        super().__init__()
        self.view_leilao = view

        self.valor = discord.ui.TextInput(
            label="Valor do lance",
            placeholder="Exemplo: 5000",
            required=True,
            max_length=12
        )

        self.add_item(self.valor)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            valor = int(
                str(self.valor.value)
                .replace(".", "")
                .replace(",", "")
                .strip()
            )
        except ValueError:
            await interaction.response.send_message(
                "❌ Informe um valor válido.",
                ephemeral=True
            )
            return

        await self.view_leilao.processar_lance(interaction, valor)


class LeilaoView(discord.ui.View):
    def __init__(self, item, descricao, lance_inicial, autor_id):
        super().__init__(timeout=None)

        self.item = item
        self.descricao = descricao
        self.lance_inicial = lance_inicial
        self.lance_atual = 0
        self.maior_apostador = None
        self.autor_id = autor_id
        self.historico = []
        self.finalizado = False
        self.mensagem = None
        self.fim = time.time() + TEMPO_PADRAO

    def tempo_restante(self):
        restante = int(self.fim - time.time())

        if restante <= 0:
            return "Encerrando..."

        minutos = restante // 60
        segundos = restante % 60

        return f"{minutos}min {segundos}s"

    def valor_atual(self):
        return self.lance_atual if self.lance_atual > 0 else self.lance_inicial

    def embed(self):
        maior = self.maior_apostador.mention if self.maior_apostador else "Nenhum apostador ainda"
        valor = self.valor_atual()

        historico_txt = ""

        for nome, lance in self.historico[-5:][::-1]:
            historico_txt += f"• **{nome}** — 🪙 `{lance:,}`\n"

        if not historico_txt:
            historico_txt = "Nenhum lance registrado."

        embed = discord.Embed(
            title="🎰 LEILÃO DO DIABO",
            description=(
                "Senhoras e senhores, a mesa foi aberta.\n"
                "Somente os mais ousados sairão com o prêmio.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📦 **Item em leilão:**\n"
                f"**{self.item}**\n\n"
                f"📜 **Descrição:**\n"
                f"{self.descricao}\n\n"
                f"💰 **Lance atual:** `🪙 {valor:,}`\n"
                f"👑 **Maior apostador:** {maior}\n"
                f"⏳ **Tempo restante:** `{self.tempo_restante()}`\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🎲 **Regras da mesa:**\n"
                "• Cada lance é cobrado na hora.\n"
                "• Quem for superado recebe as moedas de volta.\n"
                "• Lances no final podem estender o tempo.\n\n"
                "> A casa sempre observa."
            ),
            color=COR_LEILAO
        )

        embed.add_field(
            name="📊 Últimos Lances",
            value=historico_txt,
            inline=False
        )

        embed.set_image(url=BANNER_LEILAO)
        embed.set_footer(text="Família Sant’s • Leilão do Diabo")

        return embed

    async def atualizar(self):
        if self.mensagem:
            await self.mensagem.edit(embed=self.embed(), view=self)

    async def processar_lance(self, interaction: discord.Interaction, valor: int):
        if self.finalizado:
            await interaction.response.send_message(
                "❌ Este leilão já foi finalizado.",
                ephemeral=True
            )
            return

        minimo = self.lance_atual + 1 if self.lance_atual > 0 else self.lance_inicial

        if valor < minimo:
            await interaction.response.send_message(
                f"❌ O lance mínimo agora é **🪙 {minimo:,}**.",
                ephemeral=True
            )
            return

        if self.maior_apostador and interaction.user.id == self.maior_apostador.id:
            await interaction.response.send_message(
                "⚠️ Você já possui o maior lance.",
                ephemeral=True
            )
            return

        saldo = obter_saldo(interaction.user.id)

        if saldo < valor:
            await interaction.response.send_message(
                f"❌ Você não possui moedas suficientes.\nSeu saldo: **🪙 {saldo:,}**",
                ephemeral=True
            )
            return

        remover_moedas(interaction.user.id, valor)

        if self.maior_apostador:
            adicionar_moedas(self.maior_apostador.id, self.lance_atual)

        self.lance_atual = valor
        self.maior_apostador = interaction.user
        self.historico.append((interaction.user.display_name, valor))

        restante = self.fim - time.time()

        if restante <= ANTI_SNIPER_SEGUNDOS:
            self.fim += EXTENSAO_ANTI_SNIPER

        await interaction.response.send_message(
            f"💰 Lance registrado: **🪙 {valor:,}**",
            ephemeral=True
        )

        await self.atualizar()

    @discord.ui.button(
        label="Dar Lance",
        emoji="💰",
        style=discord.ButtonStyle.danger,
        custom_id="leilao_lance"
    )
    async def dar_lance(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(LanceModal(self))

    @discord.ui.button(
        label="+500",
        emoji="🪙",
        style=discord.ButtonStyle.secondary,
        custom_id="leilao_500"
    )
    async def lance_500(self, interaction: discord.Interaction, button: discord.ui.Button):
        base = self.valor_atual()
        await self.processar_lance(interaction, base + 500)

    @discord.ui.button(
        label="+1.000",
        emoji="🪙",
        style=discord.ButtonStyle.secondary,
        custom_id="leilao_1000"
    )
    async def lance_1000(self, interaction: discord.Interaction, button: discord.ui.Button):
        base = self.valor_atual()
        await self.processar_lance(interaction, base + 1000)

    @discord.ui.button(
        label="Histórico",
        emoji="📜",
        style=discord.ButtonStyle.secondary,
        custom_id="leilao_historico"
    )
    async def historico_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.historico:
            await interaction.response.send_message(
                "📜 Nenhum lance registrado ainda.",
                ephemeral=True
            )
            return

        texto = ""

        for nome, lance in self.historico[-10:][::-1]:
            texto += f"• **{nome}** — 🪙 `{lance:,}`\n"

        embed = discord.Embed(
            title="📜 Histórico do Leilão",
            description=texto,
            color=COR_LEILAO
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def finalizar(self):
        await asyncio.sleep(1)

        while time.time() < self.fim:
            await asyncio.sleep(5)

            if not self.finalizado:
                await self.atualizar()

        self.finalizado = True

        for item in self.children:
            item.disabled = True

        if self.maior_apostador:
            embed = discord.Embed(
                title="🏆 LEILÃO FINALIZADO",
                description=(
                    "O martelo caiu. A casa reconheceu o vencedor.\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📦 **Item:** {self.item}\n"
                    f"👑 **Vencedor:** {self.maior_apostador.mention}\n"
                    f"💰 **Lance final:** 🪙 **{self.lance_atual:,}**\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "> O pagamento já foi realizado automaticamente."
                ),
                color=COR_DOURADO
            )
        else:
            embed = discord.Embed(
                title="☠️ LEILÃO ENCERRADO",
                description=(
                    f"📦 **Item:** {self.item}\n\n"
                    "Nenhum lance foi realizado.\n\n"
                    "> Nem todos tiveram coragem de sentar à mesa."
                ),
                color=COR_ESCURO
            )

        embed.set_image(url=BANNER_LEILAO)
        embed.set_footer(text="Família Sant’s • Leilão do Diabo")

        if self.mensagem:
            await self.mensagem.edit(embed=embed, view=self)


class Leilao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(PainelLeilaoView(bot))

    @commands.command(name="painel_leilao")
    @commands.has_permissions(administrator=True)
    async def painel_leilao(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        embed = discord.Embed(
            title="🎰 PAINEL DO LEILÃO DO DIABO",
            description=(
                "Bem-vindo ao salão de apostas da Família Sant’s.\n\n"
                "Aqui, administradores e cargos autorizados podem iniciar leilões oficiais "
                "utilizando **🪙 Moedas do Diabo**.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "📦 **Itens possíveis:**\n"
                "• Cargos temporários\n"
                "• Gamepasses\n"
                "• VIP\n"
                "• Recompensas especiais\n"
                "• Itens secretos\n\n"
                "💰 **Sistema de lances:**\n"
                "• O lance é cobrado imediatamente.\n"
                "• Se outro membro superar, suas moedas voltam.\n"
                "• O maior apostador vence automaticamente no final.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "> Faça sua oferta. A casa está observando."
            ),
            color=COR_LEILAO
        )

        embed.set_image(url=BANNER_LEILAO)
        embed.set_footer(text="Família Sant’s • Leilão do Diabo")

        await ctx.send(embed=embed, view=PainelLeilaoView(self.bot))

    @painel_leilao.error
    async def painel_leilao_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply(
                "❌ Apenas administradores podem enviar o painel de leilão.",
                delete_after=8
            )
        else:
            await ctx.reply(
                "⚠️ Ocorreu um erro ao enviar o painel de leilão.",
                delete_after=8
            )
            print(f"[ERRO PAINEL LEILÃO] {error}")


async def setup(bot):
    await bot.add_cog(Leilao(bot))