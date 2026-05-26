import os
import random
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands
from discord import app_commands

from utils.cassino_db import (
    obter_usuario,
    obter_saldo,
    adicionar_moedas,
    transferir_moedas,
    atualizar_daily,
    ranking_ricos
)

GUILD_ID = int(os.getenv("GUILD_ID", "0"))

COR_CASSINO  = 0x8B0000
COR_DOURADO  = 0xD4AF37
COR_VERDE    = 0x2ECC71
COR_CINZA    = 0x2C2C2C

SEPARADOR = "```\n ─────────────────────────── \n```"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#              CONFIGURAÇÃO DO DAILY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DAILY_MIN       = 30000
DAILY_MAX       = 42000
DAILY_BONUS_MIN = 11000   
DAILY_BONUS_MAX = 56000
STREAK_BONUS    = 3      

# Frases temáticas para o daily
FRASES_DAILY = [
    "O Dealer reconheceu sua presença.",
    "A casa presenteia os que retornam.",
    "Sua lealdade tem preço. E foi pago.",
    "O Cassino anotou mais um dia seu.",
    "Quem aparece, recebe. Quem some, perde.",
    "O Diabo honra sua palavra — por hoje.",
    "Mais um dia, mais uma moeda no contrato.",
]

FRASES_STREAK = [
    "Sua dedicação não passou despercebida.",
    "O Dealer sorriu para sua constância.",
    "Dias consecutivos. O Cassino recompensa.",
    "Lealdade prolongada merece recompensa maior.",
]


class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # streak em memória {user_id: {"dias": int, "ultimo": date}}
        self._streaks: dict[int, dict] = {}

    def _calcular_streak(self, uid: int, ultima_daily: str | None) -> int:
        """Calcula dias consecutivos de daily."""
        if not ultima_daily:
            return 1
        try:
            ultima = datetime.fromisoformat(ultima_daily).date()
        except Exception:
            return 1
        hoje = datetime.now(timezone.utc).date()
        ontem = hoje - timedelta(days=1)

        dados = self._streaks.get(uid, {"dias": 1})
        if ultima == ontem:
            novo = dados["dias"] + 1
        elif ultima == hoje:
            novo = dados["dias"]
        else:
            novo = 1
        self._streaks[uid] = {"dias": novo}
        return novo

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #                   /saldo
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @app_commands.command(name="saldo", description="Veja seu saldo de Moedas do Diabo.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def saldo(self, interaction: discord.Interaction, membro: discord.Member = None):
        alvo   = membro or interaction.user
        dados  = obter_usuario(alvo.id)
        moedas       = dados[1]
        total_ganho  = dados[2]
        total_perdido= dados[3]

        streak = self._streaks.get(alvo.id, {}).get("dias", 0)
        streak_txt = f"🔥 **{streak}** dias consecutivos" if streak > 1 else "—"

        embed = discord.Embed(
            title="🪙  Saldo do Cassino",
            description=(
                f"-# *\"A casa registrou sua fortuna.\"*\n\n"
                f"👤 **Membro:** {alvo.mention}\n\n"
                f"{SEPARADOR}"
                f"🪙 **Moedas do Diabo**\n### {moedas:,}\n\n"
                f"📈 Total ganho: **{total_ganho:,}**\n"
                f"📉 Total perdido: **{total_perdido:,}**\n\n"
                f"🔥 Streak diário: {streak_txt}"
            ),
            color=COR_DOURADO
        )
        embed.set_thumbnail(url=alvo.display_avatar.url)
        embed.set_footer(text="👁️ Cassino do Diabo  •  A casa sempre observa")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #                   /daily
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @app_commands.command(name="daily", description="Receba sua recompensa diária do Cassino.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def daily(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            dados = obter_usuario(interaction.user.id)
        except Exception:
            return await interaction.followup.send(
                "❌ Erro ao acessar o banco de dados. Tente novamente.", ephemeral=True)

        ultima_daily = dados[4] if dados and len(dados) > 4 else None
        agora = datetime.now(timezone.utc)

        # ── Verificação de cooldown ──────────────────
        if ultima_daily:
            try:
                ultima = datetime.fromisoformat(ultima_daily)
                if ultima.tzinfo is None:
                    ultima = ultima.replace(tzinfo=timezone.utc)
                proximo = ultima + timedelta(hours=24)

                if agora < proximo:
                    restante  = proximo - agora
                    horas     = int(restante.total_seconds() // 3600)
                    minutos   = int((restante.total_seconds() % 3600) // 60)
                    ts_proximo = int(proximo.timestamp())

                    embed = discord.Embed(
                        title="⏳  Recompensa Indisponível",
                        description=(
                            f"-# *\"A casa ainda não liberou sua próxima recompensa.\"*\n\n"
                            f"{SEPARADOR}"
                            f"🕐 Próxima recompensa: <t:{ts_proximo}:R>\n\n"
                            f"Faltam **{horas}h {minutos}min**.\n\n"
                            f"> *Paciência também é uma aposta.*"
                        ),
                        color=COR_CINZA
                    )
                    embed.set_thumbnail(url=interaction.user.display_avatar.url)
                    embed.set_footer(text="👁️ Cassino do Diabo  •  Paciência também é aposta")
                    embed.timestamp = discord.utils.utcnow()
                    return await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception:
                pass  # Se falhar no parse, deixa pegar o daily

        # ── Calcula streak e recompensa ──────────────
        streak     = self._calcular_streak(interaction.user.id, ultima_daily)
        recompensa = random.randint(DAILY_MIN, DAILY_MAX)
        bonus      = 0
        bonus_txt  = ""

        if streak >= STREAK_BONUS:
            bonus = random.randint(DAILY_BONUS_MIN, DAILY_BONUS_MAX)
            bonus_txt = (
                f"\n\n🔥 **Bônus de Streak** (+{streak} dias)\n"
                f"🪙 **+{bonus:,} Moedas extras!**"
            )

        total = recompensa + bonus

        # ── Salva no banco ───────────────────────────
        try:
            adicionar_moedas(interaction.user.id, total)
            atualizar_daily(interaction.user.id)
        except Exception as e:
            return await interaction.followup.send(
                f"❌ Erro ao salvar recompensa: `{e}`", ephemeral=True)

        # ── Embed de sucesso ─────────────────────────
        frase = random.choice(FRASES_STREAK if streak >= STREAK_BONUS else FRASES_DAILY)
        streak_bar = "🔥" * min(streak, 10) + ("..." if streak > 10 else "")

        embed = discord.Embed(
            title="🎁  Recompensa Diária",
            description=(
                f"-# *\"{frase}\"*\n\n"
                f"{SEPARADOR}"
                f"🪙 **+{recompensa:,} Moedas do Diabo**"
                f"{bonus_txt}\n\n"
                f"{'━' * 20}\n\n"
                f"💰 **Total recebido:** {total:,} moedas\n\n"
                f"🔥 Streak atual: {streak_bar} **{streak} dia(s)**"
            ),
            color=COR_DOURADO if streak < STREAK_BONUS else 0xFF6B35
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="👁️ Cassino do Diabo  •  Retorne amanhã")
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #                   /pay
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @app_commands.command(name="pay", description="Envie Moedas do Diabo para outro membro.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def pay(self, interaction: discord.Interaction, membro: discord.Member, quantidade: int):
        if membro.bot:
            return await interaction.response.send_message(
                "❌ Você não pode enviar moedas para bots.", ephemeral=True)
        if membro.id == interaction.user.id:
            return await interaction.response.send_message(
                "❌ Você não pode enviar moedas para si mesmo.", ephemeral=True)
        if quantidade <= 0:
            return await interaction.response.send_message(
                "❌ Informe uma quantidade válida (maior que 0).", ephemeral=True)

        sucesso = transferir_moedas(interaction.user.id, membro.id, quantidade)
        if not sucesso:
            return await interaction.response.send_message(
                "❌ Você não possui Moedas do Diabo suficientes.", ephemeral=True)

        embed = discord.Embed(
            title="💸  Transferência Registrada",
            description=(
                f"-# *\"O cassino observou a movimentação.\"*\n\n"
                f"{SEPARADOR}"
                f"📤 **De:** {interaction.user.mention}\n"
                f"📥 **Para:** {membro.mention}\n"
                f"🪙 **Valor:** {quantidade:,} Moedas do Diabo\n\n"
                f"> *Toda dívida deixa rastros.*"
            ),
            color=COR_DOURADO
        )
        embed.set_footer(text="👁️ Cassino do Diabo  •  Toda dívida deixa rastros")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

        # Notifica o destinatário
        try:
            aviso = discord.Embed(
                title="🪙  Você recebeu Moedas do Diabo!",
                description=(
                    f"{interaction.user.mention} enviou **{quantidade:,} Moedas do Diabo** para você.\n\n"
                    f"> *O Cassino registrou a transação.*"
                ),
                color=COR_VERDE
            )
            aviso.set_footer(text="👁️ Cassino do Diabo  •  Transferência recebida")
            aviso.timestamp = discord.utils.utcnow()
            await membro.send(embed=aviso)
        except Exception:
            pass

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #                  /ranking
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @app_commands.command(name="ranking", description="Veja os membros mais ricos do Cassino.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ranking(self, interaction: discord.Interaction):
        dados = ranking_ricos(10)
        if not dados:
            return await interaction.response.send_message(
                "📊 Ainda não há jogadores no ranking.", ephemeral=True)

        medalhas = ["👑", "🥈", "🥉"]
        linhas   = []

        for pos, (user_id, moedas) in enumerate(dados, start=1):
            alvo   = interaction.guild.get_member(user_id)
            nome   = alvo.mention if alvo else f"`{user_id}`"
            medal  = medalhas[pos - 1] if pos <= 3 else f"`{pos}.`"
            streak = self._streaks.get(user_id, {}).get("dias", 0)
            streak_txt = f" 🔥{streak}" if streak > 1 else ""
            linhas.append(f"{medal} {nome} — 🪙 **{moedas:,}**{streak_txt}")

        embed = discord.Embed(
            title="🏆  Ranking das Moedas do Diabo",
            description=(
                f"-# *\"Riqueza, poder e corrupção.\"*\n\n"
                f"{SEPARADOR}"
                + "\n".join(linhas)
            ),
            color=COR_DOURADO
        )
        embed.set_footer(text="👁️ Cassino do Diabo  •  Riqueza, poder e corrupção")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Economia(bot))