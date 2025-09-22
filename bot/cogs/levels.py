import discord
from discord.ext import commands
from ..utils.database import db, UserLevel, LevelConfig
from datetime import datetime, timedelta
import asyncio

class LevelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_users = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        config = LevelConfig.query.filter_by(guild_id=message.guild.id).first()
        if not config:
            config = LevelConfig(guild_id=message.guild.id, xp_per_message=10, xp_per_minute=5)
            db.session.add(config)
            db.session.commit()

        user = UserLevel.query.filter_by(user_id=message.author.id, guild_id=message.guild.id).first()
        if not user:
            user = UserLevel(user_id=message.author.id, guild_id=message.guild.id)
            db.session.add(user)

        now = datetime.utcnow()
        if (now - user.last_message).total_seconds() < 60:
            return

        user.xp += config.xp_per_message
        user.last_message = now

        # Формула уровня: L = sqrt(XP / 100)
        new_level = int((user.xp / 100) ** 0.5) + 1
        if new_level > user.level:
            old_level = user.level
            user.level = new_level
            # Награда за уровень
            economy_user = EconomyUser.query.filter_by(user_id=message.author.id, guild_id=message.guild.id).first()
            if economy_user:
                reward_coins = old_level * 100
                economy_user.balance += reward_coins
                await message.channel.send(f"🎉 {message.author.mention} достиг {user.level} уровня и получил {reward_coins} 🪙!")

        db.session.commit()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        if before.channel is None and after.channel is not None:
            self.voice_users[member.id] = datetime.utcnow()
        elif before.channel is not None and after.channel is None:
            if member.id in self.voice_users:
                start_time = self.voice_users.pop(member.id)
                duration = (datetime.utcnow() - start_time).total_seconds()

                user = UserLevel.query.filter_by(user_id=member.id, guild_id=member.guild.id).first()
                if not user:
                    user = UserLevel(user_id=member.id, guild_id=member.guild.id)
                    db.session.add(user)

                config = LevelConfig.query.filter_by(guild_id=member.guild.id).first()
                if config:
                    xp_earned = int(duration // 60) * config.xp_per_minute
                    user.xp += xp_earned

                new_level = int((user.xp / 100) ** 0.5) + 1
                if new_level > user.level:
                    old_level = user.level
                    user.level = new_level
                    economy_user = EconomyUser.query.filter_by(user_id=member.id, guild_id=member.guild.id).first()
                    if economy_user:
                        reward_coins = old_level * 50
                        economy_user.balance += reward_coins
                        channel = member.guild.system_channel or next(iter(member.guild.text_channels), None)
                        if channel:
                            await channel.send(f"🎉 {member.mention} достиг {user.level} уровня за голосовую активность и получил {reward_coins} 🪙!")

                db.session.commit()

    @commands.hybrid_command(name="rank", description="Показать ранг пользователя")
    async def rank(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        user = UserLevel.query.filter_by(user_id=target.id, guild_id=ctx.guild.id).first()
        if not user:
            await ctx.send(f"❌ У {target.mention} ещё нет ранга.")
            return
        economy_user = EconomyUser.query.filter_by(user_id=target.id, guild_id=ctx.guild.id).first()
        balance = economy_user.balance if economy_user else 0
        await ctx.send(f"📊 {target.mention}: Уровень {user.level} | XP: {user.xp} | Баланс: {balance} 🪙")

    @commands.hy