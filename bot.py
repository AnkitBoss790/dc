from pathlib import Path
import json

# Define the contents of the fixed bot.py file
bot_py_code = '''
import discord
from discord.ext import commands
from discord import app_commands
import requests
import json
import os

TOKEN = 'BOT_TOKEN'
PANEL_URL = 'http://panel.dragoncloud.ggff.net'
API_KEY = ''

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)
tree = bot.tree

USERS_FILE = 'users.json'
CREDITS_FILE = 'credits.json'
REDEEM_CODES_FILE = 'redeem_codes.json'
admin_ids = set([1159037240622723092])  # Replace with your Discord ID

def load_json(filename):
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump({}, f)
    with open(filename, 'r') as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

user_credits = load_json(CREDITS_FILE)
redeem_codes = load_json(REDEEM_CODES_FILE)
users_data = load_json(USERS_FILE)

def get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "Application/vnd.pterodactyl.v1+json"
    }

@bot.event
async def on_ready():
    await tree.sync()
    print(f'✅ Bot is ready. Logged in as {bot.user}')

@tree.command(name="register", description="Register on the Pterodactyl panel")
@app_commands.describe(email="Your email", password="Your password")
async def register(interaction: discord.Interaction, email: str, password: str):
    username = email.split('@')[0]
    data = {
        "username": username,
        "email": email,
        "first_name": interaction.user.name,
        "last_name": "PteroDash",
        "password": password
    }
    res = requests.post(f"{PANEL_URL}/api/application/users", json=data, headers=get_headers())
    if res.status_code == 201:
        panel_user = res.json()["attributes"]
        users_data[str(interaction.user.id)] = {
            "panel_id": panel_user["id"],
            "email": email
        }
        save_json(USERS_FILE, users_data)
        user_credits[str(interaction.user.id)] = 0
        save_json(CREDITS_FILE, user_credits)
        await interaction.response.send_message("✅ Account created and registered. You have 0 credits.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Error: {res.text}", ephemeral=True)

@tree.command(name="credits", description="Check your credits")
async def credits(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    user_credits.setdefault(uid, 0)
    save_json(CREDITS_FILE, user_credits)
    await interaction.response.send_message(f"💰 You have {user_credits[uid]} credits.", ephemeral=True)

@tree.command(name="createredeemcode", description="Create a redeemable code (admin only)")
@app_commands.describe(name="Code name", amount="Credit amount")
async def createredeemcode(interaction: discord.Interaction, name: str, amount: int):
    if interaction.user.id not in admin_ids:
        return await interaction.response.send_message("❌ Only admins can use this.", ephemeral=True)
    redeem_codes[name] = amount
    save_json(REDEEM_CODES_FILE, redeem_codes)
    await interaction.response.send_message(f"✅ Created code `{name}` for {amount} credits.", ephemeral=True)

@tree.command(name="addredeemcode", description="Add credits to a user (admin only)")
@app_commands.describe(userid="User ID", amount="Amount to add")
async def addredeemcode(interaction: discord.Interaction, userid: int, amount: int):
    if interaction.user.id not in admin_ids:
        return await interaction.response.send_message("❌ Only admins can use this.", ephemeral=True)
    user_credits[str(userid)] = user_credits.get(str(userid), 0) + amount
    save_json(CREDITS_FILE, user_credits)
    await interaction.response.send_message(f"✅ Added {amount} credits to user {userid}.", ephemeral=True)

@tree.command(name="redeem", description="Redeem a credit code")
@app_commands.describe(code="The code to redeem")
async def redeem(interaction: discord.Interaction, code: str):
    uid = str(interaction.user.id)
    if code in redeem_codes:
        amount = redeem_codes.pop(code)
        user_credits[uid] = user_credits.get(uid, 0) + amount + 50
        save_json(REDEEM_CODES_FILE, redeem_codes)
        save_json(CREDITS_FILE, user_credits)
        await interaction.response.send_message(f"✅ Redeemed {amount}+50 credits! Total: {user_credits[uid]}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Invalid or already used code.", ephemeral=True)

@tree.command(name="add_admin", description="Add admin user ID")
@app_commands.describe(userid="Discord User ID to add")
async def add_admin(interaction: discord.Interaction, userid: int):
    if interaction.user.id not in admin_ids:
        return await interaction.response.send_message("❌ Only admins can use this.", ephemeral=True)
    admin_ids.add(userid)
    await interaction.response.send_message(f"✅ Added user {userid} as admin.", ephemeral=True)

@tree.command(name="createserver", description="Create a server on the Pterodactyl panel")
@app_commands.describe(name="Server name")
async def createserver(interaction: discord.Interaction, name: str):
    uid = str(interaction.user.id)
    user_credits.setdefault(uid, 0)
    save_json(CREDITS_FILE, user_credits)

    if user_credits[uid] < 250:
        return await interaction.response.send_message("❌ Not enough credits. You need 250.", ephemeral=True)

    user_info = users_data.get(uid)
    if not user_info:
        return await interaction.response.send_message("❌ You must register first using /register.", ephemeral=True)

    nodes_res = requests.get(f"{PANEL_URL}/api/application/nodes", headers=get_headers())
    if nodes_res.status_code != 200:
        return await interaction.response.send_message("❌ Failed to fetch nodes.", ephemeral=True)

    nodes_data = nodes_res.json()["data"]
    available_nodes = [node["attributes"]["id"] for node in nodes_data if node["attributes"]["name"] not in ["in1", "Paris"]]

    if not available_nodes:
        return await interaction.response.send_message("❌ No available nodes.", ephemeral=True)

    selected_node = available_nodes[0]

    server_data = {
        "name": name,
        "user": user_info["panel_id"],
        "egg": 1,
        "docker_image": "ghcr.io/parkervcp/yolks:nodejs_18",
        "startup": "npm run start",
        "limits": {
            "memory": 4096,
            "swap": 0,
            "disk": 10240,
            "io": 500,
            "cpu": 150
        },
        "feature_limits": {
            "databases": 1,
            "backups": 1,
            "allocations": 1
        },
        "environment": {
            "USER_UPLOAD": "true"
        },
        "deploy": {
            "locations": [selected_node],
            "dedicated_ip": False,
            "port_range": []
        },
        "start_on_completion": True
    }

    server_res = requests.post(f"{PANEL_URL}/api/application/servers", json=server_data, headers=get_headers())
    if server_res.status_code == 201:
        user_credits[uid] -= 250
        save_json(CREDITS_FILE, user_credits)
        await interaction.response.send_message(f"✅ Server created and 250 credits deducted. Remaining: {user_credits[uid]}", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Server creation failed: {server_res.text}", ephemeral=True)

bot.run(TOKEN)
'''

# Write to file
bot_py_path = Path("/mnt/data/bot.py")
bot_py_path.write_text(bot_py_code)

# Create empty users.json
(Path("/mnt/data/users.json")).write_text('{}')

# Create empty credits.json and redeem_codes.json
(Path("/mnt/data/credits.json")).write_text('{}')
(Path("/mnt/data/redeem_codes.json")).write_text('{}')

bot_py_path
