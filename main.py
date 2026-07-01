import os
import random
import threading
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.gateway import DiscordWebSocket
from dotenv import load_dotenv
from flask import Flask
import itertools

# MaxiBOTのコード
# Claudeを使って作成、一部コードなどはGeminiの補助で修正をしたりしてます。
# コメントアウトなどはAIが生成したものをそのままコピーしてるか改変して書いてます。
# ※このコードをフォークして自分だけのBOTを作っても問題ありません。

# .envファイルから環境変数を読み込む
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))  # (デバッグ目的です)スラッシュコマンドの即時反映用

app = Flask("")


@app.route("/")
def home():
    return "Bot is complementary and running!"  # アクセスがあったら適当な文字を返す


def run_web_server():
    # Renderが指定するポート番号を取得（なければデフォルトで8080番）
    port = int(os.environ.get("PORT", 8080))
    # 0.0.0.0で待ち受けないと外部（UptimeRobot）からアクセスできません
    app.run(host="0.0.0.0", port=port)

# =============================================
# スマホマーク用モンキーパッチ
# DiscordのGatewayに送るidentifyのbrowser情報を
# "Discord Android"に偽装することで実現する
# =============================================
async def mobile_identify(self):
    payload = {
        "op": self.IDENTIFY,
        "d": {
            "token": self.token,
            "properties": {
                "$os": "android",
                "$browser": "Discord Android",  # ここがスマホマークの肝
                "$device": "Discord Android",
            },
            "compress": True,
            "large_threshold": 250,
        },
    }
    if self.shard_id is not None and self.shard_count is not None:
        payload["d"]["shard"] = [self.shard_id, self.shard_count]

    state = self._connection
    if state._activity is not None or state._status is not None:
        payload["d"]["presence"] = {
            "status": state._status or "online",
            "game": state._activity,
            "since": 0,
            "afk": False,
        }
    if state._intents is not None:
        payload["d"]["intents"] = state._intents.value

    await self.call_identify_throttle()
    await self.send_as_json(payload)

DiscordWebSocket.identify = mobile_identify  # パッチ適用(Botより前に書く)

# =============================================
# Bot設定
# =============================================
# Intentsの設定(メッセージ内容を読み取るために必要)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="mxi!", intents=intents)

# 挨拶のバリエーション
GREETINGS = ["こんにちは!", "やあ!", "どうも!", "元気?"]

@bot.event
async def on_ready():
    print(f"ログインしました: {bot.user}")

    # ステータス(オンライン表示)とアクティビティ(プロフィールの「〜をプレイ中」等)を設定
    activity = discord.Activity(
        type=discord.ActivityType.playing,  # playing / listening / watching / competing から選択可
        name="MaxiBOT | mxi!ping や mxi!hello で挨拶"
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)

    # --- スラッシュコマンドの同期 ---
    # GUILD_IDがある場合 → そのサーバーだけに即時反映(テスト向き)
    # GUILD_IDがない場合 → 全サーバーに反映されるが最大1時間かかる
    try:
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
        else:
            synced = await bot.tree.sync()
        print(f"スラッシュコマンドを {len(synced)} 個同期しました")
    except Exception as e:
        print(f"同期エラー: {e}")

# pingコマンド: Botのレイテンシ(応答速度)を表示
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)  # 秒 → ミリ秒
    await ctx.send(f"🏓 Pong! ({latency}ms)")

# 挨拶コマンド
@bot.command()
async def hello(ctx):
    await ctx.send(f"{random.choice(GREETINGS)} {ctx.author.mention}")

# =============================================
# スラッシュコマンド (/ping, /hello, /info, /echo)
# =============================================

# /ping
@bot.tree.command(name="ping", description="Botの応答速度を確認します")
async def slash_ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! ({latency}ms)")


# /hello
@bot.tree.command(name="hello", description="Botが挨拶を返します")
async def slash_hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"{random.choice(GREETINGS)} {interaction.user.mention}"
    )


# /info : サーバー情報をEmbedで表示
@bot.tree.command(name="info", description="サーバーの基本情報を表示します")
async def slash_info(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(
        title=f"📊 {guild.name} の情報",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="メンバー数", value=str(guild.member_count), inline=True)
    embed.add_field(name="チャンネル数", value=str(len(guild.channels)), inline=True)
    embed.add_field(
        name="作成日",
        value=guild.created_at.strftime("%Y/%m/%d"),
        inline=True,
    )
    await interaction.response.send_message(embed=embed)


# /echo : 引数付きスラッシュコマンドのサンプル
@bot.tree.command(name="echo", description="入力したテキストをそのまま返します")
@app_commands.describe(text="返してほしい文字を入力")
async def slash_echo(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(f"🔁 {text}")

# メッセージに返答するコード
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if "こんにちは" in message.content:
        await message.channel.send(f"{message.author.mention} さん、こんにちは!")

    if "おはよう" in message.content:
        await message.channel.send(f"{message.author.mention} さん、おはようございます")

    # コマンドも処理できるようにする(これがないと!ping等が反応しなくなる)
    await bot.process_commands(message)

if __name__ == "__main__":
    # Webサーバーを別スレッド（裏側）で起動
    t = threading.Thread(target=run_web_server)
    t.start()

# Botを起動
bot.run(TOKEN)
