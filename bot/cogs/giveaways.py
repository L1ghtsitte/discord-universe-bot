import discord
from discord.ext import commands, tasks
from ..utils.database import db, Giveaway
import random
from datetime import datetime, timedelta
import asyncio


class GiveawaysCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        now = datetime.utcnow()
        giveaways = Giveaway.query.filter(Giveaway.ends_at <= now, Giveaway.ended == False).all()
        for gw in giveaways:
            await self.end_giveaway(gw)

    async def end_giveaway(self, gw):
        guild = self.bot.get_guild(gw.guild_id)
        if not guild:
            gw.ended = True
            db.session.commit()
            return

        channel = guild.get_channel(gw.channel_id)
        if not channel:
            gw.ended = True
            db.session.commit()
            return

        try:
            message = await channel.fetch_message(gw.message_id)
        except:
            gw.ended = True
            db.session.commit()
            return

        # Получаем всех участников, которые поставили реакцию 🎉
        reaction = discord.utils.get(message.reactions, emoji="🎉")
        if not reaction:
            await channel.send("❌ Никто не участвовал в розыгрыше!")
            gw.ended = True
            db.session.commit()
            return

        # Получаем пользователей (без ботов)
        participants = []
        async for user in reaction.users():
            if not user.bot and user.id not in gw.participants:
                participants.append(user)
                gw.participants.append(user.id)

        db.session.commit()

        if len(participants) == 0:
            await channel.send("❌ Нет участников розыгрыша!")
            gw.ended = True
            db.session.commit()
            return

        # Выбираем победителей
        winners_count = min(gw.winners, len(participants))
        winners = random.sample(participants, winners_count)
        winners_mentions = ", ".join([w.mention for w in winners])

        # Отправляем сообщение о победителях
        await channel.send(
            f"🎉 **ПОЗДРАВЛЯЕМ ПОБЕДИТЕЛЕЙ!** 🎉\n**Приз:** {gw.prize}\n**Победители:** {winners_mentions}\nСпасибо всем за участие!")

        # Отмечаем розыгрыш как завершенный
        gw.ended = True
        db.session.commit()

    @commands.hybrid_command(name="giveaway", description="Создать розыгрыш")
    @commands.has_permissions(manage_guild=True)
    async def start_giveaway(self, ctx, duration: str, winners: int, *, prize: str):
        # Парсим длительность
        seconds = 0
        if duration.endswith('s') or duration.endswith('с'):
            seconds = int(duration[:-1])
        elif duration.endswith('m') or duration.endswith('м'):
            seconds = int(duration[:-1]) * 60
        elif duration.endswith('h') or duration.endswith('ч'):
            seconds = int(duration[:-1]) * 3600
        elif duration.endswith('d') or duration.endswith('д'):
            seconds = int(duration[:-1]) * 86400
        else:
            await ctx.send("❌ Укажите длительность: 10m, 1h, 2d (можно использовать русские буквы: 10м, 1ч, 2д)")
            return

        if seconds <= 0:
            await ctx.send("❌ Длительность должна быть положительной!")
            return

        if winners <= 0:
            await ctx.send("❌ Количество победителей должно быть положительным!")
            return

        if len(prize) > 500:
            await ctx.send("❌ Название приза слишком длинное (макс. 500 символов)!")
            return

        # Рассчитываем время окончания
        ends_at = datetime.utcnow() + timedelta(seconds=seconds)

        # Создаем embed для розыгрыша
        embed = discord.Embed(
            title="🎉 РОЗЫГРЫШ! 🎉",
            description=f"**Приз:** {prize}\n**Победителей:** {winners}\n**Заканчивается:** <t:{int(ends_at.timestamp())}:R> (<t:{int(ends_at.timestamp())}:f>)",
            color=0xffd700
        )
        embed.set_footer(text="Нажмите 🎉 чтобы участвовать!")

        # Отправляем сообщение
        message = await ctx.send(embed=embed)

        # Добавляем реакцию
        await message.add_reaction("🎉")

        # Создаем запись в базе данных
        giveaway = Giveaway(
            guild_id=ctx.guild.id,
            channel_id=ctx.channel.id,
            message_id=message.id,
            prize=prize,
            winners=winners,
            ends_at=ends_at,
            participants=[],
            ended=False
        )

        db.session.add(giveaway)
        db.session.commit()

        await ctx.send(f"✅ Розыгрыш создан! ID: `{giveaway.id}`", ephemeral=True)

    @commands.hybrid_command(name="reroll", description="Переопределить победителя розыгрыша")
    @commands.has_permissions(manage_guild=True)
    async def reroll_giveaway(self, ctx, message_id: int):
        gw = Giveaway.query.filter_by(message_id=message_id, guild_id=ctx.guild.id).first()
        if not gw:
            await ctx.send("❌ Розыгрыш не найден!")
            return

        if not gw.ended:
            await ctx.send("❌ Розыгрыш еще не завершен! Сначала дождитесь окончания.")
            return

        if len(gw.participants) == 0:
            await ctx.send("❌ Нет участников для переопределения!")
            return

        # Выбираем нового победителя
        new_winner_id = random.choice(gw.participants)
        new_winner = ctx.guild.get_member(new_winner_id)
        winner_mention = new_winner.mention if new_winner else f"Пользователь ID: {new_winner_id}"

        await ctx.send(f"🎲 **Новый победитель розыгрыша '{gw.prize}':** {winner_mention}!")


async def setup(bot):
    await bot.add_cog(GiveawaysCog(bot))