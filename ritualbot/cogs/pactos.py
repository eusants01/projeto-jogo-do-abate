import random
import discord
from discord.ext import commands

from utils.cassino_db import adicionar_moedas

CHANCE_PACTO_PROIBIDO = 1  # 1 em 10.000 mensagens

IMAGEM_PACTO_PROIBIDO = "https://i.imgur.com/MX7rQpp.png"

CARGOS_PROTEGIDOS = [
    1483191687927828766,
    1480349452744265759,
    1501356975491907664,
    1500545846427652166,
    1480381506064093225,
    1487560221202321600,
    1505698473125609636,
    1505698594651373719,
    1505698708711538829,
    1505701356743295048,
    1505701448900411413,
    1487272681685647510,
    1494113762947371202,
    1494114100907741214,
    1493475034503577611,
    1494134900360744961,
    1487891283102924961,
]


PACTOS_PROIBIDOS = [
    {
        "nome": "☠️ Pacto do Sacrifício",
        "recompensa_min": 10000,
        "recompensa_max": 30000,
        "descricao": "Você receberá moedas em troca de perder um cargo aleatório.",
        "consequencia": "Perderá um cargo aleatório.",
        "perde_cargo": True,
    },
    {
        "nome": "🎲 Pacto da Sorte Viciada",
        "recompensa_min": 25000,
        "recompensa_max": 50000,
        "descricao": "O Dealer oferece fortuna imediata, mas exige uma peça da sua posição.",
        "consequencia": "Pode perder um cargo aleatório.",
        "perde_cargo": True,
    },
    {
        "nome": "👁️ Pacto do Dealer",
        "recompensa_min": 50000,
        "recompensa_max": 75000,
        "descricao": "O Cassino reconheceu seu nome. A oferta é alta, mas o preço também.",
        "consequencia": "Perderá um cargo aleatório.",
        "perde_cargo": True,
    },
    {
        "nome": "💀 Pacto da Ruína",
        "recompensa_min": 75000,
        "recompensa_max": 100000,
        "descricao": "Uma proposta rara surgiu. Poucos recebem. Menos ainda aceitam.",
        "consequencia": "Perderá um cargo aleatório.",
        "perde_cargo": True,
    },
]


def sortear_pacto():
    pacto = random.choice(PACTOS_PROIBIDOS).copy()
    pacto["recompensa"] = random.randint(
        pacto["recompensa_min"],
        pacto["recompensa_max"]
    )
    return pacto


class PactoProibidoView(discord.ui.View):
    def __init__(self, membro: discord.Member, pacto: dict):
        super().__init__(timeout=300)
        self.membro = membro
        self.pacto = pacto
        self.respondido = False

    @discord.ui.button(label="Aceitar Pacto", emoji="☠️", style=discord.ButtonStyle.danger)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.membro.id:
            await interaction.response.send_message(
                "❌ Este pacto não pertence a você.",
                ephemeral=True
            )
            return

        if self.respondido:
            await interaction.response.send_message(
                "⚠️ Este pacto já foi decidido.",
                ephemeral=True
            )
            return

        self.respondido = True

        recompensa = self.pacto["recompensa"]
        adicionar_moedas(self.membro.id, recompensa)

        cargo_removido = None

        if self.pacto.get("perde_cargo", False):
            cargos_validos = [
                cargo for cargo in self.membro.roles
                if cargo.name != "@everyone"
                and not cargo.managed
                and cargo.id not in CARGOS_PROTEGIDOS
                and cargo < self.membro.guild.me.top_role
            ]

            if cargos_validos:
                cargo_removido = random.choice(cargos_validos)

                try:
                    await self.membro.remove_roles(
                        cargo_removido,
                        reason="Pacto Proibido aceito"
                    )
                except Exception:
                    cargo_removido = None

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="☠️ PACTO ASSINADO",
            description=(
                f"**{self.pacto['nome']}**\n\n"
                "O Cassino do Diabo aceitou sua decisão.\n\n"
                f"🪙 Você recebeu **{recompensa:,} Moedas do Diabo**.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{f'🎭 Cargo perdido: **{cargo_removido.name}**' if cargo_removido else '🎭 Nenhum cargo pôde ser removido.'}\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "> A casa sempre cobra."
            ),
            color=0x8B0000
        )

        embed.set_image(url=IMAGEM_PACTO_PROIBIDO)
        embed.set_footer(text="Cassino do Diabo • Pacto Proibido")

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Recusar", emoji="❌", style=discord.ButtonStyle.secondary)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.membro.id:
            await interaction.response.send_message(
                "❌ Este pacto não pertence a você.",
                ephemeral=True
            )
            return

        if self.respondido:
            await interaction.response.send_message(
                "⚠️ Este pacto já foi decidido.",
                ephemeral=True
            )
            return

        self.respondido = True

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="📜 PACTO RECUSADO",
            description=(
                f"**{self.pacto['nome']}**\n\n"
                "Você recusou a proposta do Cassino.\n\n"
                "> Talvez ele não ofereça novamente."
            ),
            color=0x2C2C2C
        )

        embed.set_image(url=IMAGEM_PACTO_PROIBIDO)
        embed.set_footer(text="Cassino do Diabo • Pacto Proibido")

        await interaction.response.edit_message(embed=embed, view=self)


class Pactos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown_dm = set()

    async def enviar_pacto_dm(self, membro: discord.Member):
        pacto = sortear_pacto()

        embed = discord.Embed(
            title="☠️ UMA CARTA NEGRA APARECEU",
            description=(
                "O Cassino do Diabo observou seus movimentos.\n\n"
                f"Um **{pacto['nome']}** foi enviado diretamente a você.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📜 **Descrição:**\n{pacto['descricao']}\n\n"
                f"🪙 **Recompensa:**\n**{pacto['recompensa']:,} Moedas do Diabo**\n\n"
                f"🎭 **Consequência:**\n{pacto['consequencia']}\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "> Toda fortuna exige um sacrifício."
            ),
            color=0x8B0000
        )

        embed.set_image(url=IMAGEM_PACTO_PROIBIDO)
        embed.set_footer(text="Cassino do Diabo • Pacto Proibido")

        await membro.send(
            embed=embed,
            view=PactoProibidoView(membro, pacto)
        )

    @commands.command(name="pacto")
    @commands.has_permissions(administrator=True)
    async def pacto(self, ctx, membro: discord.Member):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        if membro.bot:
            await ctx.send(
                "❌ Não é possível enviar pactos para bots.",
                delete_after=8
            )
            return

        try:
            await self.enviar_pacto_dm(membro)

            frases = [
                "☠️ O Dealer entregou uma carta negra.",
                "🎰 Um novo contrato foi enviado.",
                "👁️ O Cassino escolheu um novo alvo.",
                "📜 Um pacto proibido encontrou seu destino.",
                "💀 Nem todos recusam a oferta.",
            ]

            await ctx.send(
                random.choice(frases),
                delete_after=8
            )

        except discord.Forbidden:
            await ctx.send(
                "❌ O membro está com a DM fechada.",
                delete_after=8
            )

    @commands.command(name="pactos")
    @commands.has_permissions(administrator=True)
    async def pactos(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        membros_validos = [
            membro for membro in ctx.guild.members
            if not membro.bot
        ]

        quantidade = random.randint(3, 7)

        escolhidos = random.sample(
            membros_validos,
            min(quantidade, len(membros_validos))
        )

        if ctx.author not in escolhidos:
            escolhidos.append(ctx.author)

        enviados = 0

        for membro in escolhidos:
            try:
                await self.enviar_pacto_dm(membro)
                enviados += 1
            except Exception:
                pass

        mensagens = [
            f"☠️ O Dealer enviou cartas negras para **{enviados}** membro(s).",
            f"🎰 **{enviados}** contratos proibidos foram espalhados pela Família.",
            f"👁️ O Cassino escolheu **{enviados}** alvo(s).",
            f"📜 Pactos secretos foram enviados. Nem todos voltarão iguais.",
        ]

        await ctx.send(
            random.choice(mensagens),
            delete_after=10
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not isinstance(message.author, discord.Member):
            return

        if message.author.id in self.cooldown_dm:
            return

        sorteio = random.randint(1, 10000)

        if sorteio > CHANCE_PACTO_PROIBIDO:
            return

        self.cooldown_dm.add(message.author.id)

        try:
            await self.enviar_pacto_dm(message.author)
        except discord.Forbidden:
            pass


async def setup(bot):
    await bot.add_cog(Pactos(bot))