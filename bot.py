import discord
from discord.ext import commands
from discord import app_commands
import requests

TOKEN = 'MTM3NzY4MzU5MTY1OTUyMDAyMQ.GwmnWw.1uFo4qHVxwtR6stVqt4GvUegj8KGdQ7i77WyIA'
PANEL_URL = 'http://panel.dragoncloud.ggff.net'
API_KEY = 'YOUR_PTERODACTYL_API_KEY'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)
tree = bot.tree

user_credits = {}
redeem_codes = {}
admin_ids = set([1159037240622723092])  # Replace with your actual Discord ID

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
        user_credits[str(interaction.user.id)] = 0
        await interaction.response.send_message("✅ Account created. No credits added.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Error: {res.text}", ephemeral=True)

@tree.command(name="credits", description="Check your credits")
async def credits(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    user_credits.setdefault(uid, 0)
    await interaction.response.send_message(f"💰 You have {user_credits[uid]} credits.", ephemeral=True)

@tree.command(name="createredeemcode", description="Create a redeemable code (admin)")
@app_commands.describe(name="Code name", amount="Credit amount")
async def createredeemcode(interaction: discord.Interaction, name: str, amount: int):
    if interaction.user.id not in admin_ids:
        return await interaction.response.send_message("❌ Only admins can use this.", ephemeral=True)
    redeem_codes[name] = amount
    await interaction.response.send_message(f"✅ Created code `{name}` for {amount} credits.", ephemeral=True)

@tree.command(name="addredeemcode", description="Add credits to a user (admin)")
@app_commands.describe(userid="User ID", amount="Amount to add")
async def addredeemcode(interaction: discord.Interaction, userid: int, amount: int):
    if interaction.user.id not in admin_ids:
        return await interaction.response.send_message("❌ Only admins can use this.", ephemeral=True)
    user_credits[str(userid)] = user_credits.get(str(userid), 0) + amount
    await interaction.response.send_message(f"✅ Added {amount} credits to user {userid}.", ephemeral=True)

@tree.command(name="redeem", description="Redeem a credit code")
@app_commands.describe(code="The code to redeem")
async def redeem(interaction: discord.Interaction, code: str):
    uid = str(interaction.user.id)
    if code in redeem_codes:
        amount = redeem_codes.pop(code)
        user_credits[uid] = user_credits.get(uid, 0) + amount + 50
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
    if user_credits[uid] < 250:
        return await interaction.response.send_message("❌ Not enough credits. You need 250.", ephemeral=True)

    nodes_res = requests.get(f"{PANEL_URL}/api/application/nodes", headers=get_headers())
    if nodes_res.status_code != 200:
        return await interaction.response.send_message("❌ Failed to fetch nodes.", ephemeral=True)

    nodes_data = nodes_res.json()["data"]
    available_nodes = [node["attributes"]["id"] for node in nodes_data if node["attributes"]["name"] not in ["in1", "Paris"]]

    if not available_nodes:
        return await interaction.response.send_message("❌ No available nodes.", ephemeral=True)

    selected_node = available_nodes[0]

    users_res = requests.get(f"{PANEL_URL}/api/application/users", headers=get_headers())
    panel_users = users_res.json()["data"]
    panel_user_id = next((u["attributes"]["id"] for u in panel_users if u["attributes"]["email"].startswith(interaction.user.name)), None)

    if not panel_user_id:
        return await interaction.response.send_message("❌ You must register first using /register.", ephemeral=True)

    server_data = {
        "name": name,
        "user": panel_user_id,
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
        await interaction.response.send_message(f"✅ Server created and 250 credits deducted. Remaining: {user_credits[uid]}", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Server creation failed: {server_res.text}", ephemeral=True)

bot.run(TOKEN)
    
