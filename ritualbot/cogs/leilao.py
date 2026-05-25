import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

import discord
from discord.ext import commands

from utils.cassino_db import obter_saldo, remover_moedas, adicionar_moedas

# ──────────────────────────────────────────────
#  CONFIGURAÇÕES
# ──────────────────────────────────────────────

CANAL_LEILAO_ID = 1503972510285168691

BANNER_LEILAO = (
    "https://cdn.discordapp.com/attachments/961677475191078992/"
    "1506536746278719578/48a63abb-0e0c-4859-8518-5846b51ed4c1.png"
    "?ex=6a0e9f2e&is=6a0d4dae&hm=b5a3fd40fd1837ad3d509aaa155495be8927e6ba290619d850c7d0d36732e22c&"
)

TEMPO_PADRAO_SEGUNDOS   = 10 * 60   # 10 min
ANTI_SNIPER_SEGUNDOS    = 30        
EXTENSAO_ANTI_SNIPER    = 60        
MAXIMO_EXTENSOES        = 5         
ATUALIZACAO_INTERVALO   = 10        
MINIMO_INCREMENT        = 1         

COR_LEILAO  = 0x8B0000
COR_DOURADO = 0xD4AF37
COR_ESCURO  = 0x1A0000
COR_ERRO    = 0xFF4444

CARGOS_CRIAR_LEILAO: list[int] = [
    1508350514847289454,  # Criador de Leilões / Sants rsrs
    1508350520864413700,  # Gerente de Leilões / N/A
]

log = logging.getLogger("leilao")


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def pode_criar_leilao(membro: discord.Member) -> bool:
    """Retorna True se o membro pode iniciar um leilão."""
    if membro.guild_permissions.administrator:
        return True
    cargos_ids = {cargo.id for cargo in membro.roles}
    return bool(cargos_ids & set(CARGOS_CRIAR_LEILAO))


def formatar_moedas(valor: int) -> str:
    return f"🪙 `{valor:,.0f}`".replace(",", ".")


def formatar_tempo(segundos: int) -> str:
    if segundos <= 0:
        return "⏰ Encerrando..."
    h, resto = divmod(segundos, 3600)
    m, s = divmod(resto, 60)
    if h:
        return f"{h}h {m:02d}min {s:02d}s"
    if m:
        return f"{m}min {s:02d}s"
    return f"{s}s"


def parsear_valor(raw: str) -> Optional[int]:
    """Converte string para inteiro, aceitando pontos/vírgulas como separadores."""
    try:
        limpo = raw.strip().replace(".", "").replace(",", "").replace(" ", "")
        return int(limpo)
    except (ValueError, AttributeError):
        return None

@dataclass
class EstadoLeilao:
    item: str
    descricao: str
    lance_minimo: int
    autor_id: int

    lance_atual: int = 0
    maior_apostador: Optional[discord.Member] = None
    historico: list[tuple[str, int, float]] = field(default_factory=list)
    finalizado: bool = False
    extensoes: int = 0
    fim: float = field(default_factory=lambda: time.time() + TEMPO_PADRAO_SEGUNDOS)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    @property
    def valor_exibido(self) -> int:
        return self.lance_atual if self.lance_atual > 0 else self.lance_minimo

    @property
    def minimo_proximo_lance(self) -> int:
        if self.lance_atual == 0:
            return self.lance_minimo
        return self.lance_atual + MINIMO_INCREMENT

    def segundos_restantes(self) -> int:
        return max(0, int(self.fim - time.time()))

    def esta_vivo(self) -> bool:
        return not self.finalizado and self.segundos_restantes() > 0

    def aplicar_anti_sniper(self) -> bool:
        """Prorroga tempo se houver snipe. Retorna True se prorrogou."""
        if (
            self.segundos_restantes() <= ANTI_SNIPER_SEGUNDOS
            and self.extensoes < MAXIMO_EXTENSOES
        ):
            self.fim += EXTENSAO_ANTI_SNIPER
            self.extensoes += 1
            return True
        return False


# ──────────────────────────────────────────────
#  MODAIS
# ──────────────────────────────────────────────

class CriarLeilaoModal(discord.ui.Modal, title="🎰 Criar Leilão do Diabo"):
    item = discord.ui.TextInput(
        label="Item do leilão",
        placeholder="Ex: Cargo VIP, Gamepass, Nitro…",
        required=True,
        max_length=80,
    )
    descricao = discord.ui.TextInput(
        label="Descrição do item",
        placeholder="Explique o que será entregue ao vencedor.",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=700,
    )
    lance_inicial = discord.ui.TextInput(
        label="Lance inicial (mínimo aceito)",
        placeholder="Ex: 1000",
        required=True,
        max_length=12,
    )

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        valor = parsear_valor(self.lance_inicial.value)
        if valor is None or valor <= 0:
            return await interaction.response.send_message(
                "❌ Lance inicial inválido. Use apenas números maiores que zero.",
                ephemeral=True,
            )

        canal = interaction.guild.get_channel(CANAL_LEILAO_ID)
        if canal is None:
            return await interaction.response.send_message(
                "❌ Canal de leilão não encontrado. Verifique o `CANAL_LEILAO_ID`.",
                ephemeral=True,
            )

        estado = EstadoLeilao(
            item=self.item.value.strip(),
            descricao=self.descricao.value.strip(),
            lance_minimo=valor,
            autor_id=interaction.user.id,
        )

        view = LeilaoView(estado)
        msg = await canal.send(embed=view.build_embed(), view=view)
        view.mensagem = msg

        # Agenda finalização sem bloquear o handler
        asyncio.create_task(view.ciclo_vida(), name=f"leilao_{msg.id}")

        log.info(
            "Leilão criado por %s | item=%r | mínimo=%d",
            interaction.user,
            estado.item,
            valor,
        )

        await interaction.response.send_message(
            f"✅ Leilão criado com sucesso em {canal.mention}!",
            ephemeral=True,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        log.exception("Erro em CriarLeilaoModal", exc_info=error)
        await interaction.response.send_message(
            "⚠️ Ocorreu um erro inesperado ao criar o leilão.",
            ephemeral=True,
        )


class LanceModal(discord.ui.Modal, title="💰 Fazer Lance"):
    valor = discord.ui.TextInput(
        label="Valor do lance",
        placeholder="Ex: 5000",
        required=True,
        max_length=12,
    )

    def __init__(self, view: "LeilaoView"):
        super().__init__()
        self._leilao_view = view

    async def on_submit(self, interaction: discord.Interaction):
        valor = parsear_valor(self.valor.value)
        if valor is None:
            return await interaction.response.send_message(
                "❌ Valor inválido. Use apenas números.",
                ephemeral=True,
            )
        await self._leilao_view.processar_lance(interaction, valor)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        log.exception("Erro em LanceModal", exc_info=error)
        await interaction.response.send_message(
            "⚠️ Erro ao processar seu lance.",
            ephemeral=True,
        )


# ──────────────────────────────────────────────
#  VIEW DO LEILÃO ATIVO
# ──────────────────────────────────────────────

class LeilaoView(discord.ui.View):
    def __init__(self, estado: EstadoLeilao):
        super().__init__(timeout=None)
        self.estado = estado
        self.mensagem: Optional[discord.Message] = None

    # ── Embeds ──────────────────────────────────

    def build_embed(self) -> discord.Embed:
        e = self.estado
        apostador = e.maior_apostador.mention if e.maior_apostador else "*(nenhum ainda)*"
        valor = e.valor_exibido

        linhas_hist = [
            f"`#{i:02d}` **{nome}** — {formatar_moedas(lance)}"
            for i, (nome, lance, _) in enumerate(reversed(e.historico[-8:]), 1)
        ] or ["*Nenhum lance registrado ainda.*"]

        barra_tempo = self._barra_progresso()
        extensao_aviso = (
            f"\n⚡ *Prorrogado {e.extensoes}×* (Anti-Sniper ativo)"
            if e.extensoes > 0 else ""
        )

        embed = discord.Embed(
            title="🎰 LEILÃO DO DIABO",
            description=(
                "Senhoras e senhores, a mesa foi aberta.\n"
                "Somente os mais ousados sairão com o prêmio.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📦 **Item em leilão:**\n**{e.item}**\n\n"
                f"📜 **Descrição:**\n{e.descricao}\n\n"
                f"💰 **Lance atual:** {formatar_moedas(valor)}\n"
                f"👑 **Maior apostador:** {apostador}\n"
                f"🔢 **Mínimo próximo:** {formatar_moedas(e.minimo_proximo_lance)}\n"
                f"⏳ **Tempo restante:** `{formatar_tempo(e.segundos_restantes())}`\n"
                f"{barra_tempo}{extensao_aviso}\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🎲 **Regras:**\n"
                "• Lance cobrado imediatamente.\n"
                "• Superado? Suas moedas voltam.\n"
                "• Lances no final estendem o tempo.\n\n"
                "> *A casa sempre observa.*"
            ),
            color=COR_LEILAO,
        )

        embed.add_field(
            name=f"📊 Últimos Lances ({len(e.historico)} total)",
            value="\n".join(linhas_hist),
            inline=False,
        )
        embed.set_image(url=BANNER_LEILAO)
        embed.set_footer(text="Família Sant's • Leilão do Diabo")
        return embed

    def build_embed_finalizado(self) -> discord.Embed:
        e = self.estado
        if e.maior_apostador:
            embed = discord.Embed(
                title="🏆 LEILÃO FINALIZADO",
                description=(
                    "O martelo caiu. A casa reconheceu o vencedor.\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📦 **Item:** {e.item}\n"
                    f"👑 **Vencedor:** {e.maior_apostador.mention}\n"
                    f"💰 **Lance final:** {formatar_moedas(e.lance_atual)}\n"
                    f"🔢 **Total de lances:** {len(e.historico)}\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "> O pagamento foi realizado automaticamente."
                ),
                color=COR_DOURADO,
            )
        else:
            embed = discord.Embed(
                title="☠️ LEILÃO ENCERRADO SEM VENCEDOR",
                description=(
                    f"📦 **Item:** {e.item}\n\n"
                    "Nenhum lance foi realizado.\n\n"
                    "> *Nem todos tiveram coragem de sentar à mesa.*"
                ),
                color=COR_ESCURO,
            )
        embed.set_image(url=BANNER_LEILAO)
        embed.set_footer(text="Família Sant's • Leilão do Diabo")
        return embed

    def _barra_progresso(self) -> str:
        total = TEMPO_PADRAO_SEGUNDOS + (self.estado.extensoes * EXTENSAO_ANTI_SNIPER)
        restante = self.estado.segundos_restantes()
        proporcao = max(0.0, min(1.0, restante / total))
        blocos = 20
        cheios = int(proporcao * blocos)
        return "\n`[" + "█" * cheios + "░" * (blocos - cheios) + "]`"

    # ── Lógica de lance ──────────────────────────

    async def processar_lance(self, interaction: discord.Interaction, valor: int):
        e = self.estado

        async with e._lock:
            # 1. Leilão ainda ativo?
            if e.finalizado:
                return await interaction.response.send_message(
                    "❌ Este leilão já foi finalizado.", ephemeral=True
                )
            if not e.esta_vivo():
                return await interaction.response.send_message(
                    "❌ O tempo deste leilão expirou.", ephemeral=True
                )

            # 2. Usuário já lidera?
            if e.maior_apostador and interaction.user.id == e.maior_apostador.id:
                return await interaction.response.send_message(
                    "⚠️ Você já possui o maior lance! Aguarde ser superado.", ephemeral=True
                )

            # 3. Valor mínimo
            minimo = e.minimo_proximo_lance
            if valor < minimo:
                return await interaction.response.send_message(
                    f"❌ Lance mínimo: **{formatar_moedas(minimo)}**\n"
                    f"Você tentou: {formatar_moedas(valor)}",
                    ephemeral=True,
                )

            # 4. Saldo suficiente
            saldo = obter_saldo(interaction.user.id)
            if saldo < valor:
                return await interaction.response.send_message(
                    f"❌ Saldo insuficiente.\n"
                    f"Seu saldo: {formatar_moedas(saldo)}\n"
                    f"Lance desejado: {formatar_moedas(valor)}",
                    ephemeral=True,
                )

            # 5. Transação
            anterior_apostador = e.maior_apostador
            anterior_lance = e.lance_atual

            remover_moedas(interaction.user.id, valor)

            if anterior_apostador is not None:
                adicionar_moedas(anterior_apostador.id, anterior_lance)

            # 6. Atualiza estado
            e.lance_atual = valor
            e.maior_apostador = interaction.user
            e.historico.append((interaction.user.display_name, valor, time.time()))

            # 7. Anti-sniper
            prorrogou = e.aplicar_anti_sniper()

        # Fora do lock: responder e atualizar embed
        aviso_sniper = (
            f"\n⚡ *Tempo estendido em {EXTENSAO_ANTI_SNIPER}s! (Anti-Sniper)*"
            if prorrogou else ""
        )

        await interaction.response.send_message(
            f"✅ Lance registrado: **{formatar_moedas(valor)}**{aviso_sniper}",
            ephemeral=True,
        )

        log.info(
            "Lance: %s → %d | leilão: %s",
            interaction.user,
            valor,
            self.estado.item,
        )

        await self._atualizar_embed()

    # ── Atualização do embed ─────────────────────

    async def _atualizar_embed(self):
        if self.mensagem:
            try:
                await self.mensagem.edit(embed=self.build_embed(), view=self)
            except discord.HTTPException as exc:
                log.warning("Falha ao atualizar embed: %s", exc)

    # ── Ciclo de vida ────────────────────────────

    async def ciclo_vida(self):
        """Loop principal: atualiza embed periodicamente e finaliza ao expirar."""
        while self.estado.esta_vivo():
            await asyncio.sleep(ATUALIZACAO_INTERVALO)
            if not self.estado.finalizado:
                await self._atualizar_embed()

        await self._finalizar()

    async def _finalizar(self):
        e = self.estado

        async with e._lock:
            if e.finalizado:
                return
            e.finalizado = True

        # Desabilita botões
        for item in self.children:
            item.disabled = True

        # Notifica vencedor por DM (melhor UX)
        if e.maior_apostador:
            try:
                await e.maior_apostador.send(
                    f"🏆 Você venceu o leilão **{e.item}** com um lance de "
                    f"{formatar_moedas(e.lance_atual)}!\n"
                    "Entre em contato com a administração para resgatar seu prêmio."
                )
            except discord.Forbidden:
                log.info("DM bloqueada para %s", e.maior_apostador)

        if self.mensagem:
            try:
                await self.mensagem.edit(embed=self.build_embed_finalizado(), view=self)
            except discord.HTTPException as exc:
                log.error("Falha ao editar embed final: %s", exc)

        log.info(
            "Leilão finalizado | item=%r | vencedor=%s | lance=%d | lances_total=%d",
            e.item,
            e.maior_apostador,
            e.lance_atual,
            len(e.historico),
        )

    # ── Botões ───────────────────────────────────

    @discord.ui.button(
        label="Dar Lance",
        emoji="💰",
        style=discord.ButtonStyle.danger,
        custom_id="leilao_lance",
        row=0,
    )
    async def btn_dar_lance(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(LanceModal(self))

    @discord.ui.button(
        label="+500",
        emoji="🪙",
        style=discord.ButtonStyle.secondary,
        custom_id="leilao_500",
        row=0,
    )
    async def btn_500(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.processar_lance(interaction, self.estado.valor_exibido + 500)

    @discord.ui.button(
        label="+1.000",
        emoji="🪙",
        style=discord.ButtonStyle.secondary,
        custom_id="leilao_1000",
        row=0,
    )
    async def btn_1000(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.processar_lance(interaction, self.estado.valor_exibido + 1_000)

    @discord.ui.button(
        label="+5.000",
        emoji="🪙",
        style=discord.ButtonStyle.secondary,
        custom_id="leilao_5000",
        row=0,
    )
    async def btn_5000(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.processar_lance(interaction, self.estado.valor_exibido + 5_000)

    @discord.ui.button(
        label="Histórico",
        emoji="📜",
        style=discord.ButtonStyle.secondary,
        custom_id="leilao_historico",
        row=1,
    )
    async def btn_historico(self, interaction: discord.Interaction, button: discord.ui.Button):
        e = self.estado
        if not e.historico:
            return await interaction.response.send_message(
                "📜 Nenhum lance registrado ainda.", ephemeral=True
            )

        linhas = [
            f"`#{i:02d}` **{nome}** — {formatar_moedas(lance)}"
            for i, (nome, lance, _) in enumerate(reversed(e.historico), 1)
        ]
        # Paginação simples (máx 20 por embed)
        embed = discord.Embed(
            title=f"📜 Histórico — {e.item}",
            description="\n".join(linhas[:20]),
            color=COR_LEILAO,
        )
        embed.set_footer(text=f"{len(e.historico)} lances no total")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Meu Saldo",
        emoji="💼",
        style=discord.ButtonStyle.secondary,
        custom_id="leilao_saldo",
        row=1,
    )
    async def btn_saldo(self, interaction: discord.Interaction, button: discord.ui.Button):
        saldo = obter_saldo(interaction.user.id)
        minimo = self.estado.minimo_proximo_lance
        pode = "✅" if saldo >= minimo else "❌"
        await interaction.response.send_message(
            f"💼 **Seu saldo:** {formatar_moedas(saldo)}\n"
            f"🎯 **Próximo mínimo:** {formatar_moedas(minimo)}\n"
            f"{pode} Você {'pode' if saldo >= minimo else 'não pode'} dar o próximo lance.",
            ephemeral=True,
        )


# ──────────────────────────────────────────────
#  PAINEL DO LEILÃO
# ──────────────────────────────────────────────

class PainelLeilaoView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Criar Leilão",
        emoji="🎰",
        style=discord.ButtonStyle.danger,
        custom_id="painel_criar_leilao",
    )
    async def btn_criar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not pode_criar_leilao(interaction.user):
            return await interaction.response.send_message(
                "❌ Apenas administradores ou cargos autorizados podem iniciar leilões.",
                ephemeral=True,
            )
        await interaction.response.send_modal(CriarLeilaoModal(self.bot))

    @discord.ui.button(
        label="Como Funciona",
        emoji="📜",
        style=discord.ButtonStyle.secondary,
        custom_id="painel_como_funciona",
    )
    async def btn_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📜 Como funciona o Leilão do Diabo",
            description=(
                "No **Leilão do Diabo**, cada lance usa **🪙 Moedas do Diabo** de verdade.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💰 **Lances cobrados na hora**\n"
                "Ao dar um lance, o valor é removido imediatamente do seu saldo.\n\n"
                "↩️ **Devolução automática**\n"
                "Se alguém superar seu lance, suas moedas são devolvidas na hora.\n\n"
                "⚡ **Anti-Sniper**\n"
                f"Lances nos últimos **{ANTI_SNIPER_SEGUNDOS}s** estendem o tempo em "
                f"**{EXTENSAO_ANTI_SNIPER}s** (máx. {MAXIMO_EXTENSOES}×).\n\n"
                "🏆 **Vencedor automático**\n"
                "Quando o tempo acabar, o maior apostador vence e recebe aviso por DM.\n\n"
                "💼 **Verifique seu saldo**\n"
                "Use o botão **Meu Saldo** para ver se você pode dar o próximo lance.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "> *A casa aceita lances, mas nunca perdoa indecisão.*"
            ),
            color=COR_LEILAO,
        )
        embed.set_image(url=BANNER_LEILAO)
        embed.set_footer(text="Família Sant's • Leilão do Diabo")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ──────────────────────────────────────────────
#  COG
# ──────────────────────────────────────────────

class Leilao(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Registra a view persistente para sobreviver a reinicios
        self.bot.add_view(PainelLeilaoView(bot))

    # ── Comandos ─────────────────────────────────

    @commands.command(name="painel_leilao")
    @commands.has_permissions(administrator=True)
    async def cmd_painel_leilao(self, ctx: commands.Context):
        """Envia o painel permanente de leilão no canal atual."""
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        embed = discord.Embed(
            title="🎰 PAINEL DO LEILÃO DO DIABO",
            description=(
                "Bem-vindo ao salão de apostas da **Família Sant's**.\n\n"
                "Administradores e cargos autorizados podem iniciar leilões oficiais "
                "usando **🪙 Moedas do Diabo**.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "📦 **Itens possíveis:**\n"
                "• Cargos Exclusivos • Gamepasses\n"
                "• VIP • Recompensas especiais • Itens secretos\n\n"
                "💰 **Sistema de lances:**\n"
                "• Lance cobrado imediatamente.\n"
                "• Superado? Suas moedas voltam.\n"
                "• O maior apostador vence ao fim do tempo.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "> *Faça sua oferta. A casa está observando.*"
            ),
            color=COR_LEILAO,
        )
        embed.set_image(url=BANNER_LEILAO)
        embed.set_footer(text="Família Sant's • Leilão do Diabo")
        await ctx.send(embed=embed, view=PainelLeilaoView(self.bot))

    @cmd_painel_leilao.error
    async def painel_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply(
                "❌ Apenas administradores podem enviar o painel.",
                delete_after=8,
            )
        else:
            log.exception("Erro no painel_leilao", exc_info=error)
            await ctx.reply("⚠️ Ocorreu um erro inesperado.", delete_after=8)


async def setup(bot: commands.Bot):
    await bot.add_cog(Leilao(bot))