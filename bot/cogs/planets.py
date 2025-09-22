import discord
from discord.ext import commands
from ..utils.database import db, Planet, UserResources
import random
from datetime import datetime, timedelta

PLANET_TYPES = {
    "earth": {"name": "Земля", "crystal_mult": 1.0, "crypto_mult": 1.0, "description": "Плодородная планета с умеренным климатом."},
    "mars": {"name": "Марс", "crystal_mult": 1.5, "crypto_mult": 0.8, "description": "Красная пустыня с богатыми залежами кристаллов."},
    "neptune": {"name": "Нептун", "crystal_mult": 0.8, "crypto_mult": 1.5, "description": "Ледяной гигант, генерирующий космическую энергию."},
    "cyber": {"name": "Кибер-9", "crystal_mult": 1.2, "crypto_mult": 1.2, "description": "Технологичная планета будущего."}
}

class PlanetsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="planet_list", description="Список доступных планет")
    async def planet_list(self, ctx):
        planets = Planet.query.filter_by(guild_id=ctx.guild.id).limit(10).all()
        if not planets:
            # Создаём планеты по умолчанию, если их нет
            for ptype, data in PLANET_TYPES.items():
                existing = Planet.query.filter_by(name=data["name"], guild_id=ctx.guild.id).first()
                if not existing:
                    planet = Planet(
                        name=data["name"],
                        description=data["description"],
                        planet_type=ptype,
                        base_crystal_income=int(100 * data["crystal_mult"]),
                        base_crypto_income=data["crypto_mult"],
                        guild_id=ctx.guild.id
                    )
                    db.session.add(planet)
            db.session.commit()
            planets = Planet.query.filter_by(guild_id=ctx.guild.id).limit(10).all()

        embed = discord.Embed(title="🌍 Планеты", color=0x00ff00)
        for p in planets:
            owner = ctx.guild.get_member(p.owner_id) if p.owner_id else "Свободна"
            ptype_data = PLANET_TYPES.get(p.planet_type, PLANET_TYPES["earth"])
            embed.add_field(
                name=f"{p.name} ({ptype_data['name']})",
                value=f"Владелец: {owner}\nДоход: {p.base_crystal_income} 💎/час + {p.base_crypto_income:.1f} ₿/час\n{p.description}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="planet_claim", description="Захватить планету")
    async def claim_planet(self, ctx, planet_name: str):
        planet = Planet.query.filter_by(name=planet_name, guild_id=ctx.guild.id).first()
        if not planet:
            await ctx.send("❌ Планета не найдена.")
            return
        if planet.owner_id:
            await ctx.send("❌ Планета уже занята!")
            return

        cost = 50000
        user = EconomyUser.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
        if not user or user.balance < cost:
            await ctx.send(f"❌ Нужно {cost} 🪙 для захвата планеты!")
            return

        user.balance -= cost
        planet.owner_id = ctx.author.id
        db.session.commit()

        await ctx.send(f"🚀 {ctx.author.mention} захватил планету **{planet.name}**!")

    @commands.hybrid_command(name="planet_mine", description="Добыть ресурсы с планет")
    async def mine_planet(self, ctx):
        planets = Planet.query.filter_by(owner_id=ctx.author.id, guild_id=ctx.guild.id).all()
        if not planets:
            await ctx.send("❌ У вас нет планет!")
            return

        res = UserResources.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
        if not res:
            res = UserResources(user_id=ctx.author.id, guild_id=ctx.guild.id)
            db.session.add(res)

        total_crystals = 0
        total_crypto = 0.0
        for p in planets:
            hours_passed = (datetime.utcnow() - p.last_claimed).total_seconds() // 3600
            if hours_passed > 0:
                crystals = int(p.base_crystal_income * hours_passed)
                crypto = p.base_crypto_income * hours_passed
                total_crystals += crystals
                total_crypto += crypto
                p.last_claimed = datetime.utcnow()

        res.crystals += total_crystals
        res.crypto_bitcrystal += total_crypto
        db.session.commit()

        await ctx.send(f"💎 Добыто: {total_crystals} кристаллов + {total_crypto:.2f} BitCrystal со всех ваших планет!")

async def setup(bot):
    await bot.add_cog(PlanetsCog(bot))