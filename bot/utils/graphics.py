import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
import numpy as np


def generate_activity_graph(guild_id, days=7):
    """Генерация графика активности сервера"""
    fig, ax = plt.subplots(figsize=(12, 6))

    # Генерируем фейковые данные для примера
    dates = [(datetime.utcnow() - timedelta(days=i)).strftime('%d.%m') for i in range(days - 1, -1, -1)]
    messages = [random.randint(500, 2000) for _ in range(days)]
    voice_hours = [random.randint(100, 800) for _ in range(days)]
    new_users = [random.randint(5, 50) for _ in range(days)]

    # Настройка графика
    ax.plot(dates, messages, marker='o', label='Сообщения', linewidth=2, color='#6c5ce7')
    ax.plot(dates, voice_hours, marker='s', label='Голосовые часы', linewidth=2, color='#00b894')
    ax.plot(dates, new_users, marker='^', label='Новые пользователи', linewidth=2, color='#fdcb6e')

    ax.set_title('Активность сервера (последние 7 дней)', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Дата', fontsize=12)
    ax.set_ylabel('Количество', fontsize=12)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('#36393f')
    fig.patch.set_facecolor('#36393f')
    ax.tick_params(colors='white', labelsize=10)
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')

    # Добавляем значение на каждой точке
    for i, v in enumerate(messages):
        ax.annotate(str(v), xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom', fontsize=8,
                    color='white')
    for i, v in enumerate(voice_hours):
        ax.annotate(str(v), xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom', fontsize=8,
                    color='white')
    for i, v in enumerate(new_users):
        ax.annotate(str(v), xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom', fontsize=8,
                    color='white')

    plt.xticks(rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none', dpi=150)
    buf.seek(0)
    plt.close()
    return buf


def generate_economy_graph(guild_id, days=30):
    """Генерация графика экономики сервера"""
    fig, ax = plt.subplots(figsize=(12, 6))

    # Генерируем фейковые данные
    dates = [(datetime.utcnow() - timedelta(days=i)).strftime('%d.%m') for i in range(days - 1, -1, -1)]
    total_coins = [random.randint(1000000, 5000000) for _ in range(days)]
    total_crystals = [random.randint(50000, 200000) for _ in range(days)]
    transactions = [random.randint(1000, 5000) for _ in range(days)]

    ax.plot(dates[::2], total_coins[::2], marker='o', label='Всего монет', linewidth=2, color='#fdcb6e')
    ax.plot(dates[::2], total_crystals[::2], marker='s', label='Всего кристаллов', linewidth=2, color='#00cec9')
    ax.plot(dates[::2], transactions[::2], marker='^', label='Транзакций', linewidth=2, color='#6c5ce7')

    ax.set_title('Экономика сервера (последние 30 дней)', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Дата', fontsize=12)
    ax.set_ylabel('Количество', fontsize=12)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('#36393f')
    fig.patch.set_facecolor('#36393f')
    ax.tick_params(colors='white', labelsize=10)
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')

    plt.xticks(rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none', dpi=150)
    buf.seek(0)
    plt.close()
    return buf


def generate_clan_wars_graph(guild_id, months=6):
    """Генерация графика клановых войн"""
    fig, ax = plt.subplots(figsize=(12, 6))

    # Генерируем фейковые данные
    months_labels = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн']
    wars_count = [random.randint(3, 10) for _ in range(months)]
    participants = [random.randint(50, 200) for _ in range(months)]
    rewards = [random.randint(100000, 500000) for _ in range(months)]

    x = np.arange(len(months_labels))
    width = 0.25

    ax.bar(x - width, wars_count, width, label='Войн', color='#e17055')
    ax.bar(x, participants, width, label='Участников', color='#00b894')
    ax.bar(x + width, rewards, width, label='Наград (тыс. 🪙)', color='#6c5ce7')

    ax.set_title('Статистика клановых войн', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Месяц', fontsize=12)
    ax.set_ylabel('Количество', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(months_labels)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('#36393f')
    fig.patch.set_facecolor('#36393f')
    ax.tick_params(colors='white', labelsize=10)
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none', dpi=150)
    buf.seek(0)
    plt.close()
    return buf


def generate_level_distribution_graph(guild_id):
    """Генерация графика распределения уровней"""
    fig, ax = plt.subplots(figsize=(12, 6))

    # Генерируем фейковые данные
    levels = list(range(1, 51))
    players = [int(1000 * np.exp(-((x - 10) / 15) ** 2)) for x in
               levels]  # Нормальное распределение с пиком на 10 уровне

    ax.bar(levels, players, color='#6c5ce7', alpha=0.7, edgecolor='white', linewidth=0.5)

    ax.set_title('Распределение уровней игроков', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Уровень', fontsize=12)
    ax.set_ylabel('Количество игроков', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('#36393f')
    fig.patch.set_facecolor('#36393f')
    ax.tick_params(colors='white', labelsize=10)
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')

    # Добавляем линию среднего уровня
    mean_level = sum(l * p for l, p in zip(levels, players)) / sum(players)
    ax.axvline(x=mean_level, color='red', linestyle='--', linewidth=2, label=f'Средний уровень: {mean_level:.1f}')
    ax.legend(loc='upper right', fontsize=11)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none', dpi=150)
    buf.seek(0)
    plt.close()
    return buf