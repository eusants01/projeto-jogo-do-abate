import discord
from discord.ext import commands

from utils.db import conectar, buscar_jogador, registrar_jogador

COR_ROXA = 0x7B2CFF

FAMILIAS = {
    "gojo": "🔵 Família Gojo",
    "sukuna": "🔴 Família Sukuna",
}


def definir_familia(user_id: int, familia: str):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE jogadores SET familia = %s WHERE user_id = %s",
        (familia, user_id)
    )

    conn.commit()
    conn.close()


def pegar_familia(user_id: int):
    jogador = buscar_jogador(user_id)

    if not jogador:
        return None

    # Formato do db.py: user_id, username, vidas, abates, contratos, status, alvo_id, familia
    return jogador[7]


def ranking_familias():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT familia, COUNT(*) AS membros, COALESCE(SUM(abates), 0) AS abates
        FROM jogadores
        WHERE familia IS NOT NULL
          AND familia != 'Livre'
        GROUP BY familia
        ORDER BY abates DESC, membros DESC
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
            atual = pegar_familia(ctx.author.id)

            if atual:
                await ctx.reply(
                    f"🏯 Sua família atual: **{atual}**\n\n"
                    "Use:\n"
                    "`!familia gojo`\n"
                    "`!familia sukuna`\n"
                    "`!sair_familia`"
                )
            else:
                await ctx.reply(
                    "Você ainda não está registrado no Jogo do Abate.\n\n"
                    "Use:\n"
                    "`!familia gojo`\n"
                    "`!familia sukuna`"
                )
            return

        nome = nome.lower().strip()

        if nome not in FAMILIAS:
            await ctx.reply("❌ Família não encontrada. Use `gojo` ou `sukuna`.")
            return

        jogador = buscar_jogador(ctx.author.id)

        if not jogador:
            registrar_jogador(ctx.author.id, ctx.author.name)

        familia_escolhida = FAMILIAS[nome]
        definir_familia(ctx.author.id, familia_escolhida)

        embed = discord.Embed(
            title="🏯 Família definida",
            description=(
                f"{ctx.author.mention} entrou para a **{familia_escolhida}**.\n\n"
                "Agora sua família aparecerá no perfil do Jogo do Abate."
            ),
            color=COR_ROXA
        )

        await ctx.reply(embed=embed)

    @commands.command(name="sair_familia")
    async def sair_familia(self, ctx):
        jogador = buscar_jogador(ctx.author.id)

        if not jogador:
            await ctx.reply("❌ Você ainda não está registrado no Jogo do Abate.")
            return

        definir_familia(ctx.author.id, "Livre")

        await ctx.reply(f"🚪 {ctx.author.mention} saiu da família atual e voltou para **Livre**.")

    @commands.command(name="minha_familia")
    async def minha_familia(self, ctx):
        jogador = buscar_jogador(ctx.author.id)

        if not jogador:
            await ctx.reply("❌ Você ainda não está registrado no Jogo do Abate.")
            return

        familia = jogador[7]

        await ctx.reply(f"🏯 Sua família atual é: **{familia}**")

    @commands.command(name="ranking_familias")
    async def ranking_familias_cmd(self, ctx):
        dados = ranking_familias()

        if not dados:
            await ctx.reply("Nenhuma família possui membros ainda.")
            return

        texto = ""

        for i, linha in enumerate(dados, start=1):
            # psycopg2 normal retorna tupla: familia, membros, abates
            familia, membros, abates = linha

            texto += (
                f"**{i}º** {familia}\n"
                f"👥 Membros: **{membros}**\n"
                f"⚔️ Abates: **{abates or 0}**\n\n"
            )

        embed = discord.Embed(
            title="🏯 Ranking das Famílias",
            description=texto,
            color=COR_ROXA
        )

        embed.set_footer(text="Família Sant's • Sistema de Famílias")

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Familias(bot))
