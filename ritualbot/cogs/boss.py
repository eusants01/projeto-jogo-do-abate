import random
import discord
from discord.ext import commands

from utils.db import (
    buscar_jogador,
    adicionar_abate,
    remover_vida,
    listar_jogadores_vivos,
    conectar,
    resetar_jogo,
)

COR_VERMELHA = 0xE63946
COR_VERDE = 0x2ECC71
COR_ROXA = 0x7B2CFF

VIDAS_MAXIMAS = 300
CANAL_LOG_MALDICOES_ID = 1500543560834089272

BOSS_ATIVO = None

BOSSES = [
    {
        "nome": "Sukuna",
        "descricao": "O Rei das Maldições abriu seu domínio.",
        "imagem": "https://c.tenor.com/w3KbwTJ-F5IAAAAd/tenor.gif",
        "vida": 45000,
        "tempo": 600,
        "dano_min": 18,
        "dano_max": 38,
        "recompensa_participou": 1,
        "recompensa_top": 5,
        "recompensa_final": 3,
        "dano_falha": 12,
        "agressividade": 1,
        "agressividade_max": 8,
        "chance_ataque": 30,
        "chance_habilidade": 25,
        "habilidade": "corte_area",
        "dano_habilidade": 18,
        "drop_lendario": "Fragmento do Rei das Maldições",
    },
    {
        "nome": "Mahoraga",
        "descricao": "A roda gira. A adaptação começou.",
        "imagem": "https://c.tenor.com/mS_lFC5waJcAAAAC/tenor.gif",
        "vida": 27000,
        "tempo": 600,
        "dano_min": 14,
        "dano_max": 32,
        "recompensa_participou": 1,
        "recompensa_top": 4,
        "recompensa_final": 3,
        "dano_falha": 10,
        "agressividade": 1,
        "agressividade_max": 7,
        "chance_ataque": 22,
        "chance_habilidade": 45,
        "habilidade": "adaptacao",
        "dano_habilidade": 14,
        "drop_lendario": "Roda da Adaptação",
    },
    {
        "nome": "Brunaandsants",
        "descricao": "Uma história que jamais será apagada.",
        "imagem": "https://c.tenor.com/m__ZnOd5kF8AAAAd/tenor.gif",
        "vida": 30000,
        "tempo": 600,
        "dano_min": 12,
        "dano_max": 30,
        "recompensa_participou": 1,
        "recompensa_top": 4,
        "recompensa_final": 3,
        "dano_falha": 16,
        "agressividade": 1,
        "agressividade_max": 10,
        "chance_ataque": 25,
        "chance_habilidade": 35,
        "habilidade": "pacto_eterno",
        "dano_habilidade": 20,
        "drop_lendario": "Pacto Eterno",
    },
    {
        "nome": "Rika",
        "descricao": "Uma força esmagadora apareceu.",
        "imagem": "https://c.tenor.com/7z8vSgeTDq0AAAAd/tenor.gif",
        "vida": 28000,
        "tempo": 600,
        "dano_min": 10,
        "dano_max": 28,
        "recompensa_participou": 1,
        "recompensa_top": 3,
        "recompensa_final": 2,
        "dano_falha": 8,
        "agressividade": 1,
        "agressividade_max": 6,
        "chance_ataque": 18,
        "chance_habilidade": 30,
        "habilidade": "grito",
        "dano_habilidade": 16,
        "drop_lendario": "Olhar da Rainha das Maldições",
    },
]


def buscar_boss(nome: str):
    if not nome:
        return None

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


def resetar_vidas_todos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE jogadores
        SET vidas = ?, status = 'vivo', alvo_id = NULL
        """,
        (VIDAS_MAXIMAS,)
    )

    conn.commit()
    conn.close()


def sortear_drop(boss_nome: str, boss_drop_lendario: str):
    chance = random.randint(1, 100)

    if chance <= 5:
        return {
            "raridade": "LENDÁRIO",
            "emoji": "🌟",
            "nome": boss_drop_lendario,
            "bonus_abate": 8,
        }

    if chance <= 18:
        return {
            "raridade": "ÉPICO",
            "emoji": "🟣",
            "nome": f"Relíquia de {boss_nome}",
            "bonus_abate": 5,
        }

    if chance <= 45:
        return {
            "raridade": "RARO",
            "emoji": "🔵",
            "nome": f"Marca de {boss_nome}",
            "bonus_abate": 3,
        }

    return {
        "raridade": "COMUM",
        "emoji": "⚪",
        "nome": "Fragmento Amaldiçoado",
        "bonus_abate": 1,
    }


class BossView(discord.ui.View):
    def __init__(self, boss):
        super().__init__(timeout=boss["tempo"])
        self.boss = boss.copy()
        self.vida = self.boss["vida"]
        self.max_vida = self.boss["vida"]
        self.danos = {}
        self.finalizado = False
        self.mensagem = None
        self.ultimo_hit = None
        self.agressividade = self.boss.get("agressividade", 1)
        self.agressividade_max = self.boss.get("agressividade_max", 5)
        self.turnos = 0

    def barra(self):
        if self.max_vida <= 0:
            return "⬛" * 10

        pct = max(0, self.vida) / self.max_vida

        if pct <= 0.10:
            cheio = max(1, round(pct * 10))
            return "🔥" * cheio + "⬛" * (10 - cheio)

        if pct <= 0.30:
            cheio = max(1, round(pct * 10))
            return "🟧" * cheio + "⬛" * (10 - cheio)

        if pct <= 0.60:
            cheio = max(1, round(pct * 10))
            return "🟨" * cheio + "⬛" * (10 - cheio)

        cheio = round(pct * 10)
        return "🟥" * cheio + "⬛" * (10 - cheio)

    def estado_boss(self):
        pct = max(0, self.vida) / self.max_vida

        if pct <= 0.10:
            return "🔥 **CRÍTICO — O boss está desesperado.**"

        if pct <= 0.30:
            return "🟧 **Fúria elevada — ataques mais perigosos.**"

        if pct <= 0.60:
            return "🟨 **Instável — a pressão está aumentando.**"

        return "🟥 **Controle inicial — o boss ainda está firme.**"

    def embed(self):
        ranking = sorted(self.danos.items(), key=lambda x: x[1], reverse=True)[:5]

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
                f"{self.estado_boss()}\n"
                f"🔥 **Agressividade:** `{self.agressividade}/{self.agressividade_max}`\n"
                f"⏳ Tempo limite: **{self.boss['tempo'] // 60} minutos**"
            ),
            color=COR_VERMELHA
        )

        embed.add_field(name="🏆 Ranking de Dano", value=texto, inline=False)
        embed.set_image(url=self.boss["imagem"])
        embed.set_footer(text="Família Sant's • Raid Boss")
        return embed

    async def usar_habilidade(self, interaction: discord.Interaction):
        habilidade = self.boss.get("habilidade")
        dano_base = self.boss.get("dano_habilidade", 0)

        if not habilidade or dano_base <= 0:
            return

        if random.randint(1, 100) > self.boss.get("chance_habilidade", 25):
            return

        jogadores = listar_jogadores_vivos()

        if not jogadores:
            return

        dano = max(1, int((dano_base * 0.6) + self.agressividade))

        if habilidade == "corte_area":
            alvos = random.sample(jogadores, min(3, len(jogadores)))
            texto = f"🔥 **{self.boss['nome']} usou CORTE EM ÁREA!**\n"

            for jogador in alvos:
                user_id = jogador[0]
                resultado = remover_vida(user_id, dano)

                if resultado:
                    vidas = resultado[2]
                    status = resultado[5]
                    texto += f"🩸 <@{user_id}> recebeu **-{dano}** dano. ❤️ `{vidas}/{VIDAS_MAXIMAS}`"

                    if status == "eliminado":
                        texto += " ☠️ **ELIMINADO**"

                    texto += "\n"

            await interaction.channel.send(texto)

        elif habilidade == "adaptacao":
            self.agressividade = min(self.agressividade + 1, self.agressividade_max)
            self.boss["dano_min"] += 1
            self.boss["dano_max"] += 1

            await interaction.channel.send(
                f"⚙️ **{self.boss['nome']} se adaptou ao dano recebido!**\n"
                f"🔥 Agressividade atual: **{self.agressividade}/{self.agressividade_max}**"
            )

        elif habilidade == "grito":
            resultado = remover_vida(interaction.user.id, dano)

            if resultado:
                vidas = resultado[2]
                status = resultado[5]
                texto = (
                    f"👁️ **{self.boss['nome']} soltou um GRITO AMALDIÇOADO!**\n"
                    f"🎯 Alvo: {interaction.user.mention}\n"
                    f"🩸 Dano: **-{dano}**\n"
                    f"❤️ Vida restante: **{vidas}/{VIDAS_MAXIMAS}**"
                )

                if status == "eliminado":
                    texto += "\n☠️ **ELIMINADO**"

                await interaction.channel.send(texto)

        elif habilidade == "pacto_eterno":
            alvos = random.sample(jogadores, min(2, len(jogadores)))
            cura = min(5000, self.max_vida - self.vida)
            self.vida += cura

            texto = (
                f"💜 **{self.boss['nome']} ativou PACTO ETERNO!**\n"
                f"❤️ O boss recuperou **{cura}** de vida.\n"
            )

            for jogador in alvos:
                user_id = jogador[0]
                resultado = remover_vida(user_id, dano)

                if resultado:
                    vidas = resultado[2]
                    status = resultado[5]
                    texto += f"🩸 <@{user_id}> recebeu **-{dano}** dano. ❤️ `{vidas}/{VIDAS_MAXIMAS}`"

                    if status == "eliminado":
                        texto += " ☠️ **ELIMINADO**"

                    texto += "\n"

            await interaction.channel.send(texto)

    async def finalizar(self, channel: discord.TextChannel, guild: discord.Guild):
        global BOSS_ATIVO
        BOSS_ATIVO = None

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

        drop_top = sortear_drop(
            self.boss["nome"],
            self.boss.get("drop_lendario", "Artefato Lendário")
        )
        drop_final = sortear_drop(
            self.boss["nome"],
            self.boss.get("drop_lendario", "Artefato Lendário")
        )

        if buscar_jogador(top):
            adicionar_abate(top, drop_top["bonus_abate"])

        if self.ultimo_hit and buscar_jogador(self.ultimo_hit):
            adicionar_abate(self.ultimo_hit, drop_final["bonus_abate"])

        ranking = sorted(self.danos.items(), key=lambda x: x[1], reverse=True)[:5]

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
                f"🎁 **Recompensas fixas:**\n"
                f"• Participou: +{self.boss['recompensa_participou']} abate(s)\n"
                f"• Top dano: +{self.boss['recompensa_top']} abate(s)\n"
                f"• Golpe final: +{self.boss['recompensa_final']} abate(s)"
            ),
            color=COR_VERDE
        )

        embed.add_field(name="📊 Ranking Final", value=texto_ranking, inline=False)
        embed.add_field(
            name="🎁 Drop do Maior Dano",
            value=(
                f"{drop_top['emoji']} **{drop_top['raridade']}**\n"
                f"Item: **{drop_top['nome']}**\n"
                f"Bônus: +{drop_top['bonus_abate']} abate(s)\n"
                f"Recebedor: <@{top}>"
            ),
            inline=False
        )
        embed.add_field(
            name="⚔️ Drop do Golpe Final",
            value=(
                f"{drop_final['emoji']} **{drop_final['raridade']}**\n"
                f"Item: **{drop_final['nome']}**\n"
                f"Bônus: +{drop_final['bonus_abate']} abate(s)\n"
                f"Recebedor: <@{self.ultimo_hit}>"
            ),
            inline=False
        )
        embed.set_footer(text="Família Sant's • Raid Boss Finalizado")

        await channel.send(embed=embed)
        await enviar_log(guild, embed)

    async def on_timeout(self):
        global BOSS_ATIVO

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
        dano_final = max(1, int((self.boss["dano_falha"] * 0.7) + self.agressividade))
        texto_atingidos = ""

        for jogador in atingidos:
            user_id = jogador[0]
            resultado = remover_vida(user_id, dano_final)

            if resultado:
                vidas = resultado[2]
                status = resultado[5]
                texto_atingidos += (
                    f"💀 <@{user_id}> perdeu **{dano_final}** vida(s). "
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

        BOSS_ATIVO = None

        if self.mensagem:
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

        self.turnos += 1

        if self.turnos % 8 == 0 and self.agressividade < self.agressividade_max:
            self.agressividade += 1

        dano = random.randint(self.boss["dano_min"], self.boss["dano_max"])
        self.vida -= dano
        self.danos[interaction.user.id] = self.danos.get(interaction.user.id, 0) + dano
        self.ultimo_hit = interaction.user.id

        await interaction.response.edit_message(embed=self.embed(), view=self)

        if random.randint(1, 100) <= self.boss.get("chance_ataque", 20):
            dano_boss = random.randint(
                max(1, int(self.boss["dano_falha"] * 0.4)),
                max(2, int(self.boss["dano_falha"] * 0.7))
            ) + self.agressividade

            resultado = remover_vida(interaction.user.id, dano_boss)

            if resultado:
                vidas = resultado[2]
                status = resultado[5]
                texto = (
                    f"💢 **{self.boss['nome']} contra-atacou!**\n"
                    f"🎯 Alvo: {interaction.user.mention}\n"
                    f"🩸 Dano: **-{dano_boss}**\n"
                    f"❤️ Vida restante: **{vidas}/{VIDAS_MAXIMAS}**"
                )

                if status == "eliminado":
                    texto += "\n☠️ **ELIMINADO**"

                await interaction.followup.send(texto, ephemeral=True)

        await self.usar_habilidade(interaction)

        if self.vida <= 0:
            self.vida = 0
            self.finalizado = True

            for item in self.children:
                item.disabled = True

            try:
                await self.mensagem.edit(embed=self.embed(), view=self)
            except Exception:
                pass

            await self.finalizar(interaction.channel, interaction.guild)


class Boss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="boss")
    @commands.has_permissions(administrator=True)
    async def boss(self, ctx, *, nome=None):
        global BOSS_ATIVO

        try:
            await ctx.message.delete()
        except Exception:
            pass

        if BOSS_ATIVO is not None:
            await ctx.send(
                "⚠️ Já existe um **boss ativo** no servidor.\n"
                "Derrote ou aguarde ele acabar antes de invocar outro.",
                delete_after=12
            )
            return

        boss = buscar_boss(nome) if nome else random.choice(BOSSES)

        if not boss:
            nomes = ", ".join([b["nome"] for b in BOSSES])
            await ctx.send(
                f"❌ Boss não encontrado.\nUse: `{nomes}`",
                delete_after=10
            )
            return

        view = BossView(boss)
        msg = await ctx.send(embed=view.embed(), view=view)
        view.mensagem = msg
        BOSS_ATIVO = view

    @commands.command(name="limpar_boss")
    @commands.has_permissions(administrator=True)
    async def limpar_boss(self, ctx):
        global BOSS_ATIVO

        try:
            await ctx.message.delete()
        except Exception:
            pass

        BOSS_ATIVO = None

        await ctx.send(
            "🧹 Boss ativo limpo manualmente. Agora outro boss pode ser invocado.",
            delete_after=10
        )

    @commands.command(name="resetar_vida", aliases=["vidas"])
    @commands.has_permissions(administrator=True)
    async def resetar_vida(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        resetar_vidas_todos()

        await ctx.send(
            f"❤️ **Vidas restauradas!**\n"
            f"Todos os jogadores voltaram para **{VIDAS_MAXIMAS}/{VIDAS_MAXIMAS}** e status **vivo**.",
            delete_after=12
        )

    @commands.command(name="resetar_tudo", aliases=["reset_tudo"])
    @commands.has_permissions(administrator=True)
    async def resetar_tudo(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        resetar_jogo()

        await ctx.send(
            "🩸 **Jogo do Abate resetado completamente.**\n"
            "Todos os registros foram apagados.",
            delete_after=12
        )

    @limpar_boss.error
    async def limpar_boss_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply(
                "❌ Apenas administradores podem limpar boss ativo.",
                delete_after=8
            )
        else:
            await ctx.reply(
                "⚠️ Ocorreu um erro ao limpar o boss ativo.",
                delete_after=8
            )
            print(f"[ERRO LIMPAR BOSS] {error}")

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

    @resetar_vida.error
    async def resetar_vida_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply(
                "❌ Apenas administradores podem resetar as vidas.",
                delete_after=8
            )
        else:
            await ctx.reply(
                "⚠️ Ocorreu um erro ao resetar vidas.",
                delete_after=8
            )
            print(f"[ERRO RESETAR VIDA] {error}")

    @resetar_tudo.error
    async def resetar_tudo_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply(
                "❌ Apenas administradores podem resetar o jogo.",
                delete_after=8
            )
        else:
            await ctx.reply(
                "⚠️ Ocorreu um erro ao resetar tudo.",
                delete_after=8
            )
            print(f"[ERRO RESETAR TUDO] {error}")


async def setup(bot):
    await bot.add_cog(Boss(bot))
