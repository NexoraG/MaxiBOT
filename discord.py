import discord
from discord.ext import commands
import random

# Intentsの設定(メッセージ内容を読み取るために必要)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 挨拶のバリエーション
GREETINGS = ["こんにちは!", "やあ!", "どうも!", "元気?"]

@bot.event
async def on_ready():
    print(f"ログインしました: {bot.user}")

# pingコマンド: Botのレイテンシ(応答速度)を表示
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)  # 秒 → ミリ秒
    await ctx.send(f"🏓 Pong! ({latency}ms)")

# 挨拶コマンド
@bot.command()
async def hello(ctx):
    await ctx.send(f"{random.choice(GREETINGS)} {ctx.author.mention}")

# メッセージに"こんにちは"が含まれていたら自動で挨拶を返す
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if "こんにちは" in message.content or "おはよう" in message.content:
        await message.channel.send(f"{message.author.mention} さん、こんにちは!")

    # コマンドも処理できるようにする(これがないと!ping等が反応しなくなる)
    await bot.process_commands(message)

# Botを起動(トークンは環境変数などで管理するのが安全です)
TOKEN = "TOKEN.env"
bot.run(TOKEN)
