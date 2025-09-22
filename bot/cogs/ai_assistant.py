import discord
from discord.ext import commands
import aiohttp
import json
import time

class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "llama3:8b-instruct-q4_K_M"

    async def call_ai(self, prompt, system_prompt="", model=None):
        if not model:
            model = self.model

        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt or "You are a helpful, creative, and concise assistant in a Discord RPG universe.",
            "stream": False,
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }

        try:
            start = time.time()
            async with self.session.post(self.ollama_url, json=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"❌ AI Error: {error_text}")
                    return "⚠️ Локальная AI-модель недоступна. Проверь, запущен ли Ollama."

                data = await resp.json()
                gen_time = time.time() - start
                print(f"✅ AI сгенерировал ответ за {gen_time:.1f} сек")

                return data.get('response', '⚠️ Пустой ответ от AI').strip()
        except Exception as e:
            print(f"❌ AI Exception: {e}")
            return "⚠️ Не удалось подключиться к локальной AI. Запущен ли Ollama?"

    @commands.hybrid_command(name="ai", description="Задать вопрос ИИ-ассистенту")
    async def ai_ask(self, ctx, *, question: str):
        await ctx.defer(ephemeral=False)
        response = await self.call_ai(question)
        if len(response) > 1900:
            response = response[:1900] + "\n... (сокращено)"
        await ctx.send(f"🧠 **AI**: {response}")

    @commands.hybrid_command(name="ai_clan_desc", description="Сгенерировать описание клана")
    async def ai_generate_clan_desc(self, ctx, clan_name: str):
        await ctx.defer()
        prompt = f"Напиши эпическое, атмосферное описание для клана '{clan_name}' в фэнтезийно-космическом сеттинге. Максимум 2 предложения. Используй метафоры и мощные образы."
        desc = await self.call_ai(prompt)
        await ctx.send(f"📜 **Описание клана {clan_name}**:\n> {desc}")

    @commands.hybrid_command(name="ai_quest", description="Сгенерировать ежедневный квест")
    async def ai_daily_quest(self, ctx):
        await ctx.defer()
        prompt = """Придумай захватывающий ежедневный квест для игроков Discord-вселенной.
Формат:
🎯 Название: [название]
📖 Описание: [описание сюжета, 1-2 предложения]
💰 Награда: [монеты, кристаллы, предметы]
⏱️ Время: [сколько времени займет]

Сделай квест уникальным и атмосферным."""
        quest = await self.call_ai(prompt)
        await ctx.send(f"🌟 **Ежедневный квест** 🌟\n{quest}")

    @commands.hybrid_command(name="ai_moderate", description="Проверить текст на токсичность")
    async def ai_moderate(self, ctx, *, text: str):
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send("❌ Только модераторы могут использовать эту команду.", ephemeral=True)
            return

        await ctx.defer(ephemeral=True)
        prompt = f"""Проанализируй следующее сообщение на предмет:
- Токсичности (0-10)
- Спама (да/нет)
- Нарушения правил сервера (да/нет)
- Рекомендации по действию (удалить/предупредить/игнорировать)

Сообщение: "{text}"

Ответь строго в формате JSON:
{{
  "toxicity_score": число,
  "is_spam": булево,
  "violates_rules": булево,
  "action": "строка",
  "reason": "строка"
}}"""
        result = await self.call_ai(prompt)
        try:
            data = json.loads(result)
            embed = discord.Embed(title="🛡️ AI Модерация", color=0xff6b6b)
            embed.add_field(name="Токсичность", value=f"{data.get('toxicity_score', '?')}/10", inline=True)
            embed.add_field(name="Спам", value="✅" if data.get('is_spam') else "❌", inline=True)
            embed.add_field(name="Нарушение", value="⚠️" if data.get('violates_rules') else "✅", inline=True)
            embed.add_field(name="Действие", value=data.get('action', 'Неизвестно'), inline=False)
            embed.add_field(name="Причина", value=data.get('reason', '—'), inline=False)
            await ctx.send(embed=embed, ephemeral=True)
        except Exception as e:
            await ctx.send(f"⚠️ Не удалось распарсить ответ AI:\n```\n{result}\n```\nОшибка: {e}", ephemeral=True)

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

async def setup(bot):
    await bot.add_cog(AICog(bot))