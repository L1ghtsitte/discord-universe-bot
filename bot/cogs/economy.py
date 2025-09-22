import discord
from discord.ext import commands
from ..utils.database import db, EconomyUser, UserResources, UserProfession, UserInventory, MarketListing, ServerEconomy, ShopItem, UserFarm, Planet
from ..utils.crypto_engine import crypto_engine
import random
from datetime import datetime, timedelta

FARM_TYPES = {
    "grain": {"name": "Зерновая ферма", "base_income": 200, "upgrade_cost": 1000},
    "livestock": {"name": "Скотоводческая ферма", "base_income": 300, "upgrade_cost": 1500},
    "magic": {"name": "Магическая ферма", "base_income": 500, "upgrade_cost": 2500}
}

PROFESSIONS = {
    "miner": {"name": "Шахтёр", "specializations": ["iron", "gold", "diamond"]},
    "farmer": {"name": "Фермер", "specializations": ["wheat", "corn", "magic_herbs"]},
    "merchant": {"name": "Торговец", "specializations": ["goods", "luxury", "smuggling"]},
    "mercenary": {"name": "Наёмник", "specializations": ["sword", "bow", "magic"]},
    "alchemist": {"name": "Алхимик", "specializations": ["potions", "elixirs", "poisons"]}
}

class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_user_resources(self, user_id, guild_id):
        user_res = UserResources.query.filter_by(user_id=user_id, guild_id=guild_id).first()
        if not user_res:
            user_res = UserResources(user_id=user_id, guild_id=guild_id)
            db.session.add(user_res)
            db.session.commit()
        return user_res

    def get_user_profession(self, user_id, guild_id):
        return UserProfession.query.filter_by(user_id=user_id, guild_id=guild_id).first()

    @commands.hybrid_command(name="balance", description="Показать ваш баланс")
    async def balance(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        user = EconomyUser.query.filter_by(user_id=target.id, guild_id=ctx.guild.id).first()
        if not user:
            user = EconomyUser(user_id=target.id, guild_id=ctx.guild.id)
            db.session.add(user)
            db.session.commit()
        res = self.get_user_resources(target.id, ctx.guild.id)
        await ctx.send(
            f"💰 **{target.display_name}**:\n"
            f"🪙 Монеты: {user.balance:,}\n"
            f"💎 Кристаллы: {res.crystals:,}\n"
            f"₿ BitCrystal: {res.crypto_bitcrystal:.2f}\n"
            f"🌌 AstroToken: {res.crypto_astrotoken:.2f}"
        )

    @commands.hybrid_command(name="daily", description="Получить ежедневную награду")
    async def daily(self, ctx):
        user = EconomyUser.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
        if not user:
            user = EconomyUser(user_id=ctx.author.id, guild_id=ctx.guild.id)
            db.session.add(user)

        now = datetime.utcnow()
        if user.last_daily and (now - user.last_daily).total_seconds() < 86400:
            wait = 86400 - (now - user.last_daily).total_seconds()
            hours = int(wait // 3600)
            minutes = int((wait % 3600) // 60)
            await ctx.send(f"⏳ Следующая награда через: {hours}ч {minutes}м")
            return

        amount = random.randint(100, 500)
        user.balance += amount
        user.last_daily = now
        db.session.commit()
        await ctx.send(f"✅ Вы получили {amount} 🪙!")

    @commands.hybrid_command(name="profession", description="Выбрать профессию")
    async def choose_profession(self, ctx, profession: str, specialization: str = None):
        if profession not in PROFESSIONS:
            professions_list = ", ".join(PROFESSIONS.keys())
            await ctx.send(f"❌ Доступные профессии: {professions_list}")
            return

        prof_data = PROFESSIONS[profession]
        if specialization and specialization not in prof_data["specializations"]:
            specs = ", ".join(prof_data["specializations"])
            await ctx.send(f"❌ Доступные специализации для {profession}: {specs}")
            return

        prof = self.get_user_profession(ctx.author.id, ctx.guild.id)
        if prof:
            await ctx.send("❌ Профессию можно выбрать только один раз!")
            return

        new_prof = UserProfession(
            user_id=ctx.author.id,
            guild_id=ctx.guild.id,
            profession=profession,
            specialization=specialization or prof_data["specializations"][0]
        )
        db.session.add(new_prof)
        db.session.commit()
        await ctx.send(f"✅ Вы выбрали профессию: **{prof_data['name']}** ({specialization or prof_data['specializations'][0]})! Используйте `/work` для заработка.")

    @commands.hybrid_command(name="work", description="Работать по профессии")
    async def work(self, ctx):
        prof = self.get_user_profession(ctx.author.id, ctx.guild.id)
        if not prof:
            await ctx.send("❌ Сначала выберите профессию: `/profession`")
            return

        now = datetime.utcnow()
        if prof.last_worked and (now - prof.last_worked).total_seconds() < 10800:
            wait = 10800 - (now - prof.last_worked).total_seconds()
            minutes = int(wait // 60)
            await ctx.send(f"⏳ Следующая работа доступна через {minutes} минут.")
            return

        base_rewards = {
            "miner": {"coins": 300, "resource": "iron_ore"},
            "farmer": {"coins": 250, "resource": "wheat"},
            "merchant": {"coins": 400, "resource": "gold_coin"},
            "mercenary": {"coins": 500, "resource": "battle_honor"},
            "alchemist": {"coins": 350, "resource": "magic_potion"}
        }

        reward = base_rewards.get(prof.profession, base_rewards["farmer"])
        bonus = prof.level * 10
        coins = reward["coins"] + bonus

        user = EconomyUser.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
        if not user:
            user = EconomyUser(user_id=ctx.author.id, guild_id=ctx.guild.id)
            db.session.add(user)

        user.balance += coins
        prof.last_worked = now
        prof.experience += 20
        if prof.experience >= prof.level * 100:
            old_level = prof.level
            prof.level += 1
            await ctx.send(f"🎉 Повышение! Вы достигли {prof.level} уровня в профессии {PROFESSIONS[prof.profession]['name']}!")

        db.session.commit()
        await ctx.send(f"💼 Вы поработали как **{PROFESSIONS[prof.profession]['name']}** и получили: **{coins} 🪙** + **1x {reward['resource']}**!")

    @commands.hybrid_command(name="farm_create", description="Создать ферму")
    async def create_farm(self, ctx, farm_type: str):
        if farm_type not in FARM_TYPES:
            farms_list = ", ".join(FARM_TYPES.keys())
            await ctx.send(f"❌ Доступные фермы: {farms_list}")
            return

        existing = UserFarm.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id, farm_type=farm_type).first()
        if existing:
            await ctx.send(f"❌ У вас уже есть {FARM_TYPES[farm_type]['name']}.")
            return

        cost = FARM_TYPES[farm_type]["upgrade_cost"] // 2  # Стоимость создания
        user = EconomyUser.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
        if not user or user.balance < cost:
            await ctx.send(f"❌ Нужно {cost} 🪙 для создания фермы.")
            return

        user.balance -= cost
        farm = UserFarm(
            user_id=ctx.author.id,
            guild_id=ctx.guild.id,
            farm_type=farm_type,
            level=1
        )
        db.session.add(farm)
        db.session.commit()
        await ctx.send(f"🚜 Вы создали **{FARM_TYPES[farm_type]['name']}** за {cost} 🪙!")

    @commands.hybrid_command(name="farm_harvest", description="Собрать урожай с фермы")
    async def harvest_farm(self, ctx, farm_type: str = None):
        if farm_type:
            farms = [UserFarm.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id, farm_type=farm_type).first()]
        else:
            farms = UserFarm.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).all()

        if not farms or not farms[0]:
            await ctx.send("❌ У вас нет ферм!")
            return

        total_coins = 0
        harvested_farms = []
        for farm in farms:
            if not farm:
                continue
            if farm.last_harvest and (datetime.utcnow() - farm.last_harvest).total_seconds() < 14400:  # 4 часа
                continue

            income = FARM_TYPES[farm.farm_type]["base_income"] * farm.level
            total_coins += income
            farm.last_harvest = datetime.utcnow()
            harvested_farms.append(FARM_TYPES[farm.farm_type]["name"])

        if total_coins == 0:
            await ctx.send("⏳ Урожай ещё не созрел. Подождите 4 часа после последнего сбора.")
            return

        user = EconomyUser.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
        if not user:
            user = EconomyUser(user_id=ctx.author.id, guild_id=ctx.guild.id)
            db.session.add(user)
        user.balance += total_coins
        db.session.commit()

        await ctx.send(f"✅ Собрано с ферм ({', '.join(harvested_farms)}): **{total_coins} 🪙**!")

    @commands.hybrid_command(name="market", description="Показать товары на рынке")
    async def market_view(self, ctx):
        listings = MarketListing.query.filter_by(guild_id=ctx.guild.id).limit(20).all()
        if not listings:
            await ctx.send("🛒 Рынок пуст. Станьте первым продавцом!")
            return

        embed = discord.Embed(title="🛒 Рынок игроков", color=0x00ff00)
        for l in listings:
            seller = ctx.guild.get_member(l.seller_id) or "Неизвестен"
            item = ShopItem.query.get(l.item_id)
            name = item.name if item else "Неизвестный предмет"
            price = f"{l.price_coins} 🪙"
            if l.price_crystals:
                price += f" + {l.price_crystals} 💎"
            embed.add_field(
                name=f"{name} x{l.quantity}",
                value=f"Продавец: {seller}\nЦена: {price}\nID: `{l.id}`",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="sell", description="Выставить предмет на продажу")
    async def sell_item(self, ctx, item_name: str, price: int, quantity: int = 1):
        if price < 1:
            await ctx.send("❌ Цена должна быть положительной.")
            return

        listing = MarketListing(
            seller_id=ctx.author.id,
            guild_id=ctx.guild.id,
            item_id=1,
            price_coins=price,
            quantity=quantity
        )
        db.session.add(listing)
        db.session.commit()
        await ctx.send(f"✅ Предмет '{item_name}' x{quantity} выставлен на продажу за {price} 🪙! ID: `{listing.id}`")

    @commands.hybrid_command(name="buy", description="Купить предмет с рынка")
    async def buy_from_market(self, ctx, listing_id: int):
        listing = MarketListing.query.filter_by(id=listing_id, guild_id=ctx.guild.id).first()
        if not listing:
            await ctx.send("❌ Лот не найден.")
            return

        seller = self.bot.get_user(listing.seller_id)
        if not seller:
            await ctx.send("❌ Продавец не найден.")
            return

        user = EconomyUser.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
        if not user or user.balance < listing.price_coins:
            await ctx.send("❌ Недостаточно средств!")
            return

        user.balance -= listing.price_coins
        seller_user = EconomyUser.query.filter_by(user_id=seller.id, guild_id=ctx.guild.id).first()
        if not seller_user:
            seller_user = EconomyUser(user_id=seller.id, guild_id=ctx.guild.id)
            db.session.add(seller_user)
        seller_user.balance += listing.price_coins

        economy = ServerEconomy.query.filter_by(guild_id=ctx.guild.id).first()
        if not economy:
            economy = ServerEconomy(guild_id=ctx.guild.id)
            db.session.add(economy)
        tax = int(listing.price_coins * economy.tax_rate)
        economy.treasury += tax
        seller_user.balance -= tax

        db.session.delete(listing)
        db.session.commit()

        await ctx.send(f"💰 Вы купили предмет у {seller.mention} за {listing.price_coins} 🪙 (налог: {tax} 🪙)!")

    @commands.hybrid_command(name="crypto", description="Управление криптовалютой")
    async def crypto_menu(self, ctx):
        price_bitcrystal = crypto_engine.get_price()
        price_astrotoken = crypto_engine.get_price() * 1.5

        embed = discord.Embed(title="💱 Криптовалютный обмен", color=0xffd700)
        embed.add_field(name="BitCrystal (₿)", value=f"Цена: {price_bitcrystal:.2f} 🪙 за 1 ₿", inline=False)
        embed.add_field(name="AstroToken (🌌)", value=f"Цена: {price_astrotoken:.2f} 🪙 за 1 🌌", inline=False)
        embed.add_field(name="Команды", value="`/crypto buy <currency> <amount>`\n`/crypto sell <currency> <amount>`", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="crypto_buy", description="Купить криптовалюту")
    async def crypto_buy(self, ctx, currency: str, amount: float):
        res = self.get_user_resources(ctx.author.id, ctx.guild.id)
        user = EconomyUser.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
        if not user:
            await ctx.send("❌ Сначала получите монеты!")
            return

        price = crypto_engine.get_price()
        if currency == "astrotoken":
            price *= 1.5

        cost = int(amount * price)
        if user.balance < cost:
            await ctx.send(f"❌ Недостаточно монет! Нужно {cost} 🪙.")
            return

        user.balance -= cost
        if currency == "bitcrystal":
            res.crypto_bitcrystal += amount
        elif currency == "astrotoken":
            res.crypto_astrotoken += amount
        else:
            await ctx.send("❌ Доступные валюты: bitcrystal, astrotoken")
            return

        db.session.commit()
        await ctx.send(f"✅ Куплено {amount} {currency} за {cost} 🪙!")

    @commands.hybrid_command(name="crypto_sell", description="Продать криптовалюту")
    async def crypto_sell(self, ctx, currency: str, amount: float):
        res = self.get_user_resources(ctx.author.id, ctx.guild.id)
        user = EconomyUser.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
        if not user:
            user = EconomyUser(user_id=ctx.author.id, guild_id=ctx.guild.id)
            db.session.add(user)

        price = crypto_engine.get_price()
        if currency == "astrotoken":
            price *= 1.5

        if currency == "bitcrystal":
            if res.crypto_bitcrystal < amount:
                await ctx.send("❌ Недостаточно BitCrystal!")
                return
            res.crypto_bitcrystal -= amount
        elif currency == "astrotoken":
            if res.crypto_astrotoken < amount:
                await ctx.send("❌ Недостаточно AstroToken!")
                return
            res.crypto_astrotoken -= amount
        else:
            await ctx.send("❌ Доступные валюты: bitcrystal, astrotoken")
            return

        earnings = int(amount * price)
        user.balance += earnings
        db.session.commit()
        await ctx.send(f"✅ Продано {amount} {currency} за {earnings} 🪙!")

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))