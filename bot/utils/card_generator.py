from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
from io import BytesIO


def generate_profile_card(user_data, avatar_url, guild_name, rank, clan_name=None, clan_role=None):
    # Создаём фон
    img = Image.new('RGB', (800, 400), color=(30, 30, 30))
    d = ImageDraw.Draw(img)

    # Загружаем аватар
    try:
        response = requests.get(avatar_url)
        avatar = Image.open(BytesIO(response.content)).convert("RGBA")

        # Масштабируем
        avatar = avatar.resize((200, 200))

        # Создаём круглую маску
        mask = Image.new('L', (200, 200), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 200, 200), fill=255)

        # Вставляем аватар
        img.paste(avatar, (50, 80), mask)
    except:
        d.rectangle([50, 80, 250, 280], fill=(100, 100, 100))
        d.text((90, 170), "NO IMG", fill=(255, 255, 255))

    # Шрифты
    try:
        font_big = ImageFont.truetype("arial.ttf", 48)
        font_med = ImageFont.truetype("arial.ttf", 32)
        font_small = ImageFont.truetype("arial.ttf", 24)
        font_tiny = ImageFont.truetype("arial.ttf", 20)
    except:
        font_big = ImageFont.load_default()
        font_med = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()

    # Имя пользователя
    d.text((280, 80), user_data['name'], fill=(255, 255, 255), font=font_big)

    # Уровень и ранг
    d.text((280, 150), f"Уровень: {user_data['level']}", fill=(0, 255, 0), font=font_med)
    d.text((280, 190), f"Ранг: #{rank}", fill=(255, 215, 0), font=font_med)
    d.text((280, 230), f"Сервер: {guild_name}", fill=(100, 100, 255), font=font_small)

    # Клан
    if clan_name:
        color = (255, 105, 180) if clan_role == "leader" else (105, 255, 180) if clan_role in ["officer",
                                                                                               "elder"] else (180, 180,
                                                                                                              255)
        d.text((50, 300), f"Клан: {clan_name}", fill=color, font=font_small)
        if clan_role:
            role_names = {"leader": "Лидер", "officer": "Офицер", "elder": "Старейшина", "warrior": "Воин",
                          "member": "Участник"}
            d.text((50, 330), f"Роль: {role_names.get(clan_role, clan_role)}", fill=color, font=font_tiny)

    # Статистика
    d.text((450, 80), "📊 Статистика:", fill=(255, 255, 255), font=font_med)
    d.text((450, 130), f"🪙 Монеты: {user_data['coins']:,}", fill=(255, 255, 0), font=font_small)
    d.text((450, 165), f"💎 Кристаллы: {user_data['crystals']:,}", fill=(0, 255, 255), font=font_small)
    d.text((450, 200), f"₿ BitCrystal: {user_data['crypto_bitcrystal']:.2f}", fill=(255, 255, 255), font=font_small)
    d.text((450, 235), f"🌌 AstroToken: {user_data['crypto_astrotoken']:.2f}", fill=(200, 200, 255), font=font_small)

    # Бейджи
    if user_data.get('badges'):
        d.text((450, 280), "🎖️ Бейджи:", fill=(255, 255, 255), font=font_small)
        for i, badge in enumerate(user_data['badges'][:3]):
            d.text((450, 310 + i * 25), f"• {badge}", fill=(255, 200, 0), font=font_tiny)

    # Рамка
    d.rectangle([0, 0, 799, 399], outline=(100, 100, 100), width=2)

    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf