import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from utils.db import criar_tabelas
from utils.cassino_db import criar_tabelas_cassino

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

status_list = [
    "🎰 O Cassino do Diabo abriu...",
    "🪙 Moedas do Diabo circulando...",
    "🎲 A roleta está girando...",
    "✍️ Pactos sendo assinados...",
    "👁️ A casa sempre observa.",
]


@tasks.loop(seconds=20)
async def trocar_status():
    status = status_list[trocar_status.current_loop % len(status_list)]
    await bot.change_presence(
        activity=discord.Game(name=status),
        status=discord.Status.online
    )


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)


@bot.event
async def on_ready():
    criar_tabelas()
    criar_tabelas_cassino()

    if not trocar_status.is_running():
        trocar_status.start()

    print(f"✅ RitualBot online como {bot.user}")

    try:
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ {len(synced)} comandos sincronizados no servidor.")
    except Exception as e:
        print(f"❌ Erro ao sincronizar comandos: {e}")


async def carregar_cogs():
    await bot.load_extension("cogs.abate")
    await bot.load_extension("cogs.maldicoes")
    await bot.load_extension("cogs.familias")
    await bot.load_extension("cogs.loja")

    # 🎰 Cassino do Diabo
    await bot.load_extension("cogs.painel_cassino")
    await bot.load_extension("cogs.economia")
    await bot.load_extension("cogs.roleta")


async def main():
    if not TOKEN:
        raise RuntimeError("Token não encontrado. Configure o arquivo .env")

    async with bot:
        await carregar_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())