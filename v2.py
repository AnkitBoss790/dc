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
API_KEY = "ptla_XIWptSIam95ls8GSKYkJTNknlimCw6wACioqikejvTQ"
ADMIN_ID = "1159037240622723092"
ADMIN_FILE = "admins.json"
MSG_FILE = "messages.json"

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

def load_admins():
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE) as f:
            return json.load(f)
    else:
        return [str(config["admin_id"])]

def save_admins(admins):
    with open(ADMIN_FILE, "w") as f:
        json.dump(admins, f, indent=4)

admins = load_admins()

# Load/save messages
def load_messages():
    if os.path.exists(MSG_FILE):
        with open(MSG_FILE) as f:
            return json.load(f)
    else:
        return {}

def save_messages(messages):
    with open(MSG_FILE, "w") as f:
        json.dump(messages, f, indent=4)

messages = load_messages()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await tree.sync()

@tree.command(name="addadmin", description="Add a new admin (admin only)")
@app_commands.describe(userid="User ID to add as admin")
@admin_only()
async def addadmin(interaction: discord.Interaction, userid: str):
    global admins
    if userid in admins:
        await interaction.response.send_message(f"User ID `{userid}` is already an admin.", ephemeral=True)
        return
    admins.append(userid)
    save_admins(admins)
    await interaction.response.send_message(f"User ID `{userid}` added as admin.", ephemeral=True)

@tree.command(name="new", description="Send message to a channel (admin only)")
@app_commands.describe(message="Message to send", channel_id="Channel ID to send to")
@admin_only()
async def new(interaction: discord.Interaction, message: str, channel_id: str):
    channel = bot.get_channel(int(channel_id))
    if channel:
        await channel.send(message)
        await interaction.response.send_message(f"Message sent to <#{channel_id}>", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Channel not found.", ephemeral=True)
    
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
