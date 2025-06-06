import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction
import json
import aiohttp
import os

# Load config
with open("config.json") as f:
    config = json.load(f)

TOKEN = config["token"]
ADMIN_FILE = "admins.json"
MSG_FILE = "messages.json"
PANEL_URL = "https://dragoncloud.godanime.net"
API_KEY = config["api_key"]
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

# Load admins
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

# Check admin decorator
def is_admin(user_id):
    return str(user_id) in admins

def admin_only():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot ready as {bot.user}")

# /ping
@tree.command(name="ping", description="Show bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! `{round(bot.latency * 1000)}ms`")

# /addadmin
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

# /createaccount
@tree.command(name="createaccount", description="Create DragonCloud account (admin only)")
@app_commands.describe(userid="Discord User ID", email="Email", password="Password")
@admin_only()
async def createaccount(interaction: discord.Interaction, userid: str, email: str, password: str):
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
                try:
                    user = await bot.fetch_user(int(userid))
                    await user.send(f"✅ Your DragonCloud account has been created!\nEmail: `{email}`\nPassword: `{password}`")
                except:
                    pass
                await interaction.response.send_message("✅ Account created and sent via DM.", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Failed to create account: {data}", ephemeral=True)

# /removeaccount
@tree.command(name="removeaccount", description="Remove DragonCloud account (admin only)")
@app_commands.describe(userid="Discord User ID")
@admin_only()
async def removeaccount(interaction: discord.Interaction, userid: str):
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

# /new - send msg to channel
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

# Manage buttons for /manage command
class ManageButtons(ui.View):
    def __init__(self, userid, email, password):
        super().__init__(timeout=300)
        self.userid = userid
        self.email = email
        self.password = password

    async def interaction_check(self, interaction: Interaction) -> bool:
        # Only admins can use buttons
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("❌ Not authorized.", ephemeral=True)
            return False
        return True

    @ui.button(label="Start", style=discord.ButtonStyle.green)
    async def start_button(self, interaction: Interaction, button: ui.Button):
        # Call API to start server
        success = await control_server(self.userid, "start")
        if success:
            await interaction.response.send_message(f"🟢 Server `{self.userid}` started.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Failed to start server `{self.userid}`.", ephemeral=True)

    @ui.button(label="Stop", style=discord.ButtonStyle.red)
    async def stop_button(self, interaction: Interaction, button: ui.Button):
        success = await control_server(self.userid, "stop")
        if success:
            await interaction.response.send_message(f"🔴 Server `{self.userid}` stopped.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Failed to stop server `{self.userid}`.", ephemeral=True)

    @ui.button(label="Reinstall", style=discord.ButtonStyle.blurple)
    async def reinstall_button(self, interaction: Interaction, button: ui.Button):
        success = await control_server(self.userid, "reinstall")
        if success:
            await interaction.response.send_message(f"🔁 Server `{self.userid}` reinstalled.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Failed to reinstall server `{self.userid}`.", ephemeral=True)

# Helper function to check server existence and control it via API
async def control_server(userid: str, action: str) -> bool:
    # 1. Find server by userid
    # 2. Call start/stop/reinstall API
    # 3. Return True/False based on success

    async with aiohttp.ClientSession() as session:
        # Get user servers
        async with session.get(f"{PANEL_URL}/api/application/users", headers=HEADERS) as resp:
            if resp.status != 200:
                return False
            users = await resp.json()
            user_id = None
            for u in users.get("data", []):
                if u["attributes"]["username"] == userid:
                    user_id = u["attributes"]["id"]
                    break
            if not user_id:
                return False

        # Get servers of this user
        async with session.get(f"{PANEL_URL}/api/application/users/{user_id}/servers", headers=HEADERS) as resp:
            if resp.status != 200:
                return False
            servers = await resp.json()
            if not servers.get("data"):
                return False
            server = servers["data"][0]  # Assuming 1 server per user
            server_id = server["attributes"]["id"]
            server_ip = server["attributes"]["allocation"]["alias"] if server["attributes"].get("allocation") else "Unknown IP"

        # Perform action
        url = f"{PANEL_URL}/api/application/servers/{server_id}/power"
        payload = {"signal": action}  # 'start', 'stop', 'kill', 'restart'
        # For reinstall, call server reinstall endpoint (not in power API)
        if action == "reinstall":
            url = f"{PANEL_URL}/api/application/servers/{server_id}/reinstall"
            async with session.post(url, headers=HEADERS) as resp:
                return resp.status == 204

        async with session.post(url, headers=HEADERS, json=payload) as resp:
            return resp.status == 204 or resp.status == 202

# /manage
@tree.command(name="manage", description="Manage user server (admin only)")
@app_commands.describe(userid="User ID", email="Email", password="Password")
@admin_only()
async def manage(interaction: discord.Interaction, userid: str, email: str, password: str):
    # Check if server exists and get IP
    async with aiohttp.ClientSession() as session:
        # Find user id
        async with session.get(f"{PANEL_URL}/api/application/users", headers=HEADERS) as resp:
            if resp.status != 200:
                await interaction.response.send_message("❌ Failed to fetch users from panel.", ephemeral=True)
                return
            users = await resp.json()
            user_id = None
            for u in users.get("data", []):
                if u["attributes"]["username"] == userid:
                    user_id = u["attributes"]["id"]
                    break
            if not user_id:
                await interaction.response.send_message(f"❌ User `{userid}` not found.", ephemeral=True)
                return

        # Get servers of this user
        async with session.get(f"{PANEL_URL}/api/application/users/{user_id}/servers", headers=HEADERS) as resp:
            if resp.status != 200:
                await interaction.response.send_message(f"❌ Failed to fetch servers of user `{userid}`.", ephemeral=True)
                return
            servers = await resp.json()
            if not servers.get("data"):
                await interaction.response.send_message(f"❌ User `{userid}` has no servers.", ephemeral=True)
                return
            server = servers["data"][0]
            server_ip = server["attributes"]["allocation"]["alias"] if server["attributes"].get("allocation") else "Unknown IP"

    embed = discord.Embed(title=f"Manage Server: {userid}", color=discord.Color.green())
    embed.add_field(name="🟢 Start", value="Click the button to start server", inline=True)
    embed.add_field(name="🔴 Stop", value="Click the button to stop server", inline=True)
    embed.add_field(name="🔁 Reinstall", value="Click the button to reinstall server", inline=True)
    embed.add_field(name="🌐 Server IP", value=server_ip, inline=False)

    view = ManageButtons(userid, email, password)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# /botinfo
@tree.command(name="botinfo", description="Show bot info")
async def botinfo(interaction: discord.Interaction):
    await interaction.response.send_message("🤖 Bot made by Gamerzhacker")

# /createmsg
@tree.command(name="createmsg", description="Create a named message (admin only)")
@app_commands.describe(name="Message name", message="Message content")
@admin_only()
async def createmsg(interaction: discord.Interaction, name: str, message: str):
    messages[name] = message
    save_messages(messages)
    await interaction.response.send_message(f"✅ Message `{name}` saved.", ephemeral=True)

bot.run(TOKEN)
