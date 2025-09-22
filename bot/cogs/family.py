import discord
from discord.ext import commands
from ..utils.database import db, FamilyTree
import asyncio


class FamilyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="marry", description="Пожениться с другим пользователем")
    async def marry(self, ctx, member: discord.Member):
        if member.id == ctx.author.id:
            await ctx.send("❌ Нельзя жениться на самом себе!")
            return

        if member.bot:
            await ctx.send("❌ Нельзя жениться на боте!")
            return

        # Проверяем, не женат ли автор
        author_record = FamilyTree.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
        if author_record and author_record.spouse_id and not author_record.divorced_at:
            await ctx.send("❌ Вы уже женаты!")
            return

        # Проверяем, не женат ли целевой пользователь
        member_record = FamilyTree.query.filter_by(user_id=member.id, guild_id=ctx.guild.id).first()
        if member_record and member_record.spouse_id and not member_record.divorced_at:
            await ctx.send(f"❌ {member.mention} уже женат(а)!")
            return

        # Отправляем предложение
        await ctx.send(
            f"{member.mention}, {ctx.author.mention} делает вам предложение руки и сердца! У вас есть 60 секунд, чтобы ответить ✅.")

        # Ожидаем реакцию
        def check(reaction, user):
            return user == member and str(reaction.emoji) == '✅' and reaction.message.id == ctx.message.id

        try:
            await ctx.message.add_reaction('✅')
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("💔 Предложение истекло. Попробуйте еще раз!")
            return

        # Создаем или обновляем записи в базе данных
        if not author_record:
            author_record = FamilyTree(user_id=ctx.author.id, guild_id=ctx.guild.id)
            db.session.add(author_record)

        if not member_record:
            member_record = FamilyTree(user_id=member.id, guild_id=ctx.guild.id)
            db.session.add(member_record)

        # Обновляем записи
        author_record.spouse_id = member.id
        author_record.married_at = datetime.utcnow()
        author_record.divorced_at = None

        member_record.spouse_id = ctx.author.id
        member_record.married_at = datetime.utcnow()
        member_record.divorced_at = None

        db.session.commit()

        await ctx.send(f"💖 {ctx.author.mention} и {member.mention} теперь официально женаты! Поздравляем!")

    @commands.hybrid_command(name="divorce", description="Развестись с супругом")
    async def divorce(self, ctx):
        record = FamilyTree.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
        if not record or not record.spouse_id:
            await ctx.send("❌ Вы не женаты!")
            return

        if record.divorced_at:
            await ctx.send("❌ Вы уже разведены!")
            return

        # Получаем информацию о супруге
        spouse = ctx.guild.get_member(record.spouse_id)
        spouse_name = spouse.mention if spouse else f"Пользователь ID: {record.spouse_id}"

        # Подтверждение развода
        await ctx.send(
            f"Вы уверены, что хотите развестись с {spouse_name}? Отреагируйте ❌ в течение 30 секунд, чтобы отменить.")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '❌' and reaction.message.id == ctx.message.id

        try:
            await ctx.message.add_reaction('❌')
            await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            await ctx.send("❤️‍🩹 Развод отменен. Продолжайте строить отношения!")
            return
        except asyncio.TimeoutError:
            pass

        # Обновляем запись автора
        record.divorced_at = datetime.utcnow()

        # Обновляем запись супруга
        spouse_record = FamilyTree.query.filter_by(user_id=record.spouse_id, guild_id=ctx.guild.id).first()
        if spouse_record:
            spouse_record.spouse_id = None
            spouse_record.divorced_at = datetime.utcnow()

        db.session.commit()

        await ctx.send(f"💔 {ctx.author.mention} официально развелся(ась) с {spouse_name}.")

    @commands.hybrid_command(name="family", description="Показать семейное древо")
    async def family_tree(self, ctx, member: discord.Member = None):
        target = member or ctx.author

        record = FamilyTree.query.filter_by(user_id=target.id, guild_id=ctx.guild.id).first()
        if not record:
            await ctx.send(f"❌ У {target.mention} нет семейных связей.")
            return

        embed = discord.Embed(title=f"👨‍👩‍👧‍👦 Семейное древо {target.display_name}", color=0xff69b4)

        # Супруг(а)
        if record.spouse_id:
            spouse = ctx.guild.get_member(record.spouse_id)
            status = " (разведен)" if record.divorced_at else ""
            embed.add_field(name="Супруг(а)",
                            value=f"{spouse.mention if spouse else f'ID: {record.spouse_id}'}{status}", inline=False)

        # Родители (если будут реализованы)
        parents = []
        if hasattr(record, 'parent1_id') and record.parent1_id:
            parent1 = ctx.guild.get_member(record.parent1_id)
            parents.append(parent1.mention if parent1 else f"ID: {record.parent1_id}")
        if hasattr(record, 'parent2_id') and record.parent2_id:
            parent2 = ctx.guild.get_member(record.parent2_id)
            parents.append(parent2.mention if parent2 else f"ID: {record.parent2_id}")

        if parents:
            embed.add_field(name="Родители", value=", ".join(parents), inline=False)

        # Дети (если будут реализованы)
        children = []
        if hasattr(record, 'children') and record.children:
            for child_id in record.children:
                child = ctx.guild.get_member(child_id)
                children.append(child.mention if child else f"ID: {child_id}")

        if children:
            embed.add_field(name="Дети", value=", ".join(children), inline=False)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="adopt", description="Усыновить пользователя")
    async def adopt(self, ctx, member: discord.Member):
        """Усыновить пользователя (требует подтверждения)"""
        if member.id == ctx.author.id:
            await ctx.send("❌ Нельзя усыновить самого себя!")
            return

        if member.bot:
            await ctx.send("❌ Нельзя усыновить бота!")
            return

        # Проверяем, есть ли у целевого пользователя родители
        member_record = FamilyTree.query.filter_by(user_id=member.id, guild_id=ctx.guild.id).first()
        if member_record and (member_record.parent1_id or member_record.parent2_id):
            await ctx.send(f"❌ У {member.mention} уже есть родители!")
            return

        await ctx.send(
            f"{member.mention}, {ctx.author.mention} хочет вас усыновить! У вас есть 60 секунд, чтобы ответить ✅.")

        def check(reaction, user):
            return user == member and str(reaction.emoji) == '✅' and reaction.message.id == ctx.message.id

        try:
            await ctx.message.add_reaction('✅')
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("💔 Предложение об усыновлении истекло.")
            return

        # Создаем или обновляем записи
        if not member_record:
            member_record = FamilyTree(user_id=member.id, guild_id=ctx.guild.id)
            db.session.add(member_record)

        # Устанавливаем автора как первого родителя
        member_record.parent1_id = ctx.author.id

        db.session.commit()

        await ctx.send(f"👨‍👧 {ctx.author.mention} теперь родитель {member.mention}!")


async def setup(bot):
    await bot.add_cog(FamilyCog(bot))