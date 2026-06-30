import os
import random
import threading
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask

# .envファイルから環境変数を読み込む
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

app = Flask("")


@app.route("/")
def home():
    return "Bot is complementary and running!"  # アクセスがあったら適当な文字を返す


def run_web_server():
    # Renderが指定するポート番号を取得（なければデフォルトで8080番）
    port = int(os.environ.get("PORT", 8080))
    # 0.0.0.0で待ち受けないと外部（UptimeRobot）からアクセスできません
    app.run(host="0.0.0.0", port=port)

# Intentsの設定(メッセージ内容を読み取るために必要)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 挨拶のバリエーション
GREETINGS = ["こんにちは!", "やあ!", "どうも!", "元気?"]

@bot.event
async def on_ready():
    print(f"ログインしました: {bot.user}")

    # ステータス(オンライン表示)とアクティビティ(プロフィールの「〜をプレイ中」等)を設定
    activity = discord.Activity(
        type=discord.ActivityType.watching,  # playing / listening / watching / competing から選択可
        name="!ping や !hello で挨拶"
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)

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

if __name__ == "__main__":
    # Webサーバーを別スレッド（裏側）で起動
    t = threading.Thread(target=run_web_server)
    t.start()

# Botを起動
bot.run(TOKEN)
