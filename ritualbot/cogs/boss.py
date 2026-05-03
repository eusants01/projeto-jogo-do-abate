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
COR_ROXA = 0x7B2CFF

VIDAS_MAXIMAS = 20
CANAL_LOG_MALDICOES_ID = 1500543560834089272

BOSSES = [
    {
        "nome": "Sukuna",
        "descricao": "O Rei das Maldições abriu seu domínio.",
        "imagem": "https://tenor.com/view/jujutsu-kaisen-ryomen-sukuna-fuga-jjk-phantom-parade-gif-16618067802049057888",
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
        "imagem": "https://tenor.com/view/megumi-mahoraga-ritual-gif-8462616184562925653",
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
        "imagem": "https://tenor.com/view/rika-rika-orimoto-yuta-yuta-okkotsu-jujutsu-kaisen-gif-9848562706999514109",
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


def buscar_boss(nome: str):
    nome = nome.lower().strip()

    for boss in BOSSES:
        if boss["nome"].lower() == nome:
            return boss

    return None


async def enviar_log(guild: discord.Guild, embed: discord.Embed):
    if not guild:
        return

    canal = guild.get_channel(CANAL_LOG_MALDICOES_ID)
    if canal:
        await canal.send(embed=embed)


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
        if self.max_vida <= 0:
            return "⬛" * 10

        pct = max(0, self.vida) / self.max_vida
        cheio = round(pct * 10)
        vazio = 10 - cheio

        return "🟥" * cheio + "⬛" * vazio

    def embed(self):
        ranking = sorted(
            self.danos.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        texto = ""

        for i, (uid, dmg) in enumerate(ranking, start=1):
            medalha = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"`#{i}`"
            texto += f"{medalha} <@{uid}> — 💥 **{dmg}** dano\n"

        if not texto:
            texto = "Ninguém atacou ainda."

        embed = discord.Embed(
            title=f"💀 BOSS — {self.boss['nome']}",
            description=(
                f"{self.boss['descricao']}\n\n"
                f"❤️ **Vida:** `{max(0, self.vida)}/{self.max_vida}`\n"
                f"{self.barra()}\n\n"
                f"⏳ Tempo limite: **{self.boss['tempo'] // 60} minutos**"
            ),
            color=COR_VERMELHA
        )

        embed.add_field(name="🏆 Ranking de Dano", value=texto, inline=False)
        embed.set_image(url=self.boss["imagem"])
        embed.set_footer(text="Família Sant's • Raid Boss")
        return embed

    async def finalizar(self, channel: discord.TextChannel, guild: discord.Guild):
        if not self.danos:
            return

        top = max(self.danos, key=self.danos.get)

        for uid in self.danos:
            if buscar_jogador(uid):
                adicionar_abate(uid, self.boss["recompensa_participou"])

        if buscar_jogador(top):
            adicionar_abate(top, self.boss["recompensa_top"])

        if self.ultimo_hit and buscar_jogador(self.ultimo_hit):
            adicionar_abate(self.ultimo_hit, self.boss["recompensa_final"])

        ranking = sorted(
            self.danos.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        texto_ranking = ""

        for i, (uid, dmg) in enumerate(ranking, start=1):
            medalha = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"`#{i}`"
            texto_ranking += f"{medalha} <@{uid}> — 💥 **{dmg}** dano\n"

        embed = discord.Embed(
            title="🏆 BOSS DERROTADO",
            description=(
                f"💀 **Boss:** {self.boss['nome']}\n"
                f"🥇 **Maior dano:** <@{top}>\n"
                f"⚔️ **Golpe final:** <@{self.ultimo_hit}>\n\n"
                f"🎁 **Recompensas:**\n"
                f"• Participou: +{self.boss['recompensa_participou']} abate(s)\n"
                f"• Top dano: +{self.boss['recompensa_top']} abate(s)\n"
                f"• Golpe final: +{self.boss['recompensa_final']} abate(s)"
            ),
            color=COR_VERDE
        )

        embed.add_field(name="📊 Ranking Final", value=texto_ranking, inline=False)
        embed.set_footer(text="Família Sant's • Raid Boss Finalizado")

        await channel.send(embed=embed)
        await enviar_log(guild, embed)

    async def on_timeout(self):
        if self.finalizado:
            return

        self.finalizado = True

        for item in self.children:
            item.disabled = True

        if self.mensagem:
            try:
                await self.mensagem.edit(embed=self.embed(), view=self)
            except Exception:
                pass

        jogadores = listar_jogadores_vivos()

        if not jogadores:
            return

        atingidos = random.sample(jogadores, min(3, len(jogadores)))

        texto_atingidos = ""

        for jogador in atingidos:
            user_id = jogador[0]
            resultado = remover_vida(user_id, self.boss["dano_falha"])

            if resultado:
                vidas = resultado[2]
                status = resultado[5]
                texto_atingidos += (
                    f"💀 <@{user_id}> perdeu **{self.boss['dano_falha']}** vida(s). "
                    f"❤️ `{vidas}/{VIDAS_MAXIMAS}`"
                )

                if status == "eliminado":
                    texto_atingidos += " ☠️ **ELIMINADO**"

                texto_atingidos += "\n"

        embed = discord.Embed(
            title="☠️ O BOSS VENCEU",
            description=(
                f"💀 **{self.boss['nome']}** não foi derrotado a tempo.\n\n"
                f"{texto_atingidos}"
            ),
            color=COR_VERMELHA
        )

        embed.set_footer(text="Família Sant's • Raid Boss")
        await self.mensagem.channel.send(embed=embed)
        await enviar_log(self.mensagem.guild, embed)

    @discord.ui.button(
        label="Atacar",
        emoji="⚔️",
        style=discord.ButtonStyle.danger,
        custom_id="boss_atacar"
    )
    async def atacar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finalizado:
            await interaction.response.send_message(
                "💀 Esse boss já foi finalizado.",
                ephemeral=True
            )
            return

        jogador = buscar_jogador(interaction.user.id)

        if not jogador:
            await interaction.response.send_message(
                "🚫 Você precisa entrar no **Jogo do Abate** antes de atacar bosses.",
                ephemeral=True
            )
            return

        if jogador[5] != "vivo":
            await interaction.response.send_message(
                "💀 Você está eliminado e não pode atacar bosses.",
                ephemeral=True
            )
            return

        dano = random.randint(self.boss["dano_min"], self.boss["dano_max"])

        self.vida -= dano
        self.danos[interaction.user.id] = self.danos.get(interaction.user.id, 0) + dano
        self.ultimo_hit = interaction.user.id

        if self.vida <= 0:
            self.vida = 0
            self.finalizado = True

            for item in self.children:
                item.disabled = True

            await interaction.response.edit_message(embed=self.embed(), view=self)
            await self.finalizar(interaction.channel, interaction.guild)
            return

        await interaction.response.edit_message(embed=self.embed(), view=self)


class Boss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="boss")
    @commands.has_permissions(administrator=True)
    async def boss(self, ctx, *, nome=None):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        if nome:
            boss = buscar_boss(nome)
        else:
            boss = random.choice(BOSSES)

        if not boss:
            nomes = ", ".join([b["nome"] for b in BOSSES])
            await ctx.send(
                f"❌ Boss não encontrado.\nUse: `{nomes}`",
                delete_after=10
            )
            return

        view = BossView(boss)

        msg = await ctx.send(
            embed=view.embed(),
            view=view
        )

        view.mensagem = msg

    @boss.error
    async def boss_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply(
                "❌ Apenas administradores podem invocar bosses.",
                delete_after=8
            )
        else:
            await ctx.reply(
                "⚠️ Ocorreu um erro ao invocar o boss.",
                delete_after=8
            )
            print(f"[ERRO BOSS] {error}")


async def setup(bot):
    await bot.add_cog(Boss(bot))