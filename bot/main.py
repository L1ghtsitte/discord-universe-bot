import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.database import db

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix=os.getenv("BOT_PREFIX", "!"), intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} запущен!")
    await bot.tree.sync()

async def load_cogs():
    cogs = [
        "cogs.admin", "cogs.levels", "cogs.moderation", "cogs.warns",
        "cogs.tickets", "cogs.automod", "cogs.clans", "cogs.economy",
        "cogs.giveaways", "cogs.family", "cogs.duels", "cogs.planets",
        "cogs.shop", "cogs.wars", "cogs.profile", "cogs.admin_full",
        "cogs.ai_assistant"
    ]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ {cog} загружен")
        except Exception as e:
            print(f"❌ Ошибка загрузки {cog}: {e}")

@bot.tree.command(name="help", description="Показать список команд")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="📚 Список команд", color=0x00ff00)
    for cog in bot.cogs.values():
        commands_list = [f"`/{c.name}` — {c.description or 'Нет описания'}" for c in cog.get_app_commands()]
        if commands_list:
            embed.add_field(name=f"**{cog.qualified_name}**", value="\n".join(commands_list), inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == "__main__":
    db.init_app(bot.loop)
    with bot:
        bot.loop.run_until_complete(load_cogs())
        bot.run(os.getenv("DISCORD_TOKEN"))