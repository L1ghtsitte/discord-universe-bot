import discord
from discord.ext import commands
from ..utils.database import db, UserLevel, LevelConfig
from datetime import datetime, timedelta
import asyncio

class LevelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_users = {}  # {user_id: start_time}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # Получаем настройки уровней для сервера
        config = LevelConfig.query.filter_by(guild_id=message.guild.id).first()
        if not config:
            config = LevelConfig(guild_id=message.guild.id)
            db.session.add(config)
            db.session.commit()

        # Получаем или создаем запись пользователя
        user = UserLevel.query.filter_by(user_id=message.author.id, guild_id=message.guild.id).first()
        if not user:
            user = UserLevel(user_id=message.author.id, guild_id=message.guild.id)
            db.session.add(user)

        # Проверяем кулдаун (1 сообщение в минуту)
        now = datetime.utcnow()
        if user.last_message and (now - user.last_message).total_seconds() < 60:
            return

        # Начисляем XP
        user.xp += config.xp_per_message
        user.last_message = now

        # Рассчитываем новый уровень
        old_level = user.level
        # Формула: уровень = sqrt(XP / 100) + 1
        new_level = int((user.xp / 100) ** 0.5) + 1

        if new_level > old_level:
            user.level = new_level
            # Отправляем уведомление о повышении уровня
            try:
                await message.channel.send(f"🎉 {message.author.mention} достиг {new_level} уровня!")
            except:
                pass  # Игнорируем ошибки, если нет прав на отправку

        db.session.commit()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        # Пользователь зашел в голосовой канал
        if before.channel is None and after.channel is not None:
            self.voice_users[member.id] = datetime.utcnow()

        # Пользователь вышел из голосового канала
        elif before.channel is not None and after.channel is None:
            if member.id in self.voice_users:
                start_time = self.voice_users.pop(member.id)
                duration = (datetime.utcnow() - start_time).total_seconds()

                # Получаем или создаем запись пользователя
                user = UserLevel.query.filter_by(user_id=member.id, guild_id=member.guild.id).first()
                if not user:
                    user = UserLevel(user_id=member.id, guild_id=member.guild.id)
                    db.session.add(user)

                # Обновляем время в голосе
                user.voice_time += int(duration)

                # Получаем настройки уровней
                config = LevelConfig.query.filter_by(guild_id=member.guild.id).first()
                if config:
                    # Начисляем XP за время в голосе (за каждую минуту)
                    xp_earned = int(duration // 60) * config.xp_per_minute
                    user.xp += xp_earned

                    # Рассчитываем новый уровень
                    old_level = user.level
                    new_level = int((user.xp / 100) ** 0.5) + 1

                    if new_level > old_level:
                        user.level = new_level
                        # Отправляем уведомление
                        channel = member.guild.system_channel or next((c for c in member.guild.text_channels if c.permissions_for(member.guild.me).send_messages), None)
                        if channel:
                            try:
                                await channel.send(f"🎉 {member.mention} достиг {new_level} уровня за голосовую активность!")
                            except:
                                pass

                db.session.commit()

    @commands.hybrid_command(name="rank", description="Показать ваш ранг или ранг другого пользователя")
    async def rank(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        user = UserLevel.query.filter_by(user_id=target.id, guild_id=ctx.guild.id).first()
        if not user:
            await ctx.send(f"❌ У {target.mention} еще нет ранга.")
            return

        # Рассчитываем позицию в рейтинге
        all_users = UserLevel.query.filter_by(guild_id=ctx.guild.id).order_by(UserLevel.xp.desc()).all()
        rank = next((i + 1 for i, u in enumerate(all_users) if u.user_id == target.id), 0)

        await ctx.send(
            f"📊 **{target.display_name}**\n"
            f"Уровень: {user.level}\n"
            f"XP: {user.xp}\n"
            f"Голосовое время: {user.voice_time // 3600}ч {user.voice_time % 3600 // 60}м\n"
            f"Ранг на сервере: #{rank}"
        )

    @commands.hybrid_command(name="leaderboard", description="Показать топ-10 пользователей по XP")
    async def leaderboard(self, ctx):
        users = UserLevel.query.filter_by(guild_id=ctx.guild.id).order_by(UserLevel.xp.desc()).limit(10).all()
        if not users:
            await ctx.send("❌ Нет данных для топа.")
            return

        embed = discord.Embed(title="🏆 Топ-10 по XP", color=0xffd700)
        for i, u in enumerate(users, 1):
            member = ctx.guild.get_member(u.user_id)
            name = member.display_name if member else f"ID: {u.user_id}"
            embed.add_field(
                name=f"{i}. {name}",
                value=f"Уровень: {u.level} | XP: {u.xp}",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="voice_leaderboard", description="Показать топ-10 пользователей по голосовому времени")
    async def voice_leaderboard(self, ctx):
        users = UserLevel.query.filter_by(guild_id=ctx.guild.id).order_by(UserLevel.voice_time.desc()).limit(10).all()
        if not users:
            await ctx.send("❌ Нет данных для топа.")
            return

        embed = discord.Embed(title="🎙️ Топ-10 по голосовому времени", color=0x00ff00)
        for i, u in enumerate(users, 1):
            member = ctx.guild.get_member(u.user_id)
            name = member.display_name if member else f"ID: {u.user_id}"
            hours = u.voice_time // 3600
            minutes = (u.voice_time % 3600) // 60
            embed.add_field(
                name=f"{i}. {name}",
                value=f"Время: {hours}ч {minutes}м",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="set_xp_rate", description="Установить XP за сообщение и минуту в голосе (только администраторы)")
    @commands.has_permissions(administrator=True)
    async def set_xp_rate(self, ctx, xp_per_message: int = None, xp_per_minute: int = None):
        config = LevelConfig.query.filter_by(guild_id=ctx.guild.id).first()
        if not config:
            config = LevelConfig(guild_id=ctx.guild.id)
            db.session.add(config)

        if xp_per_message is not None:
            config.xp_per_message = xp_per_message
        if xp_per_minute is not None:
            config.xp_per_minute = xp_per_minute

        db.session.commit()

        await ctx.send(
            f"✅ Настройки XP обновлены!\n"
            f"XP за сообщение: {config.xp_per_message}\n"
            f"XP за минуту в голосе: {config.xp_per_minute}"
        )

async def setup(bot):
    await bot.add_cog(LevelCog(bot))