from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import requests
import os
from dotenv import load_dotenv
from bot.utils.database import db as bot_db, ServerEconomy, EconomyUser, MarketListing, Clan, ClanMember, LevelConfig, AutoModConfig

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
db.Model = bot_db.Model

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User:
    def __init__(self, id, username):
        self.id = id
        self.username = username
    def is_authenticated(self): return True
    def is_active(self): return True
    def is_anonymous(self): return False
    def get_id(self): return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    return User(user_id, session.get('username', 'Unknown'))

DISCORD_API_URL = "https://discord.com/api"
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/login")
def login():
    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify guilds")

@app.route("/callback")
def callback():
    code = request.args.get("code")
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "identify guilds"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(f"{DISCORD_API_URL}/v10/oauth2/token", data=data, headers=headers)
    r.raise_for_status()
    token = r.json()["access_token"]
    r = requests.get(f"{DISCORD_API_URL}/v10/users/@me", headers={"Authorization": f"Bearer {token}"})
    user_data = r.json()
    session["token"] = token
    login_user(User(user_data["id"], user_data["username"]))
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
@login_required
def dashboard():
    headers = {"Authorization": f"Bearer {session['token']}"}
    r = requests.get(f"{DISCORD_API_URL}/v10/users/@me/guilds", headers=headers)
    guilds = [g for g in r.json() if (g['permissions'] & 0x20) == 0x20]
    return render_template("dashboard.html", guilds=guilds)

@app.route("/guild/<int:guild_id>")
@login_required
def guild_panel(guild_id):
    headers = {"Authorization": f"Bearer {session['token']}"}
    r = requests.get(f"{DISCORD_API_URL}/v10/guilds/{guild_id}", headers=headers)
    guild = r.json()
    return render_template("guild.html", guild=guild, guild_id=guild_id)

@app.route("/admin/server/<int:guild_id>/economy")
@login_required
def economy_dashboard(guild_id):
    economy = ServerEconomy.query.filter_by(guild_id=guild_id).first()
    if not economy:
        economy = ServerEconomy(guild_id=guild_id)
        db.session.add(economy)
        db.session.commit()
    top_earners = EconomyUser.query.filter_by(guild_id=guild_id).order_by(EconomyUser.balance.desc()).limit(10).all()
    listings = MarketListing.query.filter_by(guild_id=guild_id).limit(20).all()
    return render_template("admin/economy_dashboard.html", guild_id=guild_id, economy=economy, top_earners=top_earners, listings=listings)

@app.route("/admin/server/<int:guild_id>/update_tax", methods=["POST"])
@login_required
def update_tax(guild_id):
    tax_rate = float(request.form.get("tax_rate", 0.05))
    economy = ServerEconomy.query.filter_by(guild_id=guild_id).first()
    if not economy:
        economy = ServerEconomy(guild_id=guild_id)
        db.session.add(economy)
    economy.tax_rate = tax_rate
    db.session.commit()
    return redirect(url_for("economy_dashboard", guild_id=guild_id))

@app.route("/admin/server/<int:guild_id>/clans")
@login_required
def clans_manager(guild_id):
    clans = Clan.query.filter_by(guild_id=guild_id).all()
    return render_template("admin/clans_manager.html", guild_id=guild_id, clans=clans)

@app.route("/admin/server/<int:guild_id>/settings")
@login_required
def server_settings(guild_id):
    level_config = LevelConfig.query.filter_by(guild_id=guild_id).first()
    automod_config = AutoModConfig.query.filter_by(guild_id=guild_id).first()
    return render_template("admin/server_settings.html", guild_id=guild_id, settings={
        "xp_per_message": level_config.xp_per_message if level_config else 10,
        "xp_per_minute": level_config.xp_per_minute if level_config else 5,
        "automod_enabled": automod_config.enabled if automod_config else True
    })

@app.route("/admin/server/<int:guild_id>/update_settings", methods=["POST"])
@login_required
def update_settings(guild_id):
    # Обновляем настройки уровней
    level_config = LevelConfig.query.filter_by(guild_id=guild_id).first()
    if not level_config:
        level_config = LevelConfig(guild_id=guild_id)
        db.session.add(level_config)
    level_config.xp_per_message = int(request.form.get("xp_per_message", 10))
    level_config.xp_per_minute = int(request.form.get("xp_per_minute", 5))

    # Обновляем автомодерацию
    automod_config = AutoModConfig.query.filter_by(guild_id=guild_id).first()
    if not automod_config:
        automod_config = AutoModConfig(guild_id=guild_id)
        db.session.add(automod_config)
    automod_config.enabled = request.form.get("automod_enabled") == "1"

    db.session.commit()
    return redirect(url_for("server_settings", guild_id=guild_id))

@app.route("/admin/server/<int:guild_id>/ai_report")
@login_required
def ai_report(guild_id):
    report = "📈 AI Отчёт: Экономика стабильна. Рекомендуется увеличить награды за квесты на 10% для повышения активности."
    return render_template("admin/ai_report.html", guild_id=guild_id, report=report)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)