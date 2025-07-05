# Full DragonCloud bot.py with all commands (excluding AntiNuke)
import discord
from discord.ext import commands
from discord import app_commands
import json
import aiohttp
import asyncio
import os
import subprocess
from datetime import datetime
import random

# Load config
with open("config.json") as f:
    config = json.load(f)

TOKEN = ""
ADMIN_ID = "1159037240622723092"
PANEL_URL = "https://dragoncloud.godanime.net"
API_KEY = "ptla_5gOLERPvZBYvYKZPoMo9XyyYgQdfXbewPxhwWZe5ybP"
ADMIN_IDS = "1159037240622723092"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

# Util functions
def load_json(file):
    return json.load(open(file)) if os.path.exists(file) else {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

users_data = load_json("users.json")
codes_data = load_json("codes.json")
data_file = "ownlist.json"

@bot.event
async def on_ready():
    await tree.sync()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Gamerzhacker"))
    print(f"Bot is ready as {bot.user}")

def is_admin(user):
    return str(user.id) == str(ADMIN_ID)

@tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong: {round(bot.latency * 1000)}ms")

@tree.command(name="botinfo")
async def botinfo(interaction: discord.Interaction):
    await interaction.response.send_message("🤖 Made by Gamerzhacker")

@tree.command(name="addadmin")
@app_commands.describe(userid="User ID")
async def addadmin(interaction: discord.Interaction, userid: str):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    config["admin_id"] = userid
    with open("config.json", "w") as f: json.dump(config, f, indent=4)
    await interaction.response.send_message(f"✅ Admin set to {userid}")

@tree.command(name="createaccount")
@app_commands.describe(email="Email", password="Password")
async def createaccount(interaction: discord.Interaction, email: str, password: str):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    async with aiohttp.ClientSession() as session:
        payload = {"email": email, "username": email.split("@")[0], "first_name": "User", "last_name": "DC", "password": password}
        async with session.post(f"{PANEL_URL}/api/application/users", headers=HEADERS, json=payload) as resp:
            await interaction.response.send_message("✅ Account created." if resp.status == 201 else "❌ Error creating account")

@tree.command(name="removeaccount")
@app_commands.describe(userid="Panel User ID")
async def removeaccount(interaction: discord.Interaction, userid: int):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{PANEL_URL}/api/application/users/{userid}", headers=HEADERS) as resp:
            await interaction.response.send_message("✅ User deleted" if resp.status == 204 else "❌ Failed to delete user")

@tree.command(name="dailycredits")
async def dailycredits(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    users_data.setdefault(uid, {"credits": 0})
    users_data[uid]["credits"] += 20
    save_json("users.json", users_data)
    await interaction.response.send_message("✅ You earned 20 credits!")

@tree.command(name="credits")
async def credits(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    balance = users_data.get(uid, {}).get("credits", 0)
    await interaction.response.send_message(f"💰 You have {balance} credits.")

@tree.command(name="addcredit")
@app_commands.describe(userid="Discord ID", amount="Amount")
async def addcredit(interaction: discord.Interaction, userid: str, amount: int):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    users_data.setdefault(userid, {"credits": 0})
    users_data[userid]["credits"] += amount
    save_json("users.json", users_data)
    await interaction.response.send_message(f"✅ Added {amount} credits to {userid}")

@tree.command(name="renewvps")
async def renewvps(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    if users_data.get(uid, {}).get("credits", 0) >= 500:
        users_data[uid]["credits"] -= 500
        save_json("users.json", users_data)
        await interaction.response.send_message("🔁 VPS renewed for 30 days!")
    else:
        await interaction.response.send_message("❌ Not enough credits (need 500).")

@tree.command(name="createredeemcode")
@app_commands.describe(code="Code", creditamount="Credits", claimlimit="Claim Limit")
async def createredeemcode(interaction: discord.Interaction, code: str, creditamount: int, claimlimit: int):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    codes_data[code] = {"credits": creditamount, "limit": claimlimit, "used": []}
    save_json("codes.json", codes_data)
    await interaction.response.send_message(f"✅ Redeem code `{code}` created")

@tree.command(name="redeemcode")
@app_commands.describe(code="Enter code")
async def redeemcode(interaction: discord.Interaction, code: str):
    uid = str(interaction.user.id)
    code_data = codes_data.get(code)
    if not code_data:
        return await interaction.response.send_message("❌ Invalid code")
    if uid in code_data["used"]:
        return await interaction.response.send_message("❌ Already redeemed")
    if len(code_data["used"]) >= code_data["limit"]:
        return await interaction.response.send_message("❌ Code limit reached")
    users_data.setdefault(uid, {"credits": 0})
    users_data[uid]["credits"] += code_data["credits"]
    code_data["used"].append(uid)
    save_json("codes.json", codes_data)
    save_json("users.json", users_data)
    await interaction.response.send_message(f"✅ Redeemed `{code}` for {code_data['credits']} credits!")

@tree.command(name="status")
async def status(interaction: discord.Interaction):
    await interaction.response.send_message("🌐 Panel Status: Online at https://dragoncloud.godanime.net")

@tree.command(name="uptime")
async def uptime(interaction: discord.Interaction):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await interaction.response.send_message(f"🕒 Panel is reachable. Current Time: {now}")

@tree.command(name="freeserver")
async def freeserver(interaction: discord.Interaction):
    await interaction.response.send_message("🎁 Free Plan: 2GB RAM / 1 CPU\nCreate a ticket in <#ticket-channel>")

@tree.command(name="serverlist")
async def serverlist(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{PANEL_URL}/api/application/servers", headers=HEADERS) as r:
            data = await r.json()
            servers = data.get("data", [])
            if not servers:
                return await interaction.response.send_message("❌ No servers found")
            msg = "\n".join([f"🖥️ {s['attributes']['name']} (ID: {s['attributes']['id']})" for s in servers])
            await interaction.response.send_message(f"📋 Servers:\n{msg}")

@tree.command(name="removeserver")
@app_commands.describe(serverid="Panel Server ID")
async def removeserver(interaction: discord.Interaction, serverid: str):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{PANEL_URL}/api/application/servers/{serverid}", headers=HEADERS) as r:
            await interaction.response.send_message("✅ Server removed" if r.status == 204 else "❌ Failed to remove")

@tree.command(name="createmsg")
@app_commands.describe(name="Message name", message="Message content")
async def createmsg(interaction: discord.Interaction, name: str, message: str):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    save_json(f"msg_{name}.json", {"content": message})
    await interaction.response.send_message(f"✅ Saved message `{name}`")

@tree.command(name="new")
@app_commands.describe(channelid="Channel ID", message="Message to send")
async def new(interaction: discord.Interaction, channelid: str, message: str):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    channel = bot.get_channel(int(channelid))
    if channel:
        await channel.send(message)
        await interaction.response.send_message("✅ Message sent")
    else:
        await interaction.response.send_message("❌ Channel not found")

class VPSMethodSelect(discord.ui.Select):
    def __init__(self, interaction, userid, amount):
        self.interaction = interaction
        self.userid = userid
        self.amount = amount

        options = [
            discord.SelectOption(label="tmate", description="Generate SSH with tmate"),
            discord.SelectOption(label="ipv4", description="Generate public IP & port with Playit")
        ]
        super().__init__(placeholder="Choose VPS Method", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)

        method = self.values[0]

        if method == "tmate":
            proc = await asyncio.create_subprocess_shell(
                "tmate -F",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            ssh_line = None
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode().strip()
                if "ssh" in decoded and "tmate.io" in decoded:
                    ssh_line = decoded
                    break
            if ssh_line:
                await interaction.user.send(f"🔐 SSH: `{ssh_line}`")
                await interaction.response.send_message("✅ tmate SSH sent via DM")
            else:
                await interaction.response.send_message("❌ Could not extract SSH line")

        elif method == "ipv4":
            proc = await asyncio.create_subprocess_shell(
                "./playit",  # Ensure playit is executable in the same folder
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            ip, port = None, None
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode()
                if "IPv4" in decoded:
                    ip = decoded.strip().split(":")[1].strip()
                elif "Port" in decoded:
                    port = decoded.strip().split(":")[1].strip()
                if ip and port:
                    break
            if ip and port:
                ssh_msg = f"🌐 Your public IP: `{ip}`\n🔐 Port: `{port}`\nSSH Example:\n```ssh root@{ip} -p {port}```"
                await interaction.user.send(ssh_msg)
                await interaction.response.send_message("✅ IPv4 + port sent in DM")
            else:
                await interaction.response.send_message("❌ Failed to get IPv4/port from Playit")

class VPSView(discord.ui.View):
    def __init__(self, interaction, userid, amount):
        super().__init__()
        self.add_item(VPSMethodSelect(interaction, userid, amount))

@tree.command(name="create-vps")
@app_commands.describe(userid="User ID", amount="Credits to charge")
async def create_vps(interaction: discord.Interaction, userid: str, amount: int):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    view = VPSView(interaction, userid, amount)
    await interaction.response.send_message("📦 Select VPS connection type:", view=view, ephemeral=True)

# -------------------- HELP --------------------
@bot.tree.command(name="help", description="Show list of available commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="📘 Command List", color=discord.Color.green())
    embed.add_field(name="/ownlist <userid>", value="🔒 Admin only: Generate server list for a user.", inline=False)
    embed.add_field(name="/list <userid>", value="📋 Show servers owned by a user.", inline=False)
    embed.add_field(name="/deleteownlist <userid>", value="🗑️ Admin only: Delete stored server list for a user.", inline=False)
    embed.add_field(name="/upgrademc <serverid> <ram> <cpu> <disk>", value="⚙️ Admin only: Upgrade server specs.", inline=False)
    embed.add_field(name="/manage <token>", value="🎮 View & control Minecraft servers (client token)", inline=False)
    embed.add_field(name="/getip <token> <serverid>", value="🌐 Get server IP address (client token)", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# -------------------- UPGRADEMC --------------------
@bot.tree.command(name="upgrademc", description="Upgrade RAM/CPU/Disk of a Minecraft server (Admin only)")
@app_commands.describe(serverid="Server Identifier", ram="RAM in MB", cpu="CPU %", disk="Disk in MB")
async def upgrademc(interaction: discord.Interaction, serverid: str, ram: int, cpu: int, disk: int):
    if str(interaction.user.id) not in ADMIN_IDS:
        await interaction.response.send_message("❌ You are not authorized.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    server_internal_id = await get_server_internal_id(serverid)
    if not server_internal_id:
        await interaction.followup.send("❌ Server not found or invalid server ID.")
        return

    url = f"https://dragoncloud.godanime.net/api/application/servers/{server_internal_id}/build"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "allocation": None,
        "memory": ram,
        "swap": 0,
        "disk": disk,
        "io": 500,
        "cpu": cpu,
        "threads": None,
        "feature_limits": {
            "databases": 5,
            "allocations": 5,
            "backups": 5
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
       # Full DragonCloud bot.py with all commands (excluding AntiNuke)
import discord
from discord.ext import commands
from discord import app_commands
import json
import aiohttp
import asyncio
import os
import subprocess
from datetime import datetime

# Load config
with open("config.json") as f:
    config = json.load(f)

TOKEN = ""
ADMIN_ID = "1159037240622723092"
PANEL_URL = "https://dragoncloud.godanime.net"
PANEL_API_KEY = ""
API_KEY = ""
ADMIN_IDS = "1159037240622723092"
HEADERS = {"Authorization": f"Bearer {PANEL_API_KEY}", "Content-Type": "application/json"}
EGG_ID = 1  # Replace with your Minecraft (Paper) egg ID
NODE_ID = 1  # Replace with your default node ID
PANEL_APP_ID = "1"  # Replace with Minecraft egg ID
NODE_ID = 1 # Replace with 1 node ID

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

# Util functions
def load_json(file):
    return json.load(open(file)) if os.path.exists(file) else {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

users_data = load_json("users.json")
codes_data = load_json("codes.json")
giveaways_file = "giveaways.json"
accountapi_file = "accountapi.json"
account_data_file = "accounts.json"
status_channel_file = 'status_channel.txt'

@bot.event
async def on_ready():
    await tree.sync()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Gamerzhacker"))
    print(f"Bot is ready as {bot.user}")

def is_admin(user):
    return str(user.id) == str(ADMIN_ID)

@tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong: {round(bot.latency * 1000)}ms")

@tree.command(name="botinfo")
async def botinfo(interaction: discord.Interaction):
    await interaction.response.send_message("🤖 Made by Gamerzhacker")

@tree.command(name="addadmin")
@app_commands.describe(userid="User ID")
async def addadmin(interaction: discord.Interaction, userid: str):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    config["admin_id"] = userid
    with open("config.json", "w") as f: json.dump(config, f, indent=4)
    await interaction.response.send_message(f"✅ Admin set to {userid}")

@tree.command(name="createaccount")
@app_commands.describe(email="Email", password="Password")
async def createaccount(interaction: discord.Interaction, email: str, password: str):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    async with aiohttp.ClientSession() as session:
        payload = {"email": email, "username": email.split("@")[0], "first_name": "User", "last_name": "DC", "password": password}
        async with session.post(f"{PANEL_URL}/api/application/users", headers=HEADERS, json=payload) as resp:
            await interaction.response.send_message("✅ Account created." if resp.status == 201 else "❌ Error creating account")

@tree.command(name="removeaccount")
@app_commands.describe(userid="Panel User ID")
async def removeaccount(interaction: discord.Interaction, userid: int):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{PANEL_URL}/api/application/users/{userid}", headers=HEADERS) as resp:
            await interaction.response.send_message("✅ User deleted" if resp.status == 204 else "❌ Failed to delete user")

@tree.command(name="dailycredits")
async def dailycredits(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    users_data.setdefault(uid, {"credits": 0})
    users_data[uid]["credits"] += 20
    save_json("users.json", users_data)
    await interaction.response.send_message("✅ You earned 20 credits!")

@tree.command(name="credits")
async def credits(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    balance = users_data.get(uid, {}).get("credits", 0)
    await interaction.response.send_message(f"💰 You have {balance} credits.")

@tree.command(name="addcredit")
@app_commands.describe(userid="Discord ID", amount="Amount")
async def addcredit(interaction: discord.Interaction, userid: str, amount: int):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    users_data.setdefault(userid, {"credits": 0})
    users_data[userid]["credits"] += amount
    save_json("users.json", users_data)
    await interaction.response.send_message(f"✅ Added {amount} credits to {userid}")

@tree.command(name="renewvps")
async def renewvps(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    if users_data.get(uid, {}).get("credits", 0) >= 500:
        users_data[uid]["credits"] -= 500
        save_json("users.json", users_data)
        await interaction.response.send_message("🔁 VPS renewed for 30 days!")
    else:
        await interaction.response.send_message("❌ Not enough credits (need 500).")

@tree.command(name="createredeemcode")
@app_commands.describe(code="Code", creditamount="Credits", claimlimit="Claim Limit")
async def createredeemcode(interaction: discord.Interaction, code: str, creditamount: int, claimlimit: int):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    codes_data[code] = {"credits": creditamount, "limit": claimlimit, "used": []}
    save_json("codes.json", codes_data)
    await interaction.response.send_message(f"✅ Redeem code `{code}` created")

@tree.command(name="redeemcode")
@app_commands.describe(code="Enter code")
async def redeemcode(interaction: discord.Interaction, code: str):
    uid = str(interaction.user.id)
    code_data = codes_data.get(code)
    if not code_data:
        return await interaction.response.send_message("❌ Invalid code")
    if uid in code_data["used"]:
        return await interaction.response.send_message("❌ Already redeemed")
    if len(code_data["used"]) >= code_data["limit"]:
        return await interaction.response.send_message("❌ Code limit reached")
    users_data.setdefault(uid, {"credits": 0})
    users_data[uid]["credits"] += code_data["credits"]
    code_data["used"].append(uid)
    save_json("codes.json", codes_data)
    save_json("users.json", users_data)
    await interaction.response.send_message(f"✅ Redeemed `{code}` for {code_data['credits']} credits!")

@tree.command(name="status")
async def status(interaction: discord.Interaction):
    await interaction.response.send_message("🌐 Panel Status: Online at https://dragoncloud.godanime.net")

@tree.command(name="uptime")
async def uptime(interaction: discord.Interaction):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await interaction.response.send_message(f"🕒 Panel is reachable. Current Time: {now}")

@tree.command(name="freeserver")
async def freeserver(interaction: discord.Interaction):
    await interaction.response.send_message("🎁 Free Plan: 2GB RAM / 1 CPU\nCreate a ticket in <#ticket-channel>")

@tree.command(name="serverlist")
async def serverlist(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{PANEL_URL}/api/application/servers", headers=HEADERS) as r:
            data = await r.json()
            servers = data.get("data", [])
            if not servers:
                return await interaction.response.send_message("❌ No servers found")
            msg = "\n".join([f"🖥️ {s['attributes']['name']} (ID: {s['attributes']['id']})" for s in servers])
            await interaction.response.send_message(f"📋 Servers:\n{msg}")

@tree.command(name="removeserver")
@app_commands.describe(serverid="Panel Server ID")
async def removeserver(interaction: discord.Interaction, serverid: str):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{PANEL_URL}/api/application/servers/{serverid}", headers=HEADERS) as r:
            await interaction.response.send_message("✅ Server removed" if r.status == 204 else "❌ Failed to remove")

@tree.command(name="createmsg")
@app_commands.describe(name="Message name", message="Message content")
async def createmsg(interaction: discord.Interaction, name: str, message: str):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    save_json(f"msg_{name}.json", {"content": message})
    await interaction.response.send_message(f"✅ Saved message `{name}`")

@tree.command(name="new")
@app_commands.describe(channelid="Channel ID", message="Message to send")
async def new(interaction: discord.Interaction, channelid: str, message: str):
    if not is_admin(interaction.user): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
    channel = bot.get_channel(int(channelid))
    if channel:
        await channel.send(message)
        await interaction.response.send_message("✅ Message sent")
    else:
        await interaction.response.send_message("❌ Channel not found")

# -------------------- HELP --------------------
@bot.tree.command(name="help", description="Show list of available commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="📘 Command List", color=discord.Color.green())
    embed.add_field(name="/ownlist <userid>", value="🔒 Admin only: Generate server list for a user.", inline=False)
    embed.add_field(name="/list <userid>", value="📋 Show servers owned by a user.", inline=False)
    embed.add_field(name="/deleteownlist <userid>", value="🗑️ Admin only: Delete stored server list for a user.", inline=False)
    embed.add_field(name="/upgrademc <serverid> <ram> <cpu> <disk>", value="⚙️ Admin only: Upgrade server specs.", inline=False)
    embed.add_field(name="/manage <token>", value="🎮 View & control Minecraft servers (client token)", inline=False)
    embed.add_field(name="/register <userid> <username> <email> <password>", value="🧾 Create panel account.", inline=False)
    embed.add_field(name="/ac <userid> <email> <pass>", value="⚡ Quick account creation.", inline=False)
    embed.add_field(name="/createfree <servername> <email>", value="🚀 Create 4GB Minecraft server.", inline=False)
    embed.add_field(name="/creates", value="📦 Show plan selection (invite/boost).", inline=False)
    embed.add_field(name="/removeall <userid>", value="🗑 Remove all Minecraft servers.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# -------------------- OWNLIST --------------------
@bot.tree.command(name="ownlist", description="Generate random Minecraft server IDs for a user (admin only)")
@app_commands.describe(userid="User's Discord ID")
async def ownlist(interaction: discord.Interaction, userid: str):
    if str(interaction.user.id) not in ADMIN_IDS:
        await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
        return

    servers = [f"{random.randint(100000, 999999)}_IN" for _ in range(3)]

    if not os.path.exists(data_file):
        with open(data_file, "w") as f:
            json.dump({}, f)

    with open(data_file, "r") as f:
        data = json.load(f)
    data[userid] = servers
    with open(data_file, "w") as f:
        json.dump(data, f)

    await interaction.response.send_message(f"✅ Created server list for `{userid}`:\n" + "\n".join(servers), ephemeral=True)

# -------------------- LIST --------------------
@bot.tree.command(name="list", description="List Minecraft servers of a user from /ownlist")
@app_commands.describe(userid="User's Discord ID")
async def list_servers(interaction: discord.Interaction, userid: str):
    try:
        with open(data_file, "r") as f:
            data = json.load(f)
        servers = data.get(userid)
        if not servers:
            await interaction.response.send_message("❌ No servers found for this user.", ephemeral=True)
            return
        msg = f"📋 Servers owned by `{userid}`:\n" + "\n".join(f"- `{s}`" for s in servers)
        await interaction.response.send_message(msg, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"⚠️ Error reading list: {e}", ephemeral=True)

# -------------------- REGISTER --------------------
@bot.tree.command(name="register", description="Register a new panel account")
@app_commands.describe(userid="User ID", username="Username", email="Email", password="Password")
async def register(interaction: discord.Interaction, userid: str, username: str, email: str, password: str):
    if str(interaction.user.id) not in ADMIN_IDS:
        await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
        return
    payload = {
        "username": username,
        "email": email,
        "first_name": username,
        "last_name": "user",
        "password": password
    }
    headers = {
        "Authorization": f"Bearer {PANEL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{PANEL_URL}/api/application/users", headers=headers, json=payload) as resp:
            if resp.status == 201:
                await interaction.response.send_message("✅ Account created successfully.", ephemeral=True)
            else:
                text = await resp.text()
                await interaction.response.send_message(f"❌ Failed: {resp.status} {text}", ephemeral=True)

# -------------------- CREATEFREE --------------------
@bot.tree.command(name="createfree", description="Create default 4GB server")
@app_commands.describe(servername="Name", email="Email")
async def createfree(interaction: discord.Interaction, servername: str, email: str):
    await interaction.response.defer(ephemeral=True)
    name = f"mc-{random.randint(1000, 9999)}"
    payload = {
        "name": servername,
        "user": 1,  # Set user ID manually or from email
        "egg": EGG_ID,
        "docker_image": "ghcr.io/pterodactyl/yolks:java_17",  # Adjust if needed
        "startup": "java -Xms128M -Xmx{{SERVER_MEMORY}}M -jar server.jar",
        "limits": {
            "memory": 4096,
            "swap": 0,
            "disk": 10240,
            "io": 500,
            "cpu": 100
        },
        "feature_limits": {"databases": 1, "backups": 1, "allocations": 1},
        "environment": {
            "SERVER_JARFILE": "server.jar",
            "DL_PATH": "https://api.papermc.io/v2/projects/paper/versions/1.20.1/builds/123/downloads/paper-1.20.1-123.jar",
            "SERVER_PORT": "25565"
        },
        "allocation": {
            "default": 1  # Replace with real allocation ID
        },
        "deploy": {
            "locations": [NODE_ID],
            "dedicated_ip": False,
            "port_range": []
        },
        "start_on_completion": True
    }
    headers = {
        "Authorization": f"Bearer {PANEL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{PANEL_URL}/api/application/servers", headers=headers, json=payload) as resp:
            if resp.status == 201:
                await interaction.followup.send("✅ Successfully created your server. Check panel!", ephemeral=True)
            else:
                text = await resp.text()
                await interaction.followup.send(f"❌ Failed: {resp.status}\n{text}", ephemeral=True)


# -------------------- REMOVEALL --------------------
@bot.tree.command(name="removeall", description="Remove all Minecraft servers by user ID")
@app_commands.describe(userid="User ID")
async def removeall(interaction: discord.Interaction, userid: str):
    if str(interaction.user.id) not in ADMIN_IDS:
        await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
        return
    url = f"{PANEL_URL}/api/application/servers"
    headers = {"Authorization": f"Bearer {PANEL_API_KEY}", "Accept": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                servers = [s for s in data['data'] if str(s['attributes']['user']) == str(userid)]
                count = 0
                for s in servers:
                    sid = s['attributes']['id']
                    await session.delete(f"{url}/{sid}", headers=headers)
                    count += 1
                await interaction.response.send_message(f"✅ Removed {count} servers.", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Error fetching server list.", ephemeral=True)

# -------------------- UPGRADEMC --------------------
@bot.tree.command(name="upgrademc", description="Upgrade Minecraft server specs")
@app_commands.describe(serverid="External Server ID", ram="RAM (MB)", cpu="CPU %", disk="Disk (MB)")
async def upgrademc(interaction: discord.Interaction, serverid: str, ram: int, cpu: int, disk: int):
    if str(interaction.user.id) not in ADMIN_IDS:
        await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    sid = await get_server_internal_id(serverid)
    if not sid:
        await interaction.followup.send("❌ Server ID not found.")
        return
    url = f"{PANEL_URL}/api/application/servers/{sid}/build"
    payload = {
        "memory": ram,
        "disk": disk,
        "cpu": cpu,
        "io": 500,
        "swap": 0,
        "feature_limits": {"databases": 5, "backups": 5, "allocations": 5}
    }
    headers = {"Authorization": f"Bearer {PANEL_API_KEY}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                await interaction.followup.send("✅ Upgrade successful.", ephemeral=True)
            else:
                text = await resp.text()
                await interaction.followup.send(f"❌ Failed: {resp.status}\n{text}", ephemeral=True)

# -------------------- GET SERVER INTERNAL ID --------------------
async def get_server_internal_id(external_id):
    url = f"{PANEL_URL}/api/application/servers"
    headers = {"Authorization": f"Bearer {PANEL_API_KEY}", "Accept": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                for s in data['data']:
                    if s['attributes']['identifier'] == external_id:
                        return s['attributes']['id']
    return None

# -------------------- MANAGE + BUTTONS --------------------
class ServerControlView(discord.ui.View):
    def __init__(self, token: str, serverid: str):
        super().__init__(timeout=None)
        self.token = token
        self.serverid = serverid

    async def send_power_signal(self, interaction: discord.Interaction, signal: str):
        url = f"https://dragoncloud.godanime.net/api/client/servers/{self.serverid}/power"
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json", "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json={"signal": signal}) as resp:
                if resp.status == 204:
                    await interaction.response.send_message(f"✅ `{signal}` sent          await interaction.followup.send(f"✅ Upgraded server `{serverid}`. RAM: `{ram}`, CPU: `{cpu}`, Disk: `{disk}`")
            else:
                text = await resp.text()
                await interaction.followup.send(f"❌ Upgrade failed! Status: {resp.status}\n{text}")

# -------------------- MANAGE + BUTTONS --------------------
class ServerControlView(discord.ui.View):
    def __init__(self, token: str, serverid: str):
        super().__init__(timeout=None)
        self.token = token
        self.serverid = serverid

    async def send_power_signal(self, interaction: discord.Interaction, signal: str):
        url = f"https://dragoncloud.godanime.net/api/client/servers/{self.serverid}/power"
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json", "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json={"signal": signal}) as resp:
                if resp.status == 204:
                    await interaction.response.send_message(f"✅ `{signal}` sent to `{self.serverid}`.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"❌ Failed to send `{signal}`. Status: {resp.status}", ephemeral=True)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success)
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_power_signal(interaction, "start")

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger)
    async def stop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_power_signal(interaction, "stop")

    @discord.ui.button(label="Restart", style=discord.ButtonStyle.primary)
    async def restart_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_power_signal(interaction, "restart")

    @discord.ui.button(label="Reinstall", style=discord.ButtonStyle.secondary)
    async def reinstall_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_power_signal(interaction, "reinstall")

@bot.tree.command(name="manage", description="Show Minecraft servers with token and control buttons")
@app_commands.describe(token="Your Pterodactyl Client API Token")
async def manage(interaction: discord.Interaction, token: str):
    await interaction.response.defer(ephemeral=True)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://dragoncloud.godanime.net/api/client", headers=headers) as resp:
            if resp.status != 200:
                await interaction.followup.send("❌ Invalid token.")
                return
            data = await resp.json()

    servers = data.get("data", [])
    if not servers:
        await interaction.followup.send("❌ No servers found.", ephemeral=True)
        return

    for server in servers:
        sid = server['attributes']['identifier']
        name = server['attributes']['name']
        embed = discord.Embed(title=f"🎮 {name} ({sid})", color=discord.Color.blurple())
        embed.add_field(name="Controls", value="Start / Stop / Restart / Reinstall", inline=False)
        await interaction.followup.send(embed=embed, view=ServerControlView(token, sid), ephemeral=True)

# -------------------- GET SERVER INTERNAL ID --------------------
async def get_server_internal_id(identifier):
    url = "https://dragoncloud.godanime.net/api/application/servers"
    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            for s in data.get("data", []):
                if s['attributes']['identifier'] == identifier:
                    return s['attributes']['id']
    return None

# -------------------- GIVEAWAY --------------------
@bot.tree.command(name="gstart", description="🎉 Start a giveaway (admin only)")
@app_commands.describe(time="Time in minutes", winners="Number of winners", prize="Prize description")
async def gstart(interaction: discord.Interaction, time: int, winners: int, prize: str):
    if str(interaction.user.id) not in ADMIN_IDS:
        await interaction.response.send_message("❌ You are not authorized.", ephemeral=True)
        return

    end_time = datetime.utcnow() + timedelta(minutes=time)
    embed = discord.Embed(title="🎉 Giveaway Started!", color=discord.Color.gold())
    embed.add_field(name="Prize", value=prize, inline=False)
    embed.add_field(name="Ends In", value=f"{time} minutes", inline=False)
    embed.add_field(name="Host", value=interaction.user.mention)
    embed.set_footer(text=f"Ends at {end_time.strftime('%H:%M:%S UTC')}")

    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("🎉")
    await interaction.response.send_message("✅ Giveaway started!", ephemeral=True)

    await asyncio.sleep(time * 60)

    msg = await interaction.channel.fetch_message(msg.id)
    users = await msg.reactions[0].users().flatten()
    users = [u for u in users if not u.bot and u != interaction.user]
    if len(users) < winners:
        await interaction.channel.send("❌ Not enough participants.")
    else:
        winners_list = random.sample(users, winners)
        winner_mentions = ", ".join([w.mention for w in winners_list])
        await interaction.channel.send(f"🎉 Congratulations {winner_mentions}! You won **{prize}**")

# -------------------- CHANGEPASS --------------------
@bot.tree.command(name="changepass", description="🔐 Change user's Pterodactyl password (admin only)")
@app_commands.describe(userid="User ID", api_key="Account API key", newpass="New password", confirmpass="Confirm password")
async def changepass(interaction: discord.Interaction, userid: str, api_key: str, newpass: str, confirmpass: str):
    if newpass != confirmpass:
        await interaction.response.send_message("❌ Passwords do not match.", ephemeral=True)
        return

    if str(interaction.user.id) not in ADMIN_IDS:
        await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)
        return

    headers = {
        "Authorization": f"Bearer {PANEL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    url = f"{PANEL_URL}/api/client/account/password"
    payload = {"current_password": newpass, "password": newpass, "password_confirmation": confirmpass}

    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                await interaction.user.send(f"🔐 Your password has been updated.")
                await interaction.user.send(f"🔑 Account API: `{api_key}`\n🔑 New Password: `{newpass}`")
                await interaction.response.send_message("✅ Password changed and DM sent.", ephemeral=True)
            else:
                text = await resp.text()
                await interaction.response.send_message(f"❌ Failed to update password.\n{text}", ephemeral=True)

# -------------------- ACCOUNTAPI STORE --------------------
@bot.tree.command(name="accountapi", description="📂 Add or show account API info")
@app_commands.describe(userid="User ID", name="Api name", msg="Api Key Enter")
async def accountapi(interaction: discord.Interaction, userid: str, api: str, name: str, msg: str):
    if not os.path.exists(accountapi_file):
        with open(accountapi_file, "w") as f:
            json.dump({}, f)

    with open(accountapi_file, "r") as f:
        data = json.load(f)

    data[userid] = {"name": name, "msg": msg}

    with open(accountapi_file, "w") as f:
        json.dump(data, f)

    await interaction.response.send_message(f"✅ API stored for `{userid}`.", ephemeral=True)
    user = bot.get_user(int(userid))
    if user:
        await user.send(f"📂 API Stored\n🔑 Key: `{api}`\n📛 Name: `{name}`\n📝 Message: {msg}")

# -------------------- Helper to get panel user ID --------------------
async def get_panel_user_id_by_email(email):
    headers = {"Authorization": f"Bearer {PANEL_API_KEY}", "Accept": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{PANEL_URL}/api/application/users", headers=headers) as resp:
            if resp.status == 200:
                users = await resp.json()
                for u in users["data"]:
                    if u["attributes"]["email"].lower() == email.lower():
                        return u["attributes"]["id"]
    return None

# -------------------- /ac COMMAND (store account info) --------------------
@bot.tree.command(name="ac", description="🔑 Store user account info")
@app_commands.describe(userid="User ID", email="Panel email", password="Password")
async def ac(interaction: discord.Interaction, userid: str, email: str, password: str):
    accounts = {}
    if os.path.exists(account_data_file):
        with open(account_data_file, "r") as f:
            accounts = json.load(f)

    accounts[userid] = {"email": email, "password": password}

    with open(account_data_file, "w") as f:
        json.dump(accounts, f)

    await interaction.response.send_message("✅ Account info saved for user.", ephemeral=True)

# -------------------- /creates COMMAND --------------------
@bot.tree.command(name="creates", description="🎮 Create Minecraft server using Boost or Invite plan")
async def creates(interaction: discord.Interaction):
    class PlanSelect(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(label="2x Boost", description="12GB RAM, 4 CPU, 100GB Disk", value="boost2"),
                discord.SelectOption(label="4x Boost", description="24GB RAM, 6 CPU, 150GB Disk", value="boost4"),
                discord.SelectOption(label="6x Boost", description="32GB RAM, 8 CPU, 200GB Disk", value="boost6"),
                discord.SelectOption(label="2 Invite", description="4GB RAM, 100% CPU, 10GB Disk", value="inv2"),
                discord.SelectOption(label="4 Invite", description="6GB RAM, 150% CPU, 20GB Disk", value="inv4"),
                discord.SelectOption(label="7 Invite", description="8GB RAM, 260% CPU, 35GB Disk", value="inv7"),
                discord.SelectOption(label="10 Invite", description="12GB RAM, 290% CPU, 30GB Disk", value="inv10"),
                discord.SelectOption(label="14 Invite", description="16GB RAM, 300% CPU, 40GB Disk", value="inv14"),
            ]
            super().__init__(placeholder="Select your plan", options=options, min_values=1, max_values=1)

        async def callback(self, interaction2: discord.Interaction):
            discord_id = str(interaction.user.id)
            if not os.path.exists(account_data_file):
                await interaction2.response.send_message("❌ No account found. Use /ac first.", ephemeral=True)
                return

            with open(account_data_file, "r") as f:
                acc_data = json.load(f)

            if discord_id not in acc_data:
                await interaction2.response.send_message("❌ You must register using `/ac` before creating a server.", ephemeral=True)
                return

            email = acc_data[discord_id]["email"]
            panel_user_id = await get_panel_user_id_by_email(email)
            if not panel_user_id:
                await interaction2.response.send_message("❌ Panel user not found.", ephemeral=True)
                return

            value = self.values[0]
            plans = {
                "boost2": {"ram": 12288, "cpu": 400, "disk": 100000},
                "boost4": {"ram": 24576, "cpu": 600, "disk": 150000},
                "boost6": {"ram": 32768, "cpu": 800, "disk": 200000},
                "inv2": {"ram": 4096, "cpu": 100, "disk": 10000},
                "inv4": {"ram": 6144, "cpu": 150, "disk": 20000},
                "inv7": {"ram": 8192, "cpu": 260, "disk": 35000},
                "inv10": {"ram": 12288, "cpu": 290, "disk": 30000},
                "inv14": {"ram": 16384, "cpu": 300, "disk": 40000}
            }
            config = plans[value]
            server_name = f"Dragon_{random.randint(1000,9999)}"

            payload = {
                "name": server_name,
                "user": panel_user_id,
                "egg": PANEL_APP_ID,
                "docker_image": "ghcr.io/pterodactyl/yolks:java_17",
                "startup": "java -Xms128M -Xmx{{SERVER_MEMORY}}M -jar server.jar",
                "limits": {
                    "memory": config['ram'],
                    "swap": 0,
                    "disk": config['disk'],
                    "io": 500,
                    "cpu": config['cpu']
                },
                "feature_limits": {"databases": 1, "backups": 1, "allocations": 1},
                "environment": {
                    "DL_VERSION": "latest",
                    "SERVER_JARFILE": "server.jar",
                    "BUILD_NUMBER": "latest",
                    "STARTUP": "java -Xms128M -Xmx{{SERVER_MEMORY}}M -jar server.jar"
                },
                "allocation": {"default": 1},
                "deploy": {"locations": [NODE_ID], "dedicated_ip": False, "port_range": []},
                "start_on_completion": True
            }

            headers = {
                "Authorization": f"Bearer {PANEL_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            await interaction2.response.send_message("🛠️ Creating your server... Please wait...", ephemeral=True)

            async with aiohttp.ClientSession() as session:
                async with session.post(f"{PANEL_URL}/api/application/servers", json=payload, headers=headers) as resp:
                    if resp.status in [200, 201]:
                        await interaction.user.send(f"🎉 **Minecraft Server Created Successfully!**\n\n📛 **Name**: `{server_name}`\n📊 **RAM**: `{config['ram']//1024}GB`\n🧠 **CPU**: `{config['cpu']}%`\n💾 **Disk**: `{config['disk']//1000}GB`\n🌐 [Panel Link]({PANEL_URL})")
                        await interaction.followup.send("✅ Server created and details sent via DM!", ephemeral=True)
                    else:
                        error = await resp.text()
                        await interaction.followup.send(f"❌ Failed to create server.\n``{error}``", ephemeral=True)

    class PlanView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.add_item(PlanSelect())

    await interaction.response.send_message("📦 Please select a plan: (Boost or Invite)", view=PlanView(), ephemeral=True)

    # -------------------- /setupstatus --------------------
@bot.tree.command(name="setupstatus", description="Set channel to post panel node status updates")
@app_commands.describe(channelid="Channel ID to post updates")
async def setupstatus(interaction: discord.Interaction, channelid: str):
    if str(interaction.user.id) not in ADMIN_IDS:
        await interaction.response.send_message("❌ Only admin can use this command.", ephemeral=True)
        return
    with open(status_channel_file, "w") as f:
        f.write(channelid)
    await interaction.response.send_message(f"✅ Status updates will be posted in <#{channelid}>", ephemeral=True)

# -------------------- /nodes --------------------
@bot.tree.command(name="nodes", description="📊 Show panel node stats")
async def nodes(interaction: discord.Interaction):
    headers = {"Authorization": f"Bearer {PANEL_API_KEY}", "Accept": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{PANEL_URL}/api/application/servers/{self.server_id}/allocations", headers=headers) as resp:
          session.get(f"{PANEL_URL}/api/application/nodes/{NODE_ID}", headers=headers) as resp2:
            if resp1.status == 200 and resp2.status == 200:
                allocs = await resp1.json()
                node = await resp2.json()

                name = node['attributes']['name']
                mem = node['attributes']['memory']
                disk = node['attributes']['disk']
                used_mem = node['attributes']['allocated_resources']['memory']
                used_disk = node['attributes']['allocated_resources']['disk']

                embed = discord.Embed(title=f"🧠 Node: {name} Status", color=0x00ff00)
                embed.add_field(name="Memory", value=f"{used_mem}/{mem} MB", inline=True)
                embed.add_field(name="Disk", value=f"{used_disk}/{disk} MB", inline=True)
                embed.set_footer(text="DragonCloud Panel Node Monitor")

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("❌ Failed to fetch node status.", ephemeral=True)

# Background task (if you want auto-posting every X mins)
@tasks.loop(minutes=10)
async def post_status_update():
    if not os.path.exists(status_channel_file):
        return
    with open(status_channel_file, "r") as f:
        channel_id = f.read().strip()
    try:
        channel = bot.get_channel(int(channel_id))
        if channel is None:
            return
        headers = {"Authorization": f"Bearer {PANEL_API_KEY}", "Accept": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{PANEL_URL}/api/application/nodes/{NODE_ID}", headers=headers) as resp:
                if resp.status == 200:
                    node = await resp.json()
                    name = node['attributes']['name']
                    mem = node['attributes']['memory']
                    disk = node['attributes']['disk']
                    used_mem = node['attributes']['allocated_resources']['memory']
                    used_disk = node['attributes']['allocated_resources']['disk']

                    embed = discord.Embed(title=f"🧠 Node: {name} Status", color=0x3498db)
                    embed.add_field(name="Memory", value=f"{used_mem}/{mem} MB", inline=True)
                    embed.add_field(name="Disk", value=f"{used_disk}/{disk} MB", inline=True)
                    embed.timestamp = datetime.utcnow()

                    await channel.send(embed=embed)
    except Exception as e:
        print(f"Status update error: {e}")

post_status_update.start()

bot.run(TOKEN)
