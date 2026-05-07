import random
import discord
from discord.ext import commands

from utils.db import (
    buscar_jogador,
    registrar_jogador,
    adicionar_abate,
    remover_vida,
    listar_jogadores_vivos,
    listar_ranking,
    conectar,
    resetar_jogo,
)

from utils.economia import (
    criar_tabelas_economia,
    adicionar_item,
    consumir_buff,
    adicionar_buff,
    pegar_corrupcao,
    pegar_buffs,
    quantidade_item,
)

COR_VERMELHA = 0xE63946
COR_VERDE = 0x2ECC71
COR_ROXA = 0x7B2CFF
COR_DOURADA = 0xF1C40F

VIDAS_MAXIMAS = 750
CANAL_LOG_MALDICOES_ID = 1500543560834089272
TEMPO_APAGAR_ATAQUE = 3
BOSS_ATIVO = None

ITEM_FRAGMENTO = "Fragmento Amaldiçoado"
BANNER_ABATE = "https://i.imgur.com/ypNuTwX.png"

BOSSES = [
    {
        "nome": "Sukuna",
        "descricao": "O Rei das Maldições abriu seu domínio.",
        "imagem": "https://c.tenor.com/w3KbwTJ-F5IAAAAd/tenor.gif",
        "vida": 25000,
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
        "vida": 15000,
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
        "nome": "Bruna e Sants",
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
        "vida": 20000,
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
        await canal.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())


def resetar_vidas_todos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE jogadores
        SET vidas = %s, status = 'vivo', alvo_id = NULL
        """,
        (VIDAS_MAXIMAS,)
    )
    conn.commit()
    conn.close()


def sortear_drop(boss_nome: str, boss_drop_lendario: str):
    chance = random.randint(1, 100)
    if chance <= 5:
        return {"raridade": "LENDÁRIO", "emoji": "🌟", "nome": boss_drop_lendario, "bonus_abate": 8, "fragmentos": 80}
    if chance <= 18:
        return {"raridade": "ÉPICO", "emoji": "🟣", "nome": f"Relíquia de {boss_nome}", "bonus_abate": 5, "fragmentos": 45}
    if chance <= 45:
        return {"raridade": "RARO", "emoji": "🔵", "nome": f"Marca de {boss_nome}", "bonus_abate": 3, "fragmentos": 25}
    return {"raridade": "COMUM", "emoji": "⚪", "nome": ITEM_FRAGMENTO, "bonus_abate": 1, "fragmentos": 15}


def aplicar_dano_com_escudo(user_id: int, dano: int):
    if consumir_buff(user_id, "escudo", 1):
        dano = max(0, dano - 8)

    if dano <= 0:
        return buscar_jogador(user_id), 0, True

    return remover_vida(user_id, dano), dano, False



def texto_mencao(user_id: int):
    return f"<@{user_id}>"


def criar_embed_painel_abate():
    embed = discord.Embed(
        title="🩸 Central do Jogo do Abate",
        description=(
            "Bem-vindo(a) ao **ritual principal** da Família Sant's.\n\n"
            "Use este painel para entrar no ritual, consultar seu status, acompanhar ranking "
            "e verificar se existe um boss ativo.\n\n"
            "⚔️ Derrote bosses\n"
            "🧩 Ganhe fragmentos\n"
            "🎁 Colete drops\n"
            "🛒 Use buffs da Loja Amaldiçoada"
        ),
        color=COR_ROXA
    )
    embed.add_field(
        name="🎮 Ações",
        value=(
            "⚔️ **Entrar no Ritual** — registra você no jogo\n"
            "❤️ **Meu Status** — vida, abates, fragmentos, buffs e corrupção\n"
            "🏆 **Ranking** — top jogadores do abate\n"
            "👹 **Boss Atual** — consulta o boss ativo\n"
            "📜 **Regras** — explicação rápida"
        ),
        inline=False
    )
    embed.set_image(url=BANNER_ABATE)
    embed.set_footer(text="Família Sant's • Jogo do Abate")
    return embed


class PainelAbateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Entrar no Ritual", emoji="⚔️", style=discord.ButtonStyle.danger, custom_id="abate_entrar_v2")
    async def entrar_ritual(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogador = buscar_jogador(interaction.user.id)
        if jogador:
            await interaction.response.send_message("⚠️ Você já está registrado no **Jogo do Abate**.", ephemeral=True)
            return

        registrar_jogador(interaction.user.id, interaction.user.display_name)
        await interaction.response.send_message(
            f"🩸 **Registro concluído!**\nVocê entrou no ritual com **{VIDAS_MAXIMAS}/{VIDAS_MAXIMAS}** vidas.",
            ephemeral=True
        )

    @discord.ui.button(label="Meu Status", emoji="❤️", style=discord.ButtonStyle.secondary, custom_id="abate_status_v2")
    async def meu_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogador = buscar_jogador(interaction.user.id)
        if not jogador:
            await interaction.response.send_message("🚫 Você ainda não está registrado. Clique em **Entrar no Ritual**.", ephemeral=True)
            return

        saldo = quantidade_item(interaction.user.id, ITEM_FRAGMENTO)
        buffs = pegar_buffs(interaction.user.id)
        corrupcao = pegar_corrupcao(interaction.user.id)

        texto_buffs = "Nenhum buff ativo."
        if buffs:
            texto_buffs = "\n".join([f"• **{buff}** x{qtd}" for buff, qtd in buffs])

        embed = discord.Embed(
            title=f"❤️ Status de {interaction.user.display_name}",
            description=(
                f"❤️ Vida: **{jogador[2]}/{VIDAS_MAXIMAS}**\n"
                f"🩸 Abates: **{jogador[3]}**\n"
                f"📜 Contratos: **{jogador[4]}**\n"
                f"💀 Status: **{jogador[5]}**\n"
                f"🏯 Família: **{jogador[7]}**\n"
                f"🧩 Fragmentos: **{saldo}**\n"
                f"🧫 Corrupção: **{corrupcao}**"
            ),
            color=COR_ROXA
        )
        embed.add_field(name="✨ Buffs ativos", value=texto_buffs[:1024], inline=False)
        embed.set_footer(text="Família Sant's • Status do Abate")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Ranking", emoji="🏆", style=discord.ButtonStyle.secondary, custom_id="abate_ranking_v2")
    async def ranking(self, interaction: discord.Interaction, button: discord.ui.Button):
        ranking = listar_ranking()
        if not ranking:
            await interaction.response.send_message("📊 Ainda não há jogadores no ranking.", ephemeral=True)
            return

        texto = ""
        for posicao, jogador in enumerate(ranking, start=1):
            user_id, username, vidas, abates, contratos, status, familia = jogador
            medalha = ["🥇", "🥈", "🥉"][posicao - 1] if posicao <= 3 else f"`#{posicao}`"
            texto += f"{medalha} **{username}** — 🩸 {abates} abate(s) | ❤️ {vidas}/{VIDAS_MAXIMAS}\n"

        embed = discord.Embed(title="🏆 Ranking do Jogo do Abate", description=texto, color=COR_DOURADA)
        embed.set_footer(text="Família Sant's • Ranking do Abate")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Boss Atual", emoji="👹", style=discord.ButtonStyle.primary, custom_id="abate_boss_atual_v2")
    async def boss_atual(self, interaction: discord.Interaction, button: discord.ui.Button):
        global BOSS_ATIVO
        if not BOSS_ATIVO:
            await interaction.response.send_message("👹 Nenhum boss está ativo no momento.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"👹 Boss ativo: **{BOSS_ATIVO.boss['nome']}**\n"
            f"❤️ Vida: **{max(0, BOSS_ATIVO.vida)}/{BOSS_ATIVO.max_vida}**\n"
            f"🔥 Agressividade: **{BOSS_ATIVO.agressividade}/{BOSS_ATIVO.agressividade_max}**",
            ephemeral=True
        )

    @discord.ui.button(label="Regras", emoji="📜", style=discord.ButtonStyle.secondary, custom_id="abate_regras_v2")
    async def regras(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📜 Regras rápidas do Abate",
            description=(
                "1. Entre no ritual antes de atacar bosses.\n"
                "2. Apenas jogadores vivos podem atacar.\n"
                "3. Bosses podem contra-atacar e usar habilidades.\n"
                "4. Use a loja para comprar **Escudo**, **Fúria**, **Crítico** e outros buffs.\n"
                "5. Ao derrotar bosses, participantes recebem fragmentos e drops.\n"
                "6. Admins controlam invocação e resets."
            ),
            color=COR_ROXA
        )
        embed.set_footer(text="Família Sant's • Regras do Abate")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class BossView(discord.ui.View):
    def __init__(self, boss):
        super().__init__(timeout=boss["tempo"])
        self.boss = boss.copy()
        self.vida = self.boss["vida"]
        self.max_vida = self.boss["vida"]
        self.danos = {}
        self.finalizado = False
        self.recompensas_entregues = False
        self.mensagem = None
        self.ultimo_hit = None
        self.agressividade = self.boss.get("agressividade", 1)
        self.agressividade_max = self.boss.get("agressividade_max", 5)
        self.turnos = 0

    def barra(self):
        if self.max_vida <= 0:
            return "⬛" * 10
        pct = max(0, self.vida) / self.max_vida
        cheio = max(1, round(pct * 10)) if pct > 0 else 0
        if pct <= 0.10:
            return "🔥" * cheio + "⬛" * (10 - cheio)
        if pct <= 0.30:
            return "🟧" * cheio + "⬛" * (10 - cheio)
        if pct <= 0.60:
            return "🟨" * cheio + "⬛" * (10 - cheio)
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
                f"⏳ Tempo limite: **{self.boss['tempo'] // 60} minutos**\n\n"
                f"✨ Loja ativa: use `!comprar escudo` ou `!comprar furia` antes de atacar."
            ),
            color=COR_VERMELHA
        )
        embed.add_field(name="🏆 Ranking de Dano", value=texto, inline=False)
        embed.set_image(url=self.boss["imagem"])
        embed.set_footer(text="Família Sant's • Raid Boss")
        return embed

    async def enviar_ataque_temporario(self, canal, texto: str):
        await canal.send(texto, delete_after=TEMPO_APAGAR_ATAQUE)

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
                resultado, dano_final, protegido = aplicar_dano_com_escudo(user_id, dano)
                if resultado:
                    vidas = resultado[2]
                    status = resultado[5]
                    texto += f"🩸 <@{user_id}> recebeu **-{dano_final}** dano"
                    if protegido:
                        texto += " 🛡️ **Escudo ativado**"
                    texto += f". ❤️ `{vidas}/{VIDAS_MAXIMAS}`"
                    if status == "eliminado":
                        texto += " ☠️ **ELIMINADO**"
                    texto += "\n"
            await self.enviar_ataque_temporario(interaction.channel, texto)

        elif habilidade == "adaptacao":
            self.agressividade = min(self.agressividade + 1, self.agressividade_max)
            self.boss["dano_min"] += 1
            self.boss["dano_max"] += 1
            await self.enviar_ataque_temporario(
                interaction.channel,
                f"⚙️ **{self.boss['nome']} se adaptou ao dano recebido!**\n🔥 Agressividade: **{self.agressividade}/{self.agressividade_max}**"
            )

        elif habilidade == "grito":
            resultado, dano_final, protegido = aplicar_dano_com_escudo(interaction.user.id, dano)
            if resultado:
                vidas = resultado[2]
                status = resultado[5]
                texto = (
                    f"👁️ **{self.boss['nome']} soltou um GRITO AMALDIÇOADO!**\n"
                    f"🎯 Alvo: {interaction.user.mention}\n"
                    f"🩸 Dano: **-{dano_final}**"
                )
                if protegido:
                    texto += "\n🛡️ Escudo ativado."
                texto += f"\n❤️ Vida restante: **{vidas}/{VIDAS_MAXIMAS}**"
                if status == "eliminado":
                    texto += "\n☠️ **ELIMINADO**"
                await self.enviar_ataque_temporario(interaction.channel, texto)

        elif habilidade == "pacto_eterno":
            alvos = random.sample(jogadores, min(2, len(jogadores)))
            cura = min(5000, self.max_vida - self.vida)
            self.vida += cura
            texto = f"💜 **{self.boss['nome']} ativou PACTO ETERNO!**\n❤️ O boss recuperou **{cura}** de vida.\n"
            for jogador in alvos:
                user_id = jogador[0]
                resultado, dano_final, protegido = aplicar_dano_com_escudo(user_id, dano)
                if resultado:
                    vidas = resultado[2]
                    status = resultado[5]
                    texto += f"🩸 <@{user_id}> recebeu **-{dano_final}** dano"
                    if protegido:
                        texto += " 🛡️ **Escudo ativado**"
                    texto += f". ❤️ `{vidas}/{VIDAS_MAXIMAS}`"
                    if status == "eliminado":
                        texto += " ☠️ **ELIMINADO**"
                    texto += "\n"
            await self.enviar_ataque_temporario(interaction.channel, texto)

    async def finalizar(self, channel: discord.TextChannel, guild: discord.Guild):
        global BOSS_ATIVO

        if self.recompensas_entregues:
            return

        self.recompensas_entregues = True
        self.finalizado = True
        BOSS_ATIVO = None

        for item in self.children:
            item.disabled = True

        if self.mensagem:
            try:
                await self.mensagem.edit(embed=self.embed(), view=None)
            except Exception:
                pass

        if not self.danos:
            return

        top = max(self.danos, key=self.danos.get)

        for uid in self.danos:
            if buscar_jogador(uid):
                adicionar_abate(uid, self.boss["recompensa_participou"])
                adicionar_item(uid, ITEM_FRAGMENTO, 10)

        if buscar_jogador(top):
            adicionar_abate(top, self.boss["recompensa_top"])

        if self.ultimo_hit and buscar_jogador(self.ultimo_hit):
            adicionar_abate(self.ultimo_hit, self.boss["recompensa_final"])

        drop_top = sortear_drop(self.boss["nome"], self.boss.get("drop_lendario", "Artefato Lendário"))
        drop_final = sortear_drop(self.boss["nome"], self.boss.get("drop_lendario", "Artefato Lendário"))

        adicionar_item(top, drop_top["nome"], 1)
        adicionar_item(top, ITEM_FRAGMENTO, drop_top["fragmentos"])

        if self.ultimo_hit:
            adicionar_item(self.ultimo_hit, drop_final["nome"], 1)
            adicionar_item(self.ultimo_hit, ITEM_FRAGMENTO, drop_final["fragmentos"])

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
                f"• Participou: +{self.boss['recompensa_participou']} abate(s) + 🧩 10 fragmentos\n"
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
                f"🧩 Fragmentos: **+{drop_top['fragmentos']}**\n"
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
                f"🧩 Fragmentos: **+{drop_final['fragmentos']}**\n"
                f"Bônus: +{drop_final['bonus_abate']} abate(s)\n"
                f"Recebedor: <@{self.ultimo_hit}>"
            ),
            inline=False
        )
        embed.set_footer(text="Família Sant's • Raid Boss Finalizado")
        await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        await enviar_log(guild, embed)

    async def on_timeout(self):
        global BOSS_ATIVO
        if self.finalizado or getattr(self, "recompensas_entregues", False):
            return

        self.finalizado = True
        BOSS_ATIVO = None

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
            resultado, dano_real, protegido = aplicar_dano_com_escudo(user_id, dano_final)
            if resultado:
                vidas = resultado[2]
                status = resultado[5]
                texto_atingidos += f"💀 <@{user_id}> perdeu **{dano_real}** vida(s)"
                if protegido:
                    texto_atingidos += " 🛡️ **Escudo ativado**"
                texto_atingidos += f". ❤️ `{vidas}/{VIDAS_MAXIMAS}`"
                if status == "eliminado":
                    texto_atingidos += " ☠️ **ELIMINADO**"
                texto_atingidos += "\n"

        embed = discord.Embed(
            title="☠️ O BOSS VENCEU",
            description=f"💀 **{self.boss['nome']}** não foi derrotado a tempo.\n\n{texto_atingidos}",
            color=COR_VERMELHA
        )
        embed.set_footer(text="Família Sant's • Raid Boss")

        if self.mensagem:
            await self.mensagem.channel.send(embed=embed)
            await enviar_log(self.mensagem.guild, embed)

    @discord.ui.button(label="Atacar", emoji="⚔️", style=discord.ButtonStyle.danger, custom_id="boss_atacar")
    async def atacar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finalizado or self.recompensas_entregues:
            await interaction.response.send_message("💀 Esse boss já foi finalizado.", ephemeral=True)
            return

        jogador = buscar_jogador(interaction.user.id)
        if not jogador:
            await interaction.response.send_message("🚫 Você precisa entrar no **Jogo do Abate** antes de atacar bosses.", ephemeral=True)
            return

        if jogador[5] != "vivo":
            await interaction.response.send_message("💀 Você está eliminado e não pode atacar bosses.", ephemeral=True)
            return

        self.turnos += 1
        if self.turnos % 8 == 0 and self.agressividade < self.agressividade_max:
            self.agressividade += 1

        dano = random.randint(self.boss["dano_min"], self.boss["dano_max"])

        if consumir_buff(interaction.user.id, "furia", 1):
            extra = random.randint(25, 60)
            dano += extra
            await interaction.channel.send(
                f"🔥 {interaction.user.mention} ativou **Fúria Amaldiçoada** e causou **+{extra}** de dano!",
                delete_after=5,
                allowed_mentions=discord.AllowedMentions.none()
            )

        if consumir_buff(interaction.user.id, "critico", 1):
            dano *= 2
            await interaction.channel.send(
                f"💥 {interaction.user.mention} ativou **Golpe Crítico** e dobrou o dano!",
                delete_after=5,
                allowed_mentions=discord.AllowedMentions.none()
            )

        if consumir_buff(interaction.user.id, "berserk", 1):
            extra = random.randint(80, 140)
            dano += extra
            aplicar_dano_com_escudo(interaction.user.id, 15)
            await interaction.channel.send(
                f"☠️ {interaction.user.mention} ativou **Berserk Amaldiçoado**: +{extra} dano, mas sofreu dano de retorno.",
                delete_after=6,
                allowed_mentions=discord.AllowedMentions.none()
            )

        self.vida -= dano
        self.danos[interaction.user.id] = self.danos.get(interaction.user.id, 0) + dano
        self.ultimo_hit = interaction.user.id

        await interaction.response.edit_message(embed=self.embed(), view=self)

        if random.randint(1, 100) <= self.boss.get("chance_ataque", 20):
            dano_boss = random.randint(
                max(1, int(self.boss["dano_falha"] * 0.4)),
                max(2, int(self.boss["dano_falha"] * 0.7))
            ) + self.agressividade

            resultado, dano_real, protegido = aplicar_dano_com_escudo(interaction.user.id, dano_boss)
            if resultado:
                vidas = resultado[2]
                status = resultado[5]
                texto = (
                    f"💢 **{self.boss['nome']} contra-atacou!**\n"
                    f"🎯 Alvo: {interaction.user.mention}\n"
                    f"🩸 Dano: **-{dano_real}**"
                )
                if protegido:
                    texto += "\n🛡️ Escudo ativado."
                texto += f"\n❤️ Vida restante: **{vidas}/{VIDAS_MAXIMAS}**"
                if status == "eliminado":
                    texto += "\n☠️ **ELIMINADO**"
                await self.enviar_ataque_temporario(interaction.channel, texto)

        await self.usar_habilidade(interaction)

        if self.vida <= 0:
            self.vida = 0
            self.finalizado = True
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(embed=self.embed(), view=None)
            await self.finalizar(interaction.channel, interaction.guild)
            return


class Boss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        criar_tabelas_economia()


    @commands.command(name="painel_abate")
    @commands.has_permissions(administrator=True)
    async def painel_abate(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        await ctx.send(embed=criar_embed_painel_abate(), view=PainelAbateView())

    @painel_abate.error
    async def painel_abate_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ Apenas administradores podem criar o painel do abate.", delete_after=8)
        else:
            await ctx.reply("⚠️ Ocorreu um erro ao criar o painel do abate.", delete_after=8)
            print(f"[ERRO PAINEL ABATE] {error}")

    @commands.command(name="boss")
    @commands.has_permissions(administrator=True)
    async def boss(self, ctx, *, nome=None):
        global BOSS_ATIVO

        try:
            await ctx.message.delete()
        except Exception:
            pass

        if BOSS_ATIVO is not None:
            await ctx.send("⚠️ Já existe um **boss ativo** no servidor.", delete_after=12)
            return

        boss = buscar_boss(nome) if nome else random.choice(BOSSES)

        if not boss:
            nomes = ", ".join([b["nome"] for b in BOSSES])
            await ctx.send(f"❌ Boss não encontrado.\nUse: `{nomes}`", delete_after=10)
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
        await ctx.send("🧹 Boss ativo limpo manualmente.", delete_after=10)

    @commands.command(name="resetar_vida", aliases=["vidas"])
    @commands.has_permissions(administrator=True)
    async def resetar_vida(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        resetar_vidas_todos()
        await ctx.send(
            f"❤️ Vidas restauradas para **{VIDAS_MAXIMAS}/{VIDAS_MAXIMAS}**.",
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
        await ctx.send("🩸 **Jogo do Abate resetado completamente.**", delete_after=12)


async def setup(bot):
    bot.add_view(PainelAbateView())
    await bot.add_cog(Boss(bot))
    
