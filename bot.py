import discord
from discord.ext import commands
from discord import app_commands
import json
import aiohttp
import asyncio
import os
from datetime import datetime

TOKEN = ""
ADMIN_ID = "1159037240622723092"
PANEL_URL = "https://dragoncloud.godanime.net"
api_key = "ptla_D48KU0Liqs1CpSOayM9YtUxfXoaqzGwgk6SR2RTvliC"
HEADERS = {"Authorization": f"Bearer [api_key]", "Content-Type": "application/json"}

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
        "first_name": "free",
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

# /status
@tree.command(name="status", description="Show node status")
async def status(interaction: discord.Interaction):
    await interaction.response.send_message("🌐 Check panel status: https://dragoncloud.godanime.net", ephemeral=True)

# /freeserver
@tree.command(name="freeserver", description="Show Free Plan Info")
async def freeserver(interaction: discord.Interaction):
    await interaction.response.send_message("🆓 DragonCloud Free Plan\nUse `/createaccount` to register and open a ticket in #support.", ephemeral=True)

# /credits
@tree.command(name="credits", description="Check your credit balance")
async def credits(interaction: discord.Interaction):
    data = load_json("credits.json")
    credits = data.get(str(interaction.user.id), 0)
    await interaction.response.send_message(f"💰 You have `{credits}` credits.", ephemeral=True)

# /dailycredits
@tree.command(name="dailycredits", description="Claim 20 daily credits")
async def dailycredits(interaction: discord.Interaction):
    data = load_json("credits.json")
    uid = str(interaction.user.id)
    data[uid] = data.get(uid, 0) + 20
    save_json("credits.json", data)
    await interaction.response.send_message("✅ 20 credits added!", ephemeral=True)

# /redeemcode
@tree.command(name="redeemcode", description="Redeem a code for credits")
@app_commands.describe(code="Your redeem code")
async def redeemcode(interaction: discord.Interaction, code: str):
    codes = load_json("redeemcodes.json")
    if code in codes:
        info = codes[code]
        uid = str(interaction.user.id)
        if uid not in info["claimed"]:
            info["claimed"].append(uid)
            if len(info["claimed"]) <= info["limit"]:
                credits = load_json("credits.json")
                credits[uid] = credits.get(uid, 0) + info["amount"]
                save_json("credits.json", credits)
                save_json("redeemcodes.json", codes)
                await interaction.response.send_message("✅ Code redeemed!", ephemeral=True)
                return
            else:
                await interaction.response.send_message("❌ Code claim limit reached.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ You already claimed this code.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Invalid code.", ephemeral=True)

# /createredeemcode
@tree.command(name="createredeemcode", description="Create a redeem code (admin only)")
@app_commands.describe(name="Code name", amount="Credit amount", limit="Max users")
async def createredeemcode(interaction: discord.Interaction, name: str, amount: int, limit: int):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)
        return
    codes = load_json("redeemcodes.json")
    codes[name] = {"amount": amount, "limit": limit, "claimed": []}
    save_json("redeemcodes.json", codes)
    await interaction.response.send_message(f"✅ Code `{name}` created.", ephemeral=True)

# /uptime
@tree.command(name="uptime", description="Check panel uptime")
async def uptime(interaction: discord.Interaction):
    await interaction.response.send_message("🟢 Panel status: https://dragoncloud.godanime.net", ephemeral=True)

# /manage
@tree.command(name="manage", description="Manage a user server (admin only)")
@app_commands.describe(userid="User ID", email="Email", password="Password")
async def manage(interaction: discord.Interaction, userid: str, email: str, password: str):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)
        return
    embed = discord.Embed(title=f"Manage Server: {userid}", color=discord.Color.green())
    embed.add_field(name="🟢 Start", value="Start Server Your", inline=True)
    embed.add_field(name="🔴 Stop", value="Stop Server Your", inline=True)
    embed.add_field(name="🔁 Reinstall", value="reinstall your server", inline=True)
    embed.set_footer(text=f"Panel: {email} / {password}")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# /createip
@tree.command(name="createip", description="Generate Playit.gg IP (admin only)")
@app_commands.describe(email="Panel email", password="Panel password")
async def createip(interaction: discord.Interaction, email: str, password: str):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)
        return
    user = interaction.user
    await user.send("🌐 Your server IP has been generated via Playit.gg:\nIP: playit.example.net\nPort: 10222")
    await interaction.response.send_message("✅ Playit.gg IP sent via DM.", ephemeral=True)

bot.run(TOKEN)
