import discord
from discord.ext import commands
from ..utils.database import db, UserLevel, EconomyUser, UserResources, Clan, ClanMember
from ..utils.card_generator import generate_profile_card
import io

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="profile", description="Показать профиль пользователя")
    async def profile(self, ctx, member: discord.Member = None):
        target = member or ctx.author

        level_data = UserLevel.query.filter_by(user_id=target.id, guild_id=ctx.guild.id).first()
        economy_data = EconomyUser.query.filter_by(user_id=target.id, guild_id=ctx.guild.id).first()
        res_data = UserResources.query.filter_by(user_id=target.id, guild_id=ctx.guild.id).first()

        clan_member = db.session.query(Clan, ClanMember).join(ClanMember, Clan.id == ClanMember.clan_id).filter(
            ClanMember.user_id == target.id,
            Clan.guild_id == ctx.guild.id
        ).first()

        all_users = UserLevel.query.filter_by(guild_id=ctx.guild.id).order_by(UserLevel.xp.desc()).all()
        rank = next((i+1 for i, u in enumerate(all_users) if u.user_id == target.id), 0)

        user_data = {
            "name": target.display_name,
            "level": level_data.level if level_data else 1,
            "xp": level_data.xp if level_data else 0,
            "coins": economy_data.balance if economy_data else 0,
            "crystals": res_data.crystals if res_data else 0,
            "crypto_bitcrystal": res_data.crypto_bitcrystal if res_data else 0.0,
            "crypto_astrotoken": res_data.crypto_astrotoken if res_data else 0.0,
            "badges": ["Новичок"]
        }

        avatar_url = str(target.avatar.url) if target.avatar else "https://i.imgur.com/4M34hi2.png"
        clan_name = clan_member[0].name if clan_member else None
        clan_role = clan_member[1].role if clan_member else None

        card = generate_profile_card(user_data, avatar_url, ctx.guild.name, rank, clan_name, clan_role)

        await ctx.send(file=discord.File(card, "profile.png"))

async def setup(bot):
    await bot.add_cog(ProfileCog(bot))