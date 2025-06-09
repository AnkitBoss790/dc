import discord
from discord.ext import commands
from discord import app_commands
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = ""
PANEL_URL = "https://dragoncloud.godanime.net"
API_KEY = ""

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

users_data = load_json("users.json")
antinuke_data = load_json("antinuke.json")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await tree.sync()

@tree.command(name="createaccount")
@app_commands.checks.has_permissions(administrator=True)
async def createaccount(interaction: discord.Interaction, email: str, password: str):
    response = requests.post(f"{PANEL_URL}/api/application/users", headers={"Authorization": f"Bearer {API_KEY}"}, json={
        "email": email,
        "username": email.split("@")[0],
        "first_name": "User",
        "last_name": "Bot",
        "password": password
    })
    if response.status_code == 201:
        await interaction.response.send_message("✅ Account created.")
    else:
        await interaction.response.send_message(f"❌ Failed: {response.text}")

@tree.command(name="removeaccount")
@app_commands.checks.has_permissions(administrator=True)
async def removeaccount(interaction: discord.Interaction, userid: int):
    r = requests.delete(f"{PANEL_URL}/api/application/users/{userid}", headers={"Authorization": f"Bearer {API_KEY}"})
    if r.status_code == 204:
        await interaction.response.send_message("✅ Account deleted.")
    else:
        await interaction.response.send_message("❌ Failed to delete.")

@tree.command(name="status")
async def status(interaction: discord.Interaction):
    await interaction.response.send_message("🟢 Panel is live: " + PANEL_URL)

@tree.command(name="freeserver")
async def freeserver(interaction: discord.Interaction):
    await interaction.response.send_message("💡 Use /register then /createserver to get your free Minecraft server!")

@tree.command(name="credits")
async def credits(interaction: discord.Interaction):
    await interaction.response.send_message("You can earn credits daily using /dailycredits or by redeeming codes using /redeemcode")

@tree.command(name="dailycredits")
async def dailycredits(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id not in users_data:
        users_data[user_id] = {"credits": 0}
    users_data[user_id]["credits"] += 20
    save_json("users.json", users_data)
    await interaction.response.send_message("✅ 20 credits added!")

@tree.command(name="redeemcode")
async def redeemcode(interaction: discord.Interaction, code: str):
    codes = load_json("codes.json")
    user_id = str(interaction.user.id)
    if code in codes:
        users_data[user_id]["credits"] += codes[code]
        del codes[code]
        save_json("codes.json", codes)
        save_json("users.json", users_data)
        await interaction.response.send_message("✅ Code redeemed!")
    else:
        await interaction.response.send_message("❌ Invalid or used code.")

@tree.command(name="createredeemcode")
@app_commands.checks.has_permissions(administrator=True)
async def createredeemcode(interaction: discord.Interaction, code: str, amount: int):
    codes = load_json("codes.json")
    codes[code] = amount
    save_json("codes.json", codes)
    await interaction.response.send_message(f"✅ Code {code} worth {amount} credits created.")

@tree.command(name="uptime")
async def uptime(interaction: discord.Interaction):
    await interaction.response.send_message("📊 Uptime is stable. Servers are online.")

@tree.command(name="createip")
async def createip(interaction: discord.Interaction):
    await interaction.response.send_message("🌐 Your Playit.gg IP: play.dragoncloud.gg:25565 (example)", ephemeral=True)

@tree.command(name="serverlist")
async def serverlist(interaction: discord.Interaction):
    response = requests.get(f"{PANEL_URL}/api/application/servers", headers={"Authorization": f"Bearer {API_KEY}"})
    if response.status_code == 200:
        servers = response.json()["data"]
        msg = "📋 **Server List:**\n"
        for s in servers:
            msg += f"- `{s['attributes']['name']}`\n"
        await interaction.response.send_message(msg)
    else:
        await interaction.response.send_message("❌ Failed to fetch servers.")

@tree.command(name="removeserver")
@app_commands.checks.has_permissions(administrator=True)
async def removeserver(interaction: discord.Interaction, server_id: int):
    r = requests.delete(f"{PANEL_URL}/api/application/servers/{server_id}", headers={"Authorization": f"Bearer {API_KEY}"})
    if r.status_code == 204:
        await interaction.response.send_message("✅ Server removed.")
    else:
        await interaction.response.send_message("❌ Failed to remove server.")

@tree.command(name="manage")
@app_commands.checks.has_permissions(administrator=True)
async def manage(interaction: discord.Interaction, userid: int):
    await interaction.response.send_message("🖥️ Manage server here (buttons coming soon!)")

@tree.command(name="antinuke")
async def antinuke(interaction: discord.Interaction, action: str, usertag: str = None):
    guild_id = str(interaction.guild.id)
    if guild_id not in antinuke_data:
        antinuke_data[guild_id] = {"enabled": False, "whitelist": []}

    if action == "enable":
        antinuke_data[guild_id]["enabled"] = True
    elif action == "disable":
        antinuke_data[guild_id]["enabled"] = False
    elif action == "add" and usertag:
        antinuke_data[guild_id]["whitelist"].append(usertag)
    elif action == "remove" and usertag:
        antinuke_data[guild_id]["whitelist"].remove(usertag)
    else:
        await interaction.response.send_message("❌ Invalid usage.")
        return

    save_json("antinuke.json", antinuke_data)
    await interaction.response.send_message(f"✅ Antinuke updated: {action}")

bot.run(TOKEN)
