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
API_KEY = ""
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
    embed.add_field(name="/upgrademc <userid> <serverid> <ram> <cpu> <disk>", value="⚙️ Admin only: Upgrade a server via Pterodactyl API.", inline=False)
    embed.add_field(name="/deleteownlist <userid>", value="🗑️ Admin only: Delete stored server list for a user.", inline=False)
    embed.add_field(name="/manage <email> <password>", value="🎮 Show Minecraft server control buttons (start, stop, reboot, reinstall, get IP)", inline=False)
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

# -------------------- DELETE OWNLIST --------------------
@bot.tree.command(name="deleteownlist", description="Delete stored Minecraft server list for a user (admin only)")
@app_commands.describe(userid="User's Discord ID")
async def deleteownlist(interaction: discord.Interaction, userid: str):
    if str(interaction.user.id) not in ADMIN_IDS:
        await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
        return

    try:
        with open(data_file, "r") as f:
            data = json.load(f)

        if userid in data:
            del data[userid]
            with open(data_file, "w") as f:
                json.dump(data, f)
            await interaction.response.send_message(f"🗑️ Deleted server list for `{userid}`.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No data found for this user.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"⚠️ Error: {e}", ephemeral=True)

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

# -------------------- UPGRADEMC --------------------
@bot.tree.command(name="upgrademc", description="Upgrade RAM/CPU/Disk of a Minecraft server")
@app_commands.describe(userid="User ID", serverid="Server ID", ram="RAM (MB, e.g., 12288)", cpu="CPU % (e.g., 100)", disk="Disk (MB, e.g., 20480)")
async def upgrademc(interaction: discord.Interaction, userid: str, serverid: str, ram: int, cpu: int, disk: int):
    if str(interaction.user.id) not in ADMIN_IDS:
        await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    internal_id = await get_server_internal_id(serverid)
    if not internal_id:
        await interaction.followup.send(f"❌ Server `{serverid}` not found.")
        return

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    url = f"https://dragoncloud.godanime.net/api/application/servers/{internal_id}/build"

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
                await interaction.followup.send(f"✅ Server `{serverid}` upgraded!\nRAM: `{ram}MB`, CPU: `{cpu}%`, Disk: `{disk}MB`")
            else:
                text = await resp.text()
                await interaction.followup.send(f"❌ Upgrade failed: `{resp.status}`\n{text}")

# -------------------- MANAGE --------------------
@bot.tree.command(name="manage", description="Manage your Minecraft servers (Start, Stop, Reboot, Reinstall, IP)")
@app_commands.describe(email="Your Panel Email", password="Your Panel Password")
async def manage(interaction: discord.Interaction, email: str, password: str):
    await interaction.response.defer(ephemeral=True)
    cookies = await get_panel_cookies(email, password)
    if not cookies:
        await interaction.followup.send("❌ Login failed. Check your credentials.")
        return
    servers = await get_minecraft_servers(cookies, interaction.user.id)
    if not servers:
        await interaction.followup.send("⚠️ No servers found.")
        return

    view = discord.ui.View()
    for s in servers:
        sid = s['attributes']['identifier']
        name = s['attributes']['name']
        view.add_item(discord.ui.Button(label=f"Start {name}", style=discord.ButtonStyle.green, custom_id=f"start_{sid}"))
        view.add_item(discord.ui.Button(label=f"Stop {name}", style=discord.ButtonStyle.red, custom_id=f"stop_{sid}"))
        view.add_item(discord.ui.Button(label=f"Reboot {name}", style=discord.ButtonStyle.blurple, custom_id=f"restart_{sid}"))
        view.add_item(discord.ui.Button(label=f"Reinstall {name}", style=discord.ButtonStyle.gray, custom_id=f"reinstall_{sid}"))
    await interaction.followup.send("🎮 Server controls loaded:", view=view, ephemeral=True)

# -------------------- HELPERS --------------------
async def get_panel_cookies(email, password):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://dragoncloud.godanime.net/auth/login", data={
                "email": email,
                "password": password
            }) as resp:
                if resp.status in [200, 302]:
                    return session.cookie_jar.filter_cookies("https://dragoncloud.godanime.net")
    except:
        pass
    return None

async def get_minecraft_servers(cookies, userid):
    headers = {'Accept': 'application/json'}
    try:
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get("https://dragoncloud.godanime.net/api/client", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [s for s in data['data'] if str(s['attributes']['user']) == str(userid)]
    except:
        pass
    return []

async def get_server_internal_id(external_identifier):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }
    url = "https://dragoncloud.godanime.net/api/application/servers"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                for server in data["data"]:
                    if server["attributes"]["identifier"] == external_identifier:
                        return server["attributes"]["id"]
    return None

bot.run(TOKEN)
