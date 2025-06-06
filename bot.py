import discord
from discord.ext import commands
from discord import app_commands
import json
import aiohttp
import asyncio
import os
from datetime import datetime

# Load Admin ID and Token from config
with open("config.json") as f:
    config = json.load(f)

TOKEN = config["token"]
ADMIN_ID = config["admin_id"]
PANEL_URL = "https://dragoncloud.godanime.net"
HEADERS = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

# Util: Load/Save JSON
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot is ready as {bot.user}")

# Check admin
def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID)

# /ping
@tree.command(name="ping", description="Show bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! `{round(bot.latency * 1000)}ms`")

# /createaccount
@tree.command(name="createaccount", description="Create DragonCloud account (admin only)")
@app_commands.describe(userid="User ID", email="User email", password="User password")
async def createaccount(interaction: discord.Interaction, userid: str, email: str, password: str):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ You are not authorized.", ephemeral=True)
        return

    payload = {
        "username": userid,
        "email": email,
        "first_name": "Dragon",
        "last_name": "User",
        "password": password
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{PANEL_URL}/api/application/users", headers=HEADERS, json=payload) as resp:
            data = await resp.json()
            if resp.status == 201:
                user = await bot.fetch_user(int(userid))
                await user.send(f"✅ Your DragonCloud account has been created!\nEmail: `{email}`\nPassword: `{password}`")
                await interaction.response.send_message("✅ Account created and sent via DM.", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Failed to create account: {data}", ephemeral=True)

# /removeaccount
@tree.command(name="removeaccount", description="Remove DragonCloud account (admin only)")
@app_commands.describe(userid="User ID")
async def removeaccount(interaction: discord.Interaction, userid: str):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ You are not authorized.", ephemeral=True)
        return

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{PANEL_URL}/api/application/users", headers=HEADERS) as resp:
            users = await resp.json()
            for user in users.get("data", []):
                if user["attributes"]["username"] == userid:
                    user_id = user["attributes"]["id"]
                    await session.delete(f"{PANEL_URL}/api/application/users/{user_id}", headers=HEADERS)
                    await interaction.response.send_message(f"✅ User `{userid}` deleted.", ephemeral=True)
                    return
            await interaction.response.send_message(f"❌ User `{userid}` not found.", ephemeral=True)

# /update
@tree.command(name="update", description="Send update broadcast (admin only)")
@app_commands.describe(message="Update message")
async def update(interaction: discord.Interaction, message: str):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ You are not authorized.", ephemeral=True)
        return
    for guild in bot.guilds:
        for member in guild.members:
            try:
                await member.send(f"📢 **Update from DragonCloud**:\n{message}")
            except:
                continue
    await interaction.response.send_message("✅ Broadcast sent.", ephemeral=True)

# Add remaining commands: /status, /freeserver, /credits, /dailycredits, /redeemcode, /createredeemcode,
# /uptime, /manage, /createip in next update due to size limit

bot.run(TOKEN)
