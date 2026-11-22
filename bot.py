import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque

# --- НАСТРОЙКИ ---
TOKEN = os.getenv("DISCORD_TOKEN") 
WELCOME_CHANNEL_ID = 1511258415169667103   # ID канала приветствия/прощания
AUTO_ROLE_ID = 995430962785697833          # ID роли

# Настройки анти-спама
SPAM_MESSAGES = 5      # Сколько сообщений подряд
SPAM_SECONDS = 4       # За сколько секунд (теперь 4)
MUTE_MINUTES = 10      # На сколько минут мьютить

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
spam_history = defaultdict(lambda: deque())

@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} онлайн и готов к работе!")

# --- ПРИВЕТСТВИЕ И АВТОРОЛЬ ---
@bot.event
async def on_member_join(member: discord.Member):
    role = member.guild.get_role(AUTO_ROLE_ID)
    if role:
        try:
            await member.add_roles(role, reason="Автороль при входе")
        except Exception as e:
            print(f"Ошибка выдачи роли: {e}")

    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title=f"Добро пожаловать, {member.name}!",
            description=f"Ты попал на сервер **{member.guild.name}**. Приятного общения!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.timestamp = datetime.now(timezone.utc)
        await channel.send(content=member.mention, embed=embed)

# --- ПРОЩАНИЕ (УХОД С СЕРВЕРА) ---
@bot.event
async def on_member_remove(member: discord.Member):
    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title=f"Прощай, {member.name}...",
            description=f"Пользователь покинул наш сервер. Нас стало на одного меньше. 😢",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.timestamp = datetime.now(timezone.utc)
        await channel.send(embed=embed)

# --- АНТИ-СПАМ ---
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    member = message.author
    if member.guild_permissions.administrator:
        return

    # Лимит сообщений
    now = datetime.now(timezone.utc)
    history = spam_history[member.id]
    history.append(now)

    while history and (now - history[0]).total_seconds() > SPAM_SECONDS:
        history.popleft()

    if len(history) >= SPAM_MESSAGES:
        history.clear()
        try:
            await message.channel.purge(limit=SPAM_MESSAGES, check=lambda m: m.author == member)
            until = discord.utils.utcnow() + timedelta(minutes=MUTE_MINUTES)
            await member.timeout(until, reason="Антиспам")
            await message.channel.send(f"🚫 {member.mention} замьючен на {MUTE_MINUTES} мин за флуд.", delete_after=10)
        except Exception as e:
            print(f"Ошибка анти-спама: {e}")

    await bot.process_commands(message)

bot.run(TOKEN)
