import discord
from discord.ext import commands
from ..utils.database import db, ShopItem, EconomyUser, UserInventory, UserResources
import random


class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="shop", description="Показать магазин")
    async def shop_view(self, ctx, category: str = None):
        if category:
            items = ShopItem.query.filter_by(category=category, guild_id=ctx.guild.id).all()
            if not items:
                items = ShopItem.query.filter_by(category=category).all()  # Глобальные предметы
        else:
            items = ShopItem.query.filter(ShopItem.guild_id == ctx.guild.id).all()
            if not items:
                items = ShopItem.query.all()  # Все предметы, если нет серверных

        if not items:
            await ctx.send("🛒 Магазин пуст! Обратитесь к администратору для добавления предметов.")
            return

        # Группируем предметы по категориям
        categories = {}
        for item in items:
            cat = item.category or "Без категории"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)

        # Создаем embed для каждой категории
        for category_name, category_items in categories.items():
            embed = discord.Embed(title=f"🏪 Магазин - {category_name}", color=0x00ff00)

            for item in category_items:
                # Форматируем цену
                price_parts = []
                if item.price_coins > 0:
                    price_parts.append(f"{item.price_coins} 🪙")
                if item.price_crystals > 0:
                    price_parts.append(f"{item.price_crystals} 💎")
                if hasattr(item, 'price_crypto') and item.price_crypto > 0:
                    price_parts.append(f"{item.price_crypto} ₿")

                price_str = " + ".join(price_parts) if price_parts else "Бесплатно"

                # Проверяем наличие на складе
                stock_info = ""
                if item.limited:
                    if item.stock > 0:
                        stock_info = f"\n📦 На складе: {item.stock}"
                    else:
                        stock_info = "\n⛔ Нет в наличии"

                embed.add_field(
                    name=f"{item.name} (ID: {item.id})",
                    value=f"{item.description or 'Нет описания'}\nЦена: {price_str}{stock_info}",
                    inline=False
                )

            await ctx.send(embed=embed)

    @commands.hybrid_command(name="buy", description="Купить предмет из магазина")
    async def buy_item(self, ctx, item_id: int, quantity: int = 1):
        if quantity < 1:
            await ctx.send("❌ Количество должно быть положительным!")
            return

        item = ShopItem.query.get(item_id)
        if not item:
            await ctx.send("❌ Предмет не найден в магазине!")
            return

        # Проверяем наличие на складе
        if item.limited and item.stock < quantity:
            await ctx.send(f"❌ Недостаточно товара на складе! Доступно: {item.stock}")
            return

        # Получаем данные пользователя
        user = EconomyUser.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
        if not user:
            user = EconomyUser(user_id=ctx.author.id, guild_id=ctx.guild.id)
            db.session.add(user)

        res = UserResources.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
        if not res:
            res = UserResources(user_id=ctx.author.id, guild_id=ctx.guild.id)
            db.session.add(res)

        # Проверяем баланс
        total_cost_coins = item.price_coins * quantity
        total_cost_crystals = item.price_crystals * quantity

        if user.balance < total_cost_coins:
            await ctx.send(f"❌ Недостаточно монет! Нужно: {total_cost_coins} 🪙")
            return

        if res.crystals < total_cost_crystals:
            await ctx.send(f"❌ Недостаточно кристаллов! Нужно: {total_cost_crystals} 💎")
            return

        # Списываем средства
        user.balance -= total_cost_coins
        res.crystals -= total_cost_crystals

        # Уменьшаем количество на складе
        if item.limited:
            item.stock -= quantity

        # Добавляем предмет в инвентарь
        inventory_item = UserInventory.query.filter_by(
            user_id=ctx.author.id,
            guild_id=ctx.guild.id,
            item_id=item_id
        ).first()

        if inventory_item:
            inventory_item.quantity += quantity
        else:
            inventory_item = UserInventory(
                user_id=ctx.author.id,
                guild_id=ctx.guild.id,
                item_id=item_id,
                quantity=quantity
            )
            db.session.add(inventory_item)

        db.session.commit()

        await ctx.send(f"✅ Вы купили {quantity}x {item.name} за {total_cost_coins} 🪙 и {total_cost_crystals} 💎!")

    @commands.hybrid_command(name="inventory", description="Показать ваш инвентарь")
    async def inventory_view(self, ctx, member: discord.Member = None):
        target = member or ctx.author

        items = UserInventory.query.filter_by(
            user_id=target.id,
            guild_id=ctx.guild.id
        ).all()

        if not items:
            await ctx.send(f"🎒 Инвентарь {target.mention} пуст!")
            return

        embed = discord.Embed(title=f"🎒 Инвентарь {target.display_name}", color=0x8a2be2)

        for item in items:
            shop_item = ShopItem.query.get(item.item_id)
            if not shop_item:
                continue

            status = " (экипировано)" if item.equipped else ""
            embed.add_field(
                name=f"{shop_item.name} x{item.quantity}{status}",
                value=shop_item.description or "Нет описания",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="use", description="Использовать предмет из инвентаря")
    async def use_item(self, ctx, item_id: int):
        inventory_item = UserInventory.query.filter_by(
            user_id=ctx.author.id,
            guild_id=ctx.guild.id,
            item_id=item_id
        ).first()

        if not inventory_item or inventory_item.quantity <= 0:
            await ctx.send("❌ У вас нет этого предмета!")
            return

        shop_item = ShopItem.query.get(item_id)
        if not shop_item:
            await ctx.send("❌ Предмет не найден!")
            return

        # Проверяем, можно ли использовать предмет
        if not shop_item.effect_data:
            await ctx.send(f"❌ Предмет {shop_item.name} нельзя использовать!")
            return

        # Реализация использования предмета (пример для бустеров)
        effect = shop_item.effect_data
        effect_type = effect.get("type")

        if effect_type == "xp_boost":
            # В реальной реализации нужно добавить систему временных бустеров
            multiplier = effect.get("value", 1.0)
            duration = effect.get("duration", 3600)  # в секундах
            await ctx.send(
                f"✨ Вы использовали {shop_item.name}! Получен бустер опыта x{multiplier} на {duration // 60} минут!")

        elif effect_type == "coins_boost":
            multiplier = effect.get("value", 1.0)
            duration = effect.get("duration", 3600)
            await ctx.send(
                f"💰 Вы использовали {shop_item.name}! Получен бустер монет x{multiplier} на {duration // 60} минут!")

        elif effect_type == "instant_reward":
            coins = effect.get("coins", 0)
            crystals = effect.get("crystals", 0)

            user = EconomyUser.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
            if user and coins > 0:
                user.balance += coins

            res = UserResources.query.filter_by(user_id=ctx.author.id, guild_id=ctx.guild.id).first()
            if res and crystals > 0:
                res.crystals += crystals

            await ctx.send(f"🎁 Вы использовали {shop_item.name} и получили {coins} 🪙 и {crystals} 💎!")

        else:
            await ctx.send(f"🔧 Эффект предмета {shop_item.name} еще не реализован!")

        # Уменьшаем количество предметов
        inventory_item.quantity -= 1
        if inventory_item.quantity <= 0:
            db.session.delete(inventory_item)

        db.session.commit()

    @commands.hybrid_command(name="equip", description="Экипировать предмет")
    async def equip_item(self, ctx, item_id: int):
        inventory_item = UserInventory.query.filter_by(
            user_id=ctx.author.id,
            guild_id=ctx.guild.id,
            item_id=item_id
        ).first()

        if not inventory_item or inventory_item.quantity <= 0:
            await ctx.send("❌ У вас нет этого предмета!")
            return

        shop_item = ShopItem.query.get(item_id)
        if not shop_item:
            await ctx.send("❌ Предмет не найден!")
            return

        # Проверяем, можно ли экипировать предмет
        if shop_item.category not in ["role", "pet", "weapon", "armor"]:
            await ctx.send(f"❌ Предмет {shop_item.name} нельзя экипировать!")
            return

        # Снимаем экипировку со всех предметов этой категории
        UserInventory.query.filter(
            UserInventory.user_id == ctx.author.id,
            UserInventory.guild_id == ctx.guild.id,
            UserInventory.equipped == True
        ).update({UserInventory.equipped: False})

        # Экипируем выбранный предмет
        inventory_item.equipped = True
        db.session.commit()

        await ctx.send(f"✅ Вы экипировали {shop_item.name}!")


async def setup(bot):
    await bot.add_cog(ShopCog(bot))