# cogs/levels.py

import os
import random
import asyncpg
import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta

LEVEL_TITLES = [
    (75, "🩸 Soberano do Vazio"),
    (50,  "👁️ Portador do Haki Negro"),
    (20,  "☠️ Caçador de Recompensas"),
    (10,  "🌊 Navegador da Grand Line"),
    (5,   "⚓ Marinheiro Perdido"),
]


ROLE_REWARDS = {
    5:   1489690725246308473,  # ⚓ Marinheiro Perdido
    10:  1489690908797567197,  # 🌊 Navegador da Grand Line
    20:  1489691028536557620,  # ☠️ Caçador de Recompensas
    50:  1489691179963388206,  # 👁️ Portador do Haki Negro
    75:  1489691407840055450,  # 🩸 Soberano do Vazio
}

XP_BONUS_ROLES: dict[int, float] = {

    123456789012345678: 1.5,   
    1480334522053558465: 2.0,   
    1486411238513836052: 3.00,  
}

LEVELUP_CHANNEL_ID = int(os.getenv("LEVELUP_CHANNEL_ID", 0))


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pool = None
        self.cooldowns: dict[str, datetime] = {}

    # ── Inicialização do banco de dados ──────────────────────────────────────
    async def cog_load(self):
        self.pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
        await self.criar_tabela()

    async def criar_tabela(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS levels (
                    guild_id   BIGINT  NOT NULL,
                    user_id    BIGINT  NOT NULL,
                    xp         BIGINT  NOT NULL DEFAULT 0,
                    level      INTEGER NOT NULL DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (guild_id, user_id)
                );
            """)

    # ── Lógica de XP e nível ─────────────────────────────────────────────────

    def xp_necessario(self, level: int) -> int:
        return 100 + (level * level * 85)

    def titulo_por_level(self, level: int) -> str:
        for required_level, title in LEVEL_TITLES:
            if level >= required_level:
                return title
        return "⚓ Marinheiro Perdido"

    def calcular_level(self, xp: int) -> int:
        level = 1
        while xp >= self.xp_necessario(level + 1):
            level += 1
        return level

    def xp_para_proximo(self, xp_total: int, level_atual: int) -> tuple[int, int, int]:
        xp_inicio_level   = self.xp_necessario(level_atual)
        xp_inicio_proximo = self.xp_necessario(level_atual + 1)
        xp_atual_no_level = xp_total - xp_inicio_level
        xp_necessario_level = xp_inicio_proximo - xp_inicio_level
        falta = xp_inicio_proximo - xp_total
        return xp_atual_no_level, xp_necessario_level, falta

    def calcular_multiplicador(self, member: discord.Member) -> float:
        """
        Verifica se o membro tem algum cargo com bônus de XP.
        Retorna o MAIOR multiplicador encontrado, ou 1.0 se nenhum.
        """
        ids_do_membro = {role.id for role in member.roles}
        multiplicadores = [
            mult for role_id, mult in XP_BONUS_ROLES.items()
            if role_id in ids_do_membro
        ]
        return max(multiplicadores, default=1.0)

    async def aplicar_cargo(self, member: discord.Member, level: int):
        if level not in ROLE_REWARDS:
            return
        role = member.guild.get_role(ROLE_REWARDS[level])
        if role and role not in member.roles:
            await member.add_roles(role, reason="Recompensa de nível")

    # ── Embed de level-up ────────────────────────────────────────────────────

    def montar_embed_levelup(
        self,
        member: discord.Member,
        level_novo: int,
        xp_total: int,
        xp_ganho: int,
        multiplicador: float,
    ) -> discord.Embed:
        titulo = self.titulo_por_level(level_novo)
        xp_atual_no_level, xp_necessario_level, falta = self.xp_para_proximo(xp_total, level_novo)

        blocos_cheios = int((xp_atual_no_level / xp_necessario_level) * 10)
        barra = "█" * blocos_cheios + "░" * (10 - blocos_cheios)

        # Mostra o bônus apenas se ele foi aplicado
        bonus_linha = ""
        if multiplicador > 1.0:
            bonus_linha = f"**✦ Bônus de XP:** `x{multiplicador}` (+{xp_ganho - round(xp_ganho / multiplicador)} XP extras)\n"

        embed = discord.Embed(
            title="🏴‍☠️  Novo Nível Alcançado!",
            description=(
                f"### {member.mention} avançou nos mares!\n\n"
                f"**✦ Nível:** `{level_novo}`\n"
                f"**✦ Título:** {titulo}\n"
                f"{bonus_linha}"
                f"\n──────────────────────\n"
                f"**Progresso para o Nível {level_novo + 1}**\n"
                f"`{barra}` `{xp_atual_no_level}/{xp_necessario_level} XP`\n\n"
                f"> 📌 Faltam **{falta} XP** para alcançar o **Nível {level_novo + 1}**!\n"
                f"──────────────────────"
            ),
            color=discord.Color.from_rgb(212, 175, 55),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(
            text=f"⚓  O grande rei de tudo chegará em breve aqui... • XP Total: {xp_total}"
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1500528332008325281/1509780209002610778/content.png?ex=6a1a6be4&is=6a191a64&hm=c4b7f3ff29107bdd5e6ef1bec9178240b53eb31244ea8eddb391bfe409fb0b92&")
        return embed

    # ── Listener de mensagem ─────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        user_id  = message.author.id
        guild_id = message.guild.id
        key      = f"{guild_id}:{user_id}"
        now      = datetime.now(timezone.utc)

        if (last := self.cooldowns.get(key)) and now - last < timedelta(seconds=60):
            return

        self.cooldowns[key] = now

        # Calcula o XP base e aplica o multiplicador de cargo
        xp_base  = random.randint(15, 35)
        mult     = self.calcular_multiplicador(message.author)
        xp_ganho = round(xp_base * mult)

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO levels (guild_id, user_id, xp, level, updated_at)
                VALUES ($1, $2, $3, 1, NOW())
                ON CONFLICT (guild_id, user_id)
                DO UPDATE SET
                    xp         = levels.xp + EXCLUDED.xp,
                    updated_at = NOW()
                RETURNING xp, level;
            """, guild_id, user_id, xp_ganho)

            xp_total     = row["xp"]
            level_antigo = row["level"]
            level_novo   = self.calcular_level(xp_total)

            if level_novo > level_antigo:
                await conn.execute("""
                    UPDATE levels SET level = $1
                    WHERE guild_id = $2 AND user_id = $3
                """, level_novo, guild_id, user_id)

                await self.aplicar_cargo(message.author, level_novo)

                embed = self.montar_embed_levelup(
                    message.author, level_novo, xp_total, xp_ganho, mult
                )

                canal_destino = None
                if LEVELUP_CHANNEL_ID:
                    canal_destino = message.guild.get_channel(LEVELUP_CHANNEL_ID)
                canal_destino = canal_destino or message.channel
                await canal_destino.send(embed=embed)

    # ── Comando !rank ─────────────────────────────────────────────────────────

    @commands.command(name="rank")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT xp, level FROM levels
                WHERE guild_id = $1 AND user_id = $2
            """, ctx.guild.id, member.id)

            if not row:
                return await ctx.reply(
                    f"{member.mention} ainda não começou sua jornada pelos mares. "
                    "Mande uma mensagem para ganhar XP!"
                )

            xp    = row["xp"]
            level = row["level"]
            titulo = self.titulo_por_level(level)
            xp_atual_no_level, xp_necessario_level, falta = self.xp_para_proximo(xp, level)

            blocos_cheios = int((xp_atual_no_level / xp_necessario_level) * 10)
            barra = "█" * blocos_cheios + "░" * (10 - blocos_cheios)

            posicao = await conn.fetchval("""
                SELECT posicao FROM (
                    SELECT user_id, RANK() OVER (ORDER BY xp DESC) AS posicao
                    FROM levels WHERE guild_id = $1
                ) ranking WHERE user_id = $2
            """, ctx.guild.id, member.id)

        # Mostra o multiplicador ativo do membro
        mult = self.calcular_multiplicador(member)
        mult_linha = f"**✦ Bônus de XP:** `x{mult}`\n" if mult > 1.0 else ""

        embed = discord.Embed(
            title="⚓  Registro de Jornada",
            description=(
                f"{member.mention}\n\n"
                f"**✦ Título:** {titulo}\n"
                f"**✦ Nível:** `{level}`\n"
                f"**✦ Ranking:** `#{posicao}`\n"
                f"{mult_linha}"
                f"\n──────────────────────\n"
                f"**Progresso para o Nível {level + 1}**\n"
                f"`{barra}` `{xp_atual_no_level}/{xp_necessario_level} XP`\n\n"
                f"> 📌 Faltam **{falta} XP** para o próximo nível!\n"
                f"──────────────────────\n"
                f"**XP Total acumulado:** `{xp}`"
            ),
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Continue navegando para alcançar águas mais perigosas.")
        await ctx.reply(embed=embed)

    # ── Comando !top ──────────────────────────────────────────────────────────

    @commands.command(name="top")
    async def top(self, ctx):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id, xp, level FROM levels
                WHERE guild_id = $1
                ORDER BY xp DESC LIMIT 10
            """, ctx.guild.id)

        if not rows:
            return await ctx.reply("Ainda não há piratas registrados neste mar.")

        descricao = ""
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}

        for index, row in enumerate(rows, start=1):
            titulo  = self.titulo_por_level(row["level"])
            medalha = medals.get(index, f"**{index}.**")
            descricao += (
                f"{medalha} <@{row['user_id']}>\n"
                f"╰ `Nível {row['level']}` · `{row['xp']} XP` · {titulo}\n\n"
            )

        embed = discord.Embed(
            title="🏴‍☠️  Os Piratas Mais Temidos",
            description=descricao,
            color=discord.Color.dark_gold(),
        )
        embed.set_footer(text="Os nomes mais temidos dos mares da Grand Line.")
        await ctx.reply(embed=embed)

    # ── Comando !setxp (apenas admins) ───────────────────────────────────────

    @commands.command(name="setxp")
    @commands.has_permissions(administrator=True)
    async def setxp(self, ctx, member: discord.Member, xp: int):
        if xp < 0:
            return await ctx.reply("O XP não pode ser negativo.")
        level_novo = self.calcular_level(xp)
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO levels (guild_id, user_id, xp, level, updated_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (guild_id, user_id)
                DO UPDATE SET xp = $3, level = $4, updated_at = NOW()
            """, ctx.guild.id, member.id, xp, level_novo)
        await ctx.reply(
            f"✅ XP de {member.mention} definido para **{xp}** (Nível `{level_novo}`)."
        )

    # ── Comando !addxp (apenas admins) ───────────────────────────────────────

    @commands.command(name="addxp")
    @commands.has_permissions(administrator=True)
    async def addxp(self, ctx, member: discord.Member, xp: int):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO levels (guild_id, user_id, xp, level, updated_at)
                VALUES ($1, $2, GREATEST(0, $3), 1, NOW())
                ON CONFLICT (guild_id, user_id)
                DO UPDATE SET
                    xp         = GREATEST(0, levels.xp + $3),
                    updated_at = NOW()
                RETURNING xp, level;
            """, ctx.guild.id, member.id, xp)
            xp_total   = row["xp"]
            level_novo = self.calcular_level(xp_total)
            await conn.execute("""
                UPDATE levels SET level = $1
                WHERE guild_id = $2 AND user_id = $3
            """, level_novo, ctx.guild.id, member.id)
        sinal = "+" if xp >= 0 else ""
        await ctx.reply(
            f"✅ {sinal}{xp} XP aplicado a {member.mention}. "
            f"Total: **{xp_total} XP** · Nível `{level_novo}`."
        )


async def setup(bot):
    await bot.add_cog(Levels(bot))