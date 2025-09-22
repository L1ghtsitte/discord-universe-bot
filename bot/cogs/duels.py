import discord
from discord.ext import commands
from ..utils.database import db, EconomyUser
import random
import asyncio

class DuelsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_duels = {}  # {user_id: target_id}

    @commands.hybrid_command(name="duel", description="Вызвать на дуэль другого пользователя")
    async def duel(self, ctx, member: discord.Member, bet: int):
        if member.id == ctx.author.id:
            await ctx.send("❌ Нельзя вызвать на дуэль самого себя!")
            return

        if member.bot:
            await ctx.send("❌ Нельзя вызвать на дуэль бота!")
            return

        if bet < 10:
            await ctx.send("❌ Минимальная ставка: 10 🪙")
            return

        if bet > 100000:
            await ctx.send("❌ Максимальная ставка: 100,000 🪙")
            return

        # Проверяем баланс автора
        author_user = EconomyUser.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
        if not author_user or author_user.balance < bet:
            await ctx.send("❌ У вас недостаточно средств для дуэли!")
            return

        # Проверяем баланс цели
        target_user = EconomyUser.query.filter_by(user_id=member.id, guild_id=ctx.guild.id).first()
        if not target_user or target_user.balance < bet:
            await ctx.send(f"❌ У {member.mention} недостаточно средств для дуэли!")
            return

        # Проверяем, не в дуэли ли уже автор
        if ctx.author.id in self.active_duels:
            await ctx.send("❌ Вы уже находитесь в дуэли!")
            return

        # Проверяем, не в дуэли ли уже цель
        if member.id in self.active_duels:
            await ctx.send(f"❌ {member.mention} уже находится в дуэли!")
            return

        # Отправляем вызов на дуэль
        await ctx.send(f"{member.mention}, {ctx.author.mention} вызывает вас на дуэль со ставкой {bet} 🪙! У вас есть 60 секунд, чтобы принять вызов ✅.")

        def check(reaction, user):
            return user == member and str(reaction.emoji) == '✅' and reaction.message.id == ctx.message.id

        try:
            await ctx.message.add_reaction('✅')
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("⏰ Время вышло! Вызов на дуэль отменен.")
            return

        # Добавляем дуэль в активные
        self.active_duels[ctx.author.id] = member.id
        self.active_duels[member.id] = ctx.author.id

        await ctx.send(f"⚔️ {ctx.author.mention} и {member.mention} вступают в дуэль со ставкой {bet} 🪙! Дуэль начнется через 5 секунд...")
        await asyncio.sleep(5)

        # Определяем победителя (50/50)
        winner = random.choice([ctx.author, member])
        loser = ctx.author if winner == member else member

        # Обновляем балансы
        winner_user = EconomyUser.query.filter_by(user_id=winner.id, guild_id=ctx.guild.id).first()
        loser_user = EconomyUser.query.filter_by(user_id=loser.id, guild_id=ctx.guild.id).first()

        winner_user.balance += bet
        loser_user.balance -= bet

        db.session.commit()

        # Удаляем дуэль из активных
        del self.active_duels[ctx.author.id]
        del self.active_duels[member.id]

        await ctx.send(f"🏆 {winner.mention} победил в дуэли и получает {bet} 🪙 от {loser.mention}!")

    @commands.hybrid_command(name="duel_leaderboard", description="Показать лидеров по дуэлям")
    async def duel_leaderboard(self, ctx):
        # В реальной реализации нужно добавить таблицу для статистики дуэлей
        # Здесь показываем топ-10 по балансу как временное решение
        top_users = EconomyUser.query.filter_by(guild_id=ctx.guild.id).order_by(EconomyUser.balance.desc()).limit(10).all()
        if not top_users:
            await ctx.send("❌ Нет данных для топа дуэлянтов.")
            return

        embed = discord.Embed(title="🏆 Топ дуэлянтов", color=0xff4500)
        for i, user in enumerate(top_users, 1):
            member = ctx.guild.get_member(user.user_id)
            name = member.display_name if member else f"ID: {user.user_id}"
            embed.add_field(name=f"{i}. {name}", value=f"Баланс: {user.balance} 🪙", inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DuelsCog(bot))