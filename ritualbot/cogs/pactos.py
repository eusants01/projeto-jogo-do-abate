import random
import discord
from discord.ext import commands

from utils.cassino_db import adicionar_moedas

# =========================
# CONFIG
# =========================

CHANCE_PACTO_PROIBIDO = 1  # 1 em 10.000
RECOMPENSA_PACTO = 50000

# 🎭 Imagem/GIF do pacto
IMAGEM_PACTO_PROIBIDO = "https://i.imgur.com/MX7rQpp.png"

# 🚫 Cargos protegidos
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
    1487891283102924961
]


# =========================
# VIEW
# =========================

class PactoProibidoView(discord.ui.View):
    def __init__(self, membro: discord.Member):
        super().__init__(timeout=300)

        self.membro = membro
        self.respondido = False

    @discord.ui.button(
        label="Aceitar Pacto",
        emoji="☠️",
        style=discord.ButtonStyle.danger
    )
    async def aceitar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

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

        adicionar_moedas(
            self.membro.id,
            RECOMPENSA_PACTO
        )

        cargo_removido = None

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
                "O Cassino do Diabo aceitou sua decisão.\n\n"

                f"🪙 Você recebeu "
                f"**{RECOMPENSA_PACTO:,} Moedas do Diabo**.\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                f"{f'🎭 Cargo perdido: **{cargo_removido.name}**' if cargo_removido else '🎭 Nenhum cargo pôde ser removido.'}\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "> A casa sempre cobra."
            ),
            color=0x8B0000
        )

        embed.set_image(url=IMAGEM_PACTO_PROIBIDO)

        embed.set_footer(
            text="Cassino do Diabo • Pacto Proibido"
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    @discord.ui.button(
        label="Recusar",
        emoji="❌",
        style=discord.ButtonStyle.secondary
    )
    async def recusar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.membro.id:
            await interaction.response.send_message(
                "❌ Este pacto não pertence a você.",
                ephemeral=True
            )
            return

        self.respondido = True

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="📜 PACTO RECUSADO",
            description=(
                "Você recusou a proposta do Cassino.\n\n"

                "> Talvez ele não ofereça novamente."
            ),
            color=0x2C2C2C
        )

        embed.set_image(url=IMAGEM_PACTO_PROIBIDO)

        embed.set_footer(
            text="Cassino do Diabo • Pacto Proibido"
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )


# =========================
# COG
# =========================

class Pactos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # evita spam
        self.cooldown_dm = set()

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

        embed = discord.Embed(
            title="☠️ UMA CARTA NEGRA APARECEU",
            description=(
                "O Cassino do Diabo observou suas ações.\n\n"

                "Um **Pacto Proibido** foi enviado diretamente a você.\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                f"🪙 Recompensa:\n"
                f"**{RECOMPENSA_PACTO:,} Moedas do Diabo**\n\n"

                "🎭 Consequência:\n"
                "Você perderá um cargo aleatório.\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "Aceitar este pacto pode mudar "
                "sua posição dentro da Família.\n\n"

                "> Toda fortuna exige um sacrifício."
            ),
            color=0x8B0000
        )

        embed.set_image(url=IMAGEM_PACTO_PROIBIDO)

        embed.set_footer(
            text="Cassino do Diabo • Pacto Proibido"
        )

        try:
            await message.author.send(
                embed=embed,
                view=PactoProibidoView(message.author)
            )

        except discord.Forbidden:
            pass


# =========================
# SETUP
# =========================

async def setup(bot):
    await bot.add_cog(Pactos(bot))