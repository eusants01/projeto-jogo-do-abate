import discord
from discord.ext import commands
from utils.db import conectar, buscar_jogador, registrar_jogador

FAMILIAS = {
    "gojo": "🔵 Família Gojo",
    "sukuna": "🔴 Família Sukuna",
}


def definir_familia(user_id: int, familia: str):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE jogadores SET familia = ? WHERE user_id = ?",
        (familia, user_id)
    )

    conn.commit()
    conn.close()


def ranking_familias():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT familia, COUNT(*), SUM(abates)
        FROM jogadores
        WHERE familia != 'Livre'
        GROUP BY familia
        ORDER BY SUM(abates) DESC
    """)

    dados = cursor.fetchall()
    conn.close()
    return dados


class Familias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="familia")
    async def familia(self, ctx, nome: str = None):
        if not nome:
            await ctx.reply(
                "Use:\n"
                "`!familia gojo`\n"
                "`!familia sukuna`"
            )
            return

        nome = nome.lower()

        if nome not in FAMILIAS:
            await ctx.reply("❌ Família não encontrada. Use `gojo` ou `sukuna`.")
            return

        jogador = buscar_jogador(ctx.author.id)

        if not jogador:
            registrar_jogador(ctx.author.id, ctx.author.name)

        definir_familia(ctx.author.id, FAMILIAS[nome])

        await ctx.reply(
            f"🏯 {ctx.author.mention} entrou para a **{FAMILIAS[nome]}**!"
        )

    @commands.command(name="sair_familia")
    async def sair_familia(self, ctx):
        jogador = buscar_jogador(ctx.author.id)

        if not jogador:
            await ctx.reply("❌ Você ainda não está registrado no jogo.")
            return

        definir_familia(ctx.author.id, "Livre")

        await ctx.reply(f"🚪 {ctx.author.mention} saiu da família atual.")

    @commands.command(name="ranking_familias")
    async def ranking_familias_cmd(self, ctx):
        dados = ranking_familias()

        if not dados:
            await ctx.reply("Nenhuma família possui membros ainda.")
            return

        texto = ""

        for i, (familia, membros, abates) in enumerate(dados, start=1):
            texto += (
                f"**{i}º** {familia}\n"
                f"👥 Membros: **{membros}**\n"
                f"⚔️ Abates: **{abates or 0}**\n\n"
            )

        embed = discord.Embed(
            title="🏯 Ranking das Famílias",
            description=texto,
            color=0x7B2CFF
        )

        embed.set_footer(text="Família Sant's • Sistema de Famílias")

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Familias(bot))