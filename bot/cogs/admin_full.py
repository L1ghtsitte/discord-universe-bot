import discord
from discord.ext import commands
import psutil
import platform
from datetime import datetime, timedelta


class AdminFullCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="bot_status", description="Показать статус бота")
    @commands.has_permissions(administrator=True)
    async def bot_status(self, ctx):
        embed = discord.Embed(title="🤖 Статус бота", color=0x00ff00)

        # Системная информация
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Uptime
        uptime = datetime.utcnow() - self.bot.start_time if hasattr(self.bot, 'start_time') else timedelta(seconds=0)
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        embed.add_field(name="Серверов", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Пользователей", value=len(self.bot.users), inline=True)
        embed.add_field(name="Задержка", value=f"{self.bot.latency * 1000:.0f} мс", inline=True)
        embed.add_field(name="Uptime", value=f"{hours}ч {minutes}м {seconds}с", inline=True)
        embed.add_field(name="CPU", value=f"{cpu_percent}%", inline=True)
        embed.add_field(name="RAM", value=f"{memory.percent}%", inline=True)
        embed.add_field(name="Диск", value=f"{disk.percent}%", inline=True)
        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(name="Discord.py", value=discord.__version__, inline=True)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="reload_cog", description="Перезагрузить ког")
    @commands.is_owner()
    async def reload_cog(self, ctx, cog_name: str):
        try:
            await self.bot.reload_extension(f"cogs.{cog_name}")
            await ctx.send(f"✅ Ког `{cog_name}` перезагружен.")
        except Exception as e:
            await ctx.send(f"❌ Ошибка при перезагрузке кога `{cog_name}`: {e}")

    @commands.hybrid_command(name="load_cog", description="Загрузить ког")
    @commands.is_owner()
    async def load_cog(self, ctx, cog_name: str):
        try:
            await self.bot.load_extension(f"cogs.{cog_name}")
            await ctx.send(f"✅ Ког `{cog_name}` загружен.")
        except Exception as e:
            await ctx.send(f"❌ Ошибка при загрузке кога `{cog_name}`: {e}")

    @commands.hybrid_command(name="unload_cog", description="Выгрузить ког")
    @commands.is_owner()
    async def unload_cog(self, ctx, cog_name: str):
        try:
            await self.bot.unload_extension(f"cogs.{cog_name}")
            await ctx.send(f"✅ Ког `{cog_name}` выгружен.")
        except Exception as e:
            await ctx.send(f"❌ Ошибка при выгрузке кога `{cog_name}`: {e}")

    @commands.hybrid_command(name="server_info", description="Информация о сервере")
    @commands.has_permissions(administrator=True)
    async def server_info(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title=f"ℹ️ Информация о сервере {guild.name}", color=0x00ff00)

        embed.add_field(name="Владелец", value=guild.owner.mention if guild.owner else "Неизвестен", inline=True)
        embed.add_field(name="Участников", value=guild.member_count, inline=True)
        embed.add_field(name="Каналов", value=len(guild.channels), inline=True)
        embed.add_field(name="Ролей", value=len(guild.roles), inline=True)
        embed.add_field(name="Эмодзи", value=len(guild.emojis), inline=True)
        embed.add_field(name="Стикеры", value=len(guild.stickers), inline=True)
        embed.add_field(name="Дата создания", value=guild.created_at.strftime("%d.%m.%Y %H:%M"), inline=True)
        embed.add_field(name="Уровень буста", value=guild.premium_tier, inline=True)
        embed.add_field(name="Бустеров", value=guild.premium_subscription_count, inline=True)

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await ctx.send(embed=embed)


async def setup(bot):
    # Устанавливаем время запуска бота
    if not hasattr(bot, 'start_time'):
        bot.start_time = datetime.utcnow()
    await bot.add_cog(AdminFullCog(bot))