from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
db = SQLAlchemy()

# ==================== USER DATA ====================
class EconomyUser(db.Model):
    __tablename__ = 'economy_users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False)
    guild_id = db.Column(db.BigInteger, nullable=False)
    balance = db.Column(db.BigInteger, default=0)
    bank = db.Column(db.BigInteger, default=0)
    last_daily = db.Column(db.DateTime, nullable=True)
    __table_args__ = (db.UniqueConstraint('user_id', 'guild_id', name='_economy_user_guild_uc'),)

class UserResources(db.Model):
    __tablename__ = 'user_resources'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False)
    guild_id = db.Column(db.BigInteger, nullable=False)
    coins = db.Column(db.BigInteger, default=0)
    crystals = db.Column(db.BigInteger, default=0)
    crypto_bitcrystal = db.Column(db.Float, default=0.0)
    crypto_astrotoken = db.Column(db.Float, default=0.0)
    last_farm_claim = db.Column(db.DateTime, nullable=True)
    last_planet_claim = db.Column(db.DateTime, nullable=True)
    __table_args__ = (db.UniqueConstraint('user_id', 'guild_id', name='_user_guild_res_uc'),)

class UserProfession(db.Model):
    __tablename__ = 'user_professions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False)
    guild_id = db.Column(db.BigInteger, nullable=False)
    profession = db.Column(db.String(50), nullable=False)  # miner, farmer, merchant, mercenary, alchemist
    specialization = db.Column(db.String(50), nullable=True)  # wheat, iron, potions, etc.
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    last_worked = db.Column(db.DateTime, nullable=True)
    __table_args__ = (db.UniqueConstraint('user_id', 'guild_id', name='_user_guild_prof_uc'),)

class UserInventory(db.Model):
    __tablename__ = 'user_inventory'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False)
    guild_id = db.Column(db.BigInteger, nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    equipped = db.Column(db.Boolean, default=False)
    durability = db.Column(db.Integer, nullable=True)
    __table_args__ = (db.UniqueConstraint('user_id', 'guild_id', 'item_id', name='_user_item_uc'),)

# ==================== SHOP & MARKET ====================
class ShopItem(db.Model):
    __tablename__ = 'shop_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    price_coins = db.Column(db.Integer, default=0)
    price_crystals = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50))
    role_id = db.Column(db.BigInteger, nullable=True)
    limited = db.Column(db.Boolean, default=False)
    stock = db.Column(db.Integer, default=-1)
    image_url = db.Column(db.String(500))

class MarketListing(db.Model):
    __tablename__ = 'market_listings'
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.BigInteger, nullable=False)
    guild_id = db.Column(db.BigInteger, nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    price_coins = db.Column(db.Integer, default=0)
    price_crystals = db.Column(db.Integer, default=0)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

# ==================== SERVER ECONOMY ====================
class ServerEconomy(db.Model):
    __tablename__ = 'server_economy'
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.BigInteger, unique=True, nullable=False)
    treasury = db.Column(db.BigInteger, default=0)
    tax_rate = db.Column(db.Float, default=0.05)
    inflation_rate = db.Column(db.Float, default=0.0)
    last_event = db.Column(db.String(100), nullable=True)
    event_ends_at = db.Column(db.DateTime, nullable=True)

# ==================== CLANS WITH ROLES ====================
class Clan(db.Model):
    __tablename__ = 'clans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    guild_id = db.Column(db.BigInteger, nullable=False)
    leader_id = db.Column(db.BigInteger, nullable=False)
    description = db.Column(db.String(1000), nullable=True)
    banner_url = db.Column(db.String(500), nullable=True)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    balance = db.Column(db.BigInteger, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ClanMember(db.Model):
    __tablename__ = 'clan_members'
    id = db.Column(db.Integer, primary_key=True)
    clan_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.BigInteger, nullable=False)
    role = db.Column(db.String(50), default="member")  # leader, officer, elder, warrior, member
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('clan_id', 'user_id', name='_clan_user_uc'),)

# ==================== FARM & PLANETS ====================
class UserFarm(db.Model):
    __tablename__ = 'user_farms'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False)
    guild_id = db.Column(db.BigInteger, nullable=False)
    farm_type = db.Column(db.String(50), nullable=False)  # grain, livestock, magic
    level = db.Column(db.Integer, default=1)
    last_harvest = db.Column(db.DateTime, nullable=True)
    __table_args__ = (db.UniqueConstraint('user_id', 'guild_id', 'farm_type', name='_user_farm_uc'),)

class Planet(db.Model):
    __tablename__ = 'planets'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(500))
    planet_type = db.Column(db.String(50), nullable=False)  # earth, mars, neptune, cyber
    base_crystal_income = db.Column(db.Integer, default=100)
    base_crypto_income = db.Column(db.Float, default=1.0)
    owner_id = db.Column(db.BigInteger, nullable=True)
    guild_id = db.Column(db.BigInteger, nullable=False)
    last_claimed = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== WARN & LOGS ====================
class Warn(db.Model):
    __tablename__ = 'warns'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False)
    guild_id = db.Column(db.BigInteger, nullable=False)
    moderator_id = db.Column(db.BigInteger, nullable=False)
    reason = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ActionLog(db.Model):
    __tablename__ = 'action_logs'
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.BigInteger, nullable=False)
    action = db.Column(db.String(100), nullable=False)
    target_id = db.Column(db.BigInteger, nullable=True)
    reason = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== FAMILY TREE ====================
class FamilyTree(db.Model):
    __tablename__ = 'family_trees'
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.BigInteger, nullable=False)
    parent1_id = db.Column(db.BigInteger, nullable=True)
    parent2_id = db.Column(db.BigInteger, nullable=True)
    spouse_id = db.Column(db.BigInteger, nullable=True)
    married_at = db.Column(db.DateTime, nullable=True)
    divorced_at = db.Column(db.DateTime, nullable=True)

# ==================== CLAN WARS ====================
class ClanWar(db.Model):
    __tablename__ = 'clan_wars'
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.BigInteger, nullable=False)
    attacker_id = db.Column(db.Integer, nullable=False)
    defender_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="preparing")
    started_at = db.Column(db.DateTime, nullable=True)
    ends_at = db.Column(db.DateTime, nullable=True)
    winner_id = db.Column(db.Integer, nullable=True)
    prize_territory = db.Column(db.Integer, nullable=True)
    attacker_score = db.Column(db.Integer, default=0)
    defender_score = db.Column(db.Integer, default=0)

# ==================== GIVEAWAYS ====================
class Giveaway(db.Model):
    __tablename__ = 'giveaways'
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.BigInteger, nullable=False)
    channel_id = db.Column(db.BigInteger, nullable=False)
    message_id = db.Column(db.BigInteger, nullable=False, unique=True)
    prize = db.Column(db.String(500), nullable=False)
    winners = db.Column(db.Integer, default=1)
    ends_at = db.Column(db.DateTime, nullable=False)
    participants = db.Column(db.ARRAY(db.BigInteger), default=[])
    ended = db.Column(db.Boolean, default=False)

# ==================== LEVELS ====================
class UserLevel(db.Model):
    __tablename__ = 'user_levels'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False)
    guild_id = db.Column(db.BigInteger, nullable=False)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    voice_time = db.Column(db.Integer, default=0)
    last_message = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'guild_id', name='_user_guild_uc'),)

class LevelConfig(db.Model):
    __tablename__ = 'level_config'
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.BigInteger, unique=True, nullable=False)
    xp_per_message = db.Column(db.Integer, default=10)
    xp_per_minute = db.Column(db.Integer, default=5)

# ==================== AUTO MOD ====================
class AutoModConfig(db.Model):
    __tablename__ = 'automod_config'
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.BigInteger, unique=True, nullable=False)
    banned_words = db.Column(db.ARRAY(db.String), default=[])
    spam_threshold = db.Column(db.Integer, default=5)
    max_caps_percent = db.Column(db.Integer, default=70)
    enabled = db.Column(db.Boolean, default=True)

# ==================== TICKETS ====================
class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False)
    guild_id = db.Column(db.BigInteger, nullable=False)
    channel_id = db.Column(db.BigInteger, nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed = db.Column(db.Boolean, default=False)

# ==================== MODERATOR ROLES ====================
class ModeratorRole(db.Model):
    __tablename__ = 'moderator_roles'
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.BigInteger, unique=True, nullable=False)
    guild_id = db.Column(db.BigInteger, nullable=False)