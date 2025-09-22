import discord
from discord.ext import commands
from ..utils.database import db, Clan, ClanMember, ClanWar
import random
import asyncio
from datetime import datetime, timedelta


class WarsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.war_tasks = {}  # {war_id: task}

    @commands.hybrid_command(name="war_declare", description="Объявить войну другому клану")
    async def declare_war(self, ctx, enemy_clan_name: str):
        # Получаем клан автора
        author_clan_data = db.session.query(Clan, ClanMember).join(ClanMember, Clan.id == ClanMember.clan_id).filter(
            ClanMember.user_id == ctx.author.id,
            Clan.guild_id == ctx.guild.id
        ).first()

        if not author_clan_data:
            await ctx.send("❌ Вы не состоите в клане!")
            return

        author_clan, author_member = author_clan_data

        # Проверяем, является ли автор лидером или офицером
        if author_member.role not in ["leader", "officer"]:
            await ctx.send("❌ Только лидер или офицер может объявить войну!")
            return

        # Получаем вражеский клан
        enemy_clan = Clan.query.filter_by(name=enemy_clan_name, guild_id=ctx.guild.id).first()
        if not enemy_clan:
            await ctx.send(f"❌ Клан '{enemy_clan_name}' не найден!")
            return

        if enemy_clan.id == author_clan.id:
            await ctx.send("❌ Нельзя объявить войну самому себе!")
            return

        # Проверяем, нет ли уже активной войны между этими кланами
        existing_war = ClanWar.query.filter(
            ((ClanWar.attacker_id == author_clan.id) & (ClanWar.defender_id == enemy_clan.id)) |
            ((ClanWar.attacker_id == enemy_clan.id) & (ClanWar.defender_id == author_clan.id)),
            ClanWar.status != "finished",
            ClanWar.guild_id == ctx.guild.id
        ).first()

        if existing_war:
            await ctx.send("❌ Между этими кланами уже идет война!")
            return

        # Проверяем стоимость объявления войны
        war_cost = 50000
        if author_clan.balance < war_cost:
            await ctx.send(f"❌ Недостаточно средств в казне клана! Нужно {war_cost} 🪙.")
            return

        # Списываем стоимость
        author_clan.balance -= war_cost
        db.session.commit()

        # Создаем запись о войне
        war = ClanWar(
            guild_id=ctx.guild.id,
            attacker_id=author_clan.id,
            defender_id=enemy_clan.id,
            status="preparing",
            ends_at=datetime.utcnow() + timedelta(hours=24),
            attacker_score=0,
            defender_score=0
        )
        db.session.add(war)
        db.session.commit()

        # Отправляем сообщение
        await ctx.send(
            f"⚔️ Клан **{author_clan.name}** объявил войну клану **{enemy_clan.name}**! Война начнется через 10 минут.")

        # Запускаем подготовку к войне
        self.bot.loop.create_task(self.prepare_war(war.id))

    async def prepare_war(self, war_id):
        await asyncio.sleep(600)  # 10 минут подготовки

        war = ClanWar.query.get(war_id)
        if not war or war.status != "preparing":
            return

        war.status = "active"
        db.session.commit()

        # Получаем информацию о кланах
        attacker_clan = Clan.query.get(war.attacker_id)
        defender_clan = Clan.query.get(war.defender_id)

        if not attacker_clan or not defender_clan:
            return

        # Отправляем сообщение о начале войны
        guild = self.bot.get_guild(war.guild_id)
        if guild:
            channel = guild.system_channel or next(
                (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
            if channel:
                await channel.send(
                    f"🔥 **ВОЙНА НАЧАЛАСЬ!** 🔥\nКлан **{attacker_clan.name}** против клана **{defender_clan.name}**!\nВойна продлится 24 часа. Используйте команду `/war_task` для выполнения заданий и получения очков!")

        # Запускаем таймер окончания войны
        self.bot.loop.create_task(self.end_war_timer(war_id))

    async def end_war_timer(self, war_id):
        await asyncio.sleep(86400)  # 24 часа

        war = ClanWar.query.get(war_id)
        if not war or war.status != "active":
            return

        await self.end_war(war_id)

    async def end_war(self, war_id):
        war = ClanWar.query.get(war_id)
        if not war:
            return

        attacker_clan = Clan.query.get(war.attacker_id)
        defender_clan = Clan.query.get(war.defender_id)

        if not attacker_clan or not defender_clan:
            war.status = "finished"
            db.session.commit()
            return

        # Определяем победителя
        if war.attacker_score > war.defender_score:
            winner_id = war.attacker_id
            loser_id = war.defender_id
            winner_clan = attacker_clan
            loser_clan = defender_clan
        elif war.defender_score > war.attacker_score:
            winner_id = war.defender_id
            loser_id = war.attacker_id
            winner_clan = defender_clan
            loser_clan = attacker_clan
        else:
            # Ничья
            war.status = "finished"
            war.winner_id = None
            db.session.commit()

            guild = self.bot.get_guild(war.guild_id)
            if guild:
                channel = guild.system_channel or next(
                    (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
                if channel:
                    await channel.send(
                        f"⚖️ **Война завершена ничьей!**\nКлан **{attacker_clan.name}**: {war.attacker_score} очков\nКлан **{defender_clan.name}**: {war.defender_score} очков")
            return

        # Обновляем статус войны
        war.status = "finished"
        war.winner_id = winner_id
        db.session.commit()

        # Награды победителю
        prize = int(loser_clan.balance * 0.3)  # 30% казны проигравшего
        winner_clan.balance += prize
        loser_clan.balance -= prize

        # Опыт кланам
        winner_clan.experience += 1000
        loser_clan.experience += 500

        # Повышение уровня кланов (если набрали достаточно опыта)
        for clan in [winner_clan, loser_clan]:
            required_exp = clan.level * 1000
            if clan.experience >= required_exp:
                old_level = clan.level
                clan.level += 1
                clan.experience -= required_exp

        db.session.commit()

        # Отправляем сообщение о результате
        guild = self.bot.get_guild(war.guild_id)
        if guild:
            channel = guild.system_channel or next(
                (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
            if channel:
                await channel.send(
                    f"🏆 **ВОЙНА ЗАВЕРШЕНА!** 🏆\nПобедитель: клан **{winner_clan.name}**!\nОчки: {war.attacker_score} - {war.defender_score}\nНаграда: {prize} 🪙 из казны проигравшего!")

    @commands.hybrid_command(name="war_status", description="Показать статус текущей войны")
    async def war_status(self, ctx):
        # Получаем клан пользователя
        clan_data = db.session.query(Clan, ClanMember).join(ClanMember, Clan.id == ClanMember.clan_id).filter(
            ClanMember.user_id == ctx.author.id,
            Clan.guild_id == ctx.guild.id
        ).first()

        if not clan_data:
            await ctx.send("❌ Вы не состоите в клане!")
            return

        clan, member = clan_data

        # Получаем активную войну клана
        war = ClanWar.query.filter(
            ((ClanWar.attacker_id == clan.id) | (ClanWar.defender_id == clan.id)),
            ClanWar.status != "finished",
            ClanWar.guild_id == ctx.guild.id
        ).first()

        if not war:
            await ctx.send("❌ Ваш клан не участвует в активных войнах.")
            return

        attacker_clan = Clan.query.get(war.attacker_id)
        defender_clan = Clan.query.get(war.defender_id)

        if not attacker_clan or not defender_clan:
            await ctx.send("❌ Ошибка при получении информации о войне.")
            return

        # Рассчитываем оставшееся время
        remaining_time = war.ends_at - datetime.utcnow()
        remaining_hours = int(remaining_time.total_seconds() // 3600)
        remaining_minutes = int((remaining_time.total_seconds() % 3600) // 60)

        embed = discord.Embed(title="⚔️ Статус войны", color=0xff0000)
        embed.add_field(name="Атакующий", value=f"**{attacker_clan.name}** ({war.attacker_score} очков)", inline=True)
        embed.add_field(name="Защищающийся", value=f"**{defender_clan.name}** ({war.defender_score} очков)",
                        inline=True)
        embed.add_field(name="Статус", value=war.status.capitalize(), inline=True)
        embed.add_field(name="Осталось времени", value=f"{remaining_hours}ч {remaining_minutes}м", inline=True)
        embed.add_field(name="Завершается", value=f"<t:{int(war.ends_at.timestamp())}:R>", inline=True)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="war_task", description="Выполнить задание войны")
    async def war_task(self, ctx, task_type: str = "daily"):
        # Получаем клан пользователя
        clan_data = db.session.query(Clan, ClanMember).join(ClanMember, Clan.id == ClanMember.clan_id).filter(
            ClanMember.user_id == ctx.author.id,
            Clan.guild_id == ctx.guild.id
        ).first()

        if not clan_data:
            await ctx.send("❌ Вы не состоите в клане!")
            return

        clan, member = clan_data

        # Получаем активную войну клана
        war = ClanWar.query.filter(
            ((ClanWar.attacker_id == clan.id) | (ClanWar.defender_id == clan.id)),
            ClanWar.status == "active",
            ClanWar.guild_id == ctx.guild.id
        ).first()

        if not war:
            await ctx.send("❌ Ваш клан не участвует в активной войне!")
            return

        # Проверяем тип задания
        if task_type not in ["daily", "raid", "defend"]:
            await ctx.send("❌ Доступные типы заданий: daily, raid, defend")
            return

        # Генерируем награду за задание
        if task_type == "daily":
            points = random.randint(10, 50)
            description = "Ежедневное задание"
        elif task_type == "raid":
            points = random.randint(50, 200)
            description = "Рейд на вражеский клан"
        else:  # defend
            points = random.randint(50, 200)
            description = "Защита своей территории"

        # Добавляем очки клану
        if war.attacker_id == clan.id:
            war.attacker_score += points
        else:
            war.defender_score += points

        db.session.commit()

        await ctx.send(f"✅ Вы выполнили задание '{description}' и принесли {points} очков клану **{clan.name}**!")

    @commands.hybrid_command(name="war_leaderboard", description="Показать рейтинг кланов по войнам")
    async def war_leaderboard(self, ctx):
        # Получаем топ-10 кланов по количеству побед в войнах
        clans = Clan.query.filter_by(guild_id=ctx.guild.id).order_by(Clan.level.desc(), Clan.experience.desc()).limit(
            10).all()

        if not clans:
            await ctx.send("❌ Нет данных для рейтинга кланов.")
            return

        embed = discord.Embed(title="🏆 Рейтинг кланов", color=0xffd700)

        for i, clan in enumerate(clans, 1):
            # Считаем количество побед
            wins = ClanWar.query.filter(
                ClanWar.winner_id == clan.id,
                ClanWar.guild_id == ctx.guild.id
            ).count()

            embed.add_field(
                name=f"{i}. {clan.name}",
                value=f"Уровень: {clan.level}\nОпыт: {clan.experience}\nПобед: {wins}\nКазна: {clan.balance} 🪙",
                inline=False
            )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(WarsCog(bot))