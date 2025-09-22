import discord
from discord.ext import commands
from ..utils.database import db, Clan, ClanMember
import random

ROLE_PERMISSIONS = {
    "leader": {"invite": True, "kick": True, "edit_desc": True, "declare_war": True, "manage_bank": True},
    "officer": {"invite": True, "kick": True, "edit_desc": True, "declare_war": False, "manage_bank": False},
    "elder": {"invite": True, "kick": False, "edit_desc": False, "declare_war": False, "manage_bank": False},
    "warrior": {"invite": False, "kick": False, "edit_desc": False, "declare_war": False, "manage_bank": False},
    "member": {"invite": False, "kick": False, "edit_desc": False, "declare_war": False, "manage_bank": False}
}

class ClansCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_user_clan(self, user_id, guild_id):
        return db.session.query(Clan, ClanMember).join(ClanMember, Clan.id == ClanMember.clan_id).filter(
            ClanMember.user_id == user_id,
            Clan.guild_id == guild_id
        ).first()

    def has_permission(self, member_role, permission):
        return ROLE_PERMISSIONS.get(member_role, {}).get(permission, False)

    @commands.hybrid_group(name="clan", invoke_without_command=True, description="Управление кланами")
    async def clan(self, ctx):
        await ctx.send_help(ctx.command)

    @clan.command(name="create", description="Создать клан")
    async def create_clan(self, ctx, name: str):
        existing = Clan.query.filter_by(name=name, guild_id=ctx.guild.id).first()
        if existing:
            await ctx.send("❌ Клан с таким именем уже существует.")
            return

        clan = Clan(
            name=name,
            guild_id=ctx.guild.id,
            leader_id=ctx.author.id,
            balance=0
        )
        db.session.add(clan)
        db.session.flush()

        member = ClanMember(
            clan_id=clan.id,
            user_id=ctx.author.id,
            role="leader"
        )
        db.session.add(member)
        db.session.commit()

        await ctx.send(f"🏰 Клан **{name}** создан! Лидер: {ctx.author.mention}")

    @clan.command(name="invite", description="Пригласить в клан")
    async def invite_to_clan(self, ctx, member: discord.Member):
        result = self.get_user_clan(ctx.author.id, ctx.guild.id)
        if not result:
            await ctx.send("❌ Вы не состоите в клане.")
            return

        clan, clan_member = result
        if not self.has_permission(clan_member.role, "invite"):
            await ctx.send("❌ У вас нет прав для приглашения.")
            return

        if member.id == ctx.author.id:
            await ctx.send("❌ Нельзя пригласить самого себя.")
            return

        existing = ClanMember.query.filter_by(clan_id=clan.id, user_id=member.id).first()
        if existing:
            await ctx.send("❌ Пользователь уже в клане.")
            return

        new_member = ClanMember(
            clan_id=clan.id,
            user_id=member.id,
            role="member"
        )
        db.session.add(new_member)
        db.session.commit()

        await ctx.send(f"✅ {member.mention} приглашён в клан **{clan.name}**!")

    @clan.command(name="kick", description="Исключить из клана")
    async def kick_from_clan(self, ctx, member: discord.Member):
        result = self.get_user_clan(ctx.author.id, ctx.guild.id)
        if not result:
            await ctx.send("❌ Вы не в клане.")
            return

        clan, clan_member = result
        if not self.has_permission(clan_member.role, "kick"):
            await ctx.send("❌ У вас нет прав для исключения.")
            return

        target_member = ClanMember.query.filter_by(clan_id=clan.id, user_id=member.id).first()
        if not target_member:
            await ctx.send("❌ Пользователь не в вашем клане.")
            return

        if target_member.role == "leader":
            await ctx.send("❌ Нельзя исключить лидера!")
            return

        db.session.delete(target_member)
        db.session.commit()
        await ctx.send(f"✅ {member.mention} исключён из клана **{clan.name}**.")

    @clan.command(name="promote", description="Повысить роль в клане")
    async def promote_member(self, ctx, member: discord.Member, new_role: str):
        if new_role not in ROLE_PERMISSIONS:
            roles = ", ".join(ROLE_PERMISSIONS.keys())
            await ctx.send(f"❌ Доступные роли: {roles}")
            return

        result = self.get_user_clan(ctx.author.id, ctx.guild.id)
        if not result:
            await ctx.send("❌ Вы не в клане.")
            return

        clan, clan_member = result
        if clan_member.role != "leader":
            await ctx.send("❌ Только лидер может менять роли.")
            return

        target_member = ClanMember.query.filter_by(clan_id=clan.id, user_id=member.id).first()
        if not target_member:
            await ctx.send("❌ Пользователь не в клане.")
            return

        target_member.role = new_role
        db.session.commit()
        await ctx.send(f"✅ {member.mention} получил роль **{new_role}** в клане **{clan.name}**.")

    @clan.command(name="info", description="Информация о клане")
    async def clan_info(self, ctx, name: str = None):
        if name:
            clan = Clan.query.filter_by(name=name, guild_id=ctx.guild.id).first()
        else:
            result = self.get_user_clan(ctx.author.id, ctx.guild.id)
            clan = result[0] if result else None

        if not clan:
            await ctx.send("❌ Клан не найден.")
            return

        members = ClanMember.query.filter_by(clan_id=clan.id).all()
        members_by_role = {}
        for m in members:
            role_name = m.role.capitalize()
            if role_name not in members_by_role:
                members_by_role[role_name] = []
            user = ctx.guild.get_member(m.user_id)
            members_by_role[role_name].append(user.mention if user else f"ID: {m.user_id}")

        embed = discord.Embed(title=f"🏰 Клан: {clan.name}", color=0x800080)
        leader = ctx.guild.get_member(clan.leader_id) or "Неизвестен"
        embed.add_field(name="Лидер", value=leader.mention, inline=True)
        embed.add_field(name="Уровень", value=clan.level, inline=True)
        embed.add_field(name="Казна", value=f"{clan.balance:,} 🪙", inline=True)
        if clan.description:
            embed.add_field(name="Описание", value=clan.description, inline=False)

        for role, members_list in members_by_role.items():
            if members_list:
                embed.add_field(name=f"{role} ({len(members_list)})", value=", ".join(members_list[:5]) + (f" и ещё {len(members_list)-5}" if len(members_list) > 5 else ""), inline=False)

        await ctx.send(embed=embed)

    @clan.command(name="description", description="Установить описание клана")
    async def set_description(self, ctx, *, description: str):
        result = self.get_user_clan(ctx.author.id, ctx.guild.id)
        if not result:
            await ctx.send("❌ Вы не в клане.")
            return

        clan, clan_member = result
        if not self.has_permission(clan_member.role, "edit_desc"):
            await ctx.send("❌ У вас нет прав для изменения описания.")
            return

        clan.description = description[:1000]
        db.session.commit()
        await ctx.send(f"✅ Описание клана обновлено!")

async def setup(bot):
    await bot.add_cog(ClansCog(bot))