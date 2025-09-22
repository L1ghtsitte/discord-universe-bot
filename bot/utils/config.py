# Конфигурационные константы для бота

# Настройки уровней
DEFAULT_XP_PER_MESSAGE = 10
DEFAULT_XP_PER_MINUTE = 5
LEVEL_FORMULA = "sqrt(xp / 100) + 1"

# Настройки экономики
DAILY_REWARD_MIN = 100
DAILY_REWARD_MAX = 500
WORK_COOLDOWN = 10800  # 3 часа в секундах
FARM_HARVEST_COOLDOWN = 14400  # 4 часа в секундах

# Настройки кланов
CLAN_CREATE_COST = 10000
CLAN_WAR_COST = 50000
CLAN_ROLE_PERMISSIONS = {
    "leader": {"invite": True, "kick": True, "edit_desc": True, "declare_war": True, "manage_bank": True},
    "officer": {"invite": True, "kick": True, "edit_desc": True, "declare_war": False, "manage_bank": False},
    "elder": {"invite": True, "kick": False, "edit_desc": False, "declare_war": False, "manage_bank": False},
    "warrior": {"invite": False, "kick": False, "edit_desc": False, "declare_war": False, "manage_bank": False},
    "member": {"invite": False, "kick": False, "edit_desc": False, "declare_war": False, "manage_bank": False}
}

# Настройки профессий
PROFESSIONS = {
    "miner": {
        "name": "Шахтёр",
        "specializations": ["iron", "gold", "diamond"],
        "base_income": 300,
        "resources": ["iron_ore", "gold_ore", "diamond"]
    },
    "farmer": {
        "name": "Фермер",
        "specializations": ["wheat", "corn", "magic_herbs"],
        "base_income": 250,
        "resources": ["wheat", "corn", "magic_herbs"]
    },
    "merchant": {
        "name": "Торговец",
        "specializations": ["goods", "luxury", "smuggling"],
        "base_income": 400,
        "resources": ["goods", "luxury_items", "rare_goods"]
    },
    "mercenary": {
        "name": "Наёмник",
        "specializations": ["sword", "bow", "magic"],
        "base_income": 500,
        "resources": ["battle_honor", "weapon_parts", "magic_scroll"]
    },
    "alchemist": {
        "name": "Алхимик",
        "specializations": ["potions", "elixirs", "poisons"],
        "base_income": 350,
        "resources": ["magic_potion", "health_elixir", "poison_vial"]
    }
}

# Настройки ферм
FARM_TYPES = {
    "grain": {
        "name": "Зерновая ферма",
        "base_income": 200,
        "upgrade_cost": 1000,
        "max_level": 10
    },
    "livestock": {
        "name": "Скотоводческая ферма",
        "base_income": 300,
        "upgrade_cost": 1500,
        "max_level": 10
    },
    "magic": {
        "name": "Магическая ферма",
        "base_income": 500,
        "upgrade_cost": 2500,
        "max_level": 10
    }
}

# Настройки планет
PLANET_TYPES = {
    "earth": {
        "name": "Земля",
        "crystal_mult": 1.0,
        "crypto_mult": 1.0,
        "description": "Плодородная планета с умеренным климатом.",
        "base_crystal_income": 100,
        "base_crypto_income": 1.0
    },
    "mars": {
        "name": "Марс",
        "crystal_mult": 1.5,
        "crypto_mult": 0.8,
        "description": "Красная пустыня с богатыми залежами кристаллов.",
        "base_crystal_income": 150,
        "base_crypto_income": 0.8
    },
    "neptune": {
        "name": "Нептун",
        "crystal_mult": 0.8,
        "crypto_mult": 1.5,
        "description": "Ледяной гигант, генерирующий космическую энергию.",
        "base_crystal_income": 80,
        "base_crypto_income": 1.5
    },
    "cyber": {
        "name": "Кибер-9",
        "crystal_mult": 1.2,
        "crypto_mult": 1.2,
        "description": "Технологичная планета будущего.",
        "base_crystal_income": 120,
        "base_crypto_income": 1.2
    }
}

# Настройки криптовалют
CRYPTO_CURRENCIES = {
    "bitcrystal": {
        "name": "BitCrystal",
        "symbol": "₿",
        "base_price": 100.0,
        "volatility": 0.1
    },
    "astrotoken": {
        "name": "AstroToken",
        "symbol": "🌌",
        "base_price": 150.0,
        "volatility": 0.15
    }
}

# Настройки магазина
SHOP_CATEGORIES = [
    "role",      # Роли
    "pet",       # Питомцы
    "effect",    # Эффекты (бустеры)
    "house",     # Недвижимость
    "land",      # Земля
    "weapon",    # Оружие
    "title",     # Титулы
    "consumable" # Расходники
]

# Настройки автомодерации
AUTOMOD_DEFAULTS = {
    "enabled": True,
    "spam_threshold": 5,
    "max_caps_percent": 70,
    "banned_words": []
}

# Настройки тикетов
TICKET_CATEGORY_NAME = "Тикеты"
TICKET_CHANNEL_PREFIX = "ticket-"
TICKET_CLOSE_REACTION = "🔒"
TICKET_CLOSE_DELAY = 5  # секунд

# Настройки AI
AI_MODEL = "llama3:8b-instruct-q4_K_M"
AI_TEMPERATURE = 0.7
AI_TOP_P = 0.9
AI_REPEAT_PENALTY = 1.1

# Настройки веб-панели
WEB_PORT = 5000
WEB_HOST = "0.0.0.0"
WEB_DEBUG = True