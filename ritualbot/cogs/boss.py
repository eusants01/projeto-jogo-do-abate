import random
import discord
from discord.ext import commands
from utils.db import (
    buscar_jogador,
    adicionar_abate,
    remover_vida,
    listar_jogadores_vivos,
)

COR_VERMELHA = 0xE63946
COR_VERDE = 0x2ECC71

VIDAS_MAXIMAS = 20
CANAL_LOG_MALDICOES_ID = 1500543560834089272

# =========================
# BOSSES
# =========================

BOSSES = [
    {
        "nome": "Sukuna",
        "descricao": "O Rei das Maldições abriu seu domínio.",
        "imagem": "https://media.tenor.com/RAp5YpmEH5EAAAAd/jujutsu-kaisen-shibuya-arc-sukuna-shibuya-arc.gif",
        "vida": 500,
        "tempo": 600,
        "dano_min": 15,
        "dano_max": 40,
        "recompensa_participou": 1,
        "recompensa_top": 5,
        "recompensa_final": 3,
        "dano_falha": 5,
    },
    {
        "nome": "Mahoraga",
        "descricao": "A roda gira. A adaptação começou.",
        "imagem": "https://media.tenor.com/1qESUcxlIRMAAAAC/mahoraga-then-shadows.gif",
        "vida": 400,
        "tempo": 600,
        "dano_min": 10,
        "dano_max": 35,
        "recompensa_participou": 1,
        "recompensa_top": 4,
        "recompensa_final": 3,
        "dano_falha": 4,
    },
    {
        "nome": "Rika",
        "descricao": "Uma força esmagadora apareceu.",
        "imagem": "https://media.tenor.com/3gqzv7Qy7ZcAAAAC/rika-jujutsu-kaisen.gif",
        "vida": 350,
        "tempo": 600,
        "dano_min": 10,
        "dano_max": 30,
        "recompensa_participou": 1,
        "recompensa_top": 3,
        "recompensa_final": 2,
        "dano_falha": 3,
    },
]


def buscar_boss(nome):
    nome = nome.lower()
    for boss in BOSSES:
        if boss["nome"].lower() == nome:
            return boss
    return None


# =========================
# VIEW DO BOSS
# =========================

class BossView(discord.ui.View):
    def __init__(self, boss):
        super().__init__(timeout=boss["tempo"])
        self.boss = boss
        self.vida = boss["vida"]
        self.max_vida = boss["vida"]
        self.danos = {}
        self.finalizado = False
        self.mensagem = None
        self.ultimo_hit = None

    def barra(self):
        pct = self.vida / self.max_vida
        cheio = round(pct * 10)
        vazio = 10 - cheio
        return "🟥" * cheio + "⬛" * vazio

    def embed(self):
        ranking = sorted(self.danos.items(), key=lambda x: x[1], reverse=True)[:5]

        texto = ""
        for i, (uid, dmg) in enumerate(ranking, 1):
            medalha = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}º"
            texto += f"{medalha} <@{uid}> — {dmg} dano\n"

        if not texto:
            texto = "Ninguém atacou ainda."

        embed = discord.Embed(
            title=f"💀 BOSS — {self.boss['nome']}",
            description=(
                f"{self.boss['descricao']}\n\n"
                f"❤️ {self.vida}/{self.max_vida}\n{self.barra()}"
            ),
            color=COR_VERMELHA
        )

        embed.add_field(name="Ranking", value=texto, inline=False)
        embed.set_image(url=self.boss["imagem"])
        return embed

    async def finalizar(self, channel, guild):
        top = max(self.danos, key=self.danos.get)

        for uid in self.danos:
            if buscar_jogador(uid):
                adicionar_abate(uid, self.boss["recompensa_participou"])

        adicionar_abate(top, self.boss["recompensa_top"])

        if self.ultimo_hit:
            adicionar_abate(self.ultimo_hit, self.boss["recompensa_final"])

        await channel.send(
            f"🏆 Boss derrotado!\n"
            f"🥇 Top: <@{top}>\n"
            f"⚔️ Final: <@{self.ultimo_hit}>"
        )

    async def on_timeout(self):
        if self.finalizado:
            return

        jogadores = listar_jogadores_vivos()

        if not jogadores:
            return

        for j in random.sample(jogadores, min(3, len(jogadores))):
            remover_vida(j[0], self.boss["dano_falha"])

        await self.mensagem.channel.send("💀 Boss venceu.")

    @discord.ui.button(label="Atacar", style=discord.ButtonStyle.danger)
    async def atacar(self, interaction: discord.Interaction, button):
        if self.finalizado:
            return

        dano = random.randint(self.boss["dano_min"], self.boss["dano_max"])

        self.vida -= dano
        self.danos[interaction.user.id] = self.danos.get(interaction.user.id, 0) + dano
        self.ultimo_hit = interaction.user.id

        if self.vida <= 0:
            self.finalizado = True
            for i in self.children:
                i.disabled = True

            await interaction.response.edit_message(embed=self.embed(), view=self)
            await self.finalizar(interaction.channel, interaction.guild)
            return

        await interaction.response.edit_message(embed=self.embed(), view=self)


# =========================
# COG
# =========================

class Boss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="boss")
    async def boss(self, ctx, *, nome=None):
        if nome:
            boss = buscar_boss(nome)
        else:
            boss = random.choice(BOSSES)

        if not boss:
            await ctx.send("Boss não encontrado.")
            return

        view = BossView(boss)
        msg = await ctx.send(embed=view.embed(), view=view)
        view.mensagem = msg


async def setup(bot):
    await bot.add_cog(Boss(bot))