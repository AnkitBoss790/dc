import discord
from discord.ext import commands, tasks
import requests
import json
import os

# Bot setup
TOKEN = 'MTM3NzUyMDQxMDc0NDMyNDIwNg.G3whaQ.EEHaFwq0K31cgCkT8-1zG933i6B2j8_84rl-_k'
PANEL_URL = 'http://panel.dragoncloud.ggff.net'
API_KEY = 'ptlc_OmXsasCHtMYaeSkv2n3KEJq92qw0yJ0s1OOtS9g8DMh'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)

# Simulated database (you should replace this with actual storage like SQLite or JSON file)
user_credits = {}
redeem_codes = {}
admin_ids = set(1159037240622723092)

# ---------------------- Utility ----------------------
def get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "Application/vnd.pterodactyl.v1+json"
    }

# ---------------------- Admin Control ----------------------
@bot.command()
async def add_admin(ctx, user_id: int):
    if ctx.author.guild_permissions.administrator:
        admin_ids.add(user_id)
        await ctx.send(f"✅ Added user {user_id} to admin list.")
    else:
        await ctx.send("❌ Only administrators can add admins.")

@bot.command()
async def status(ctx):
    if ctx.author.id not in admin_ids:
        return await ctx.send("❌ Only admins can use this command.")
    res = requests.get(f"{PANEL_URL}/api/application/servers", headers=get_headers())
    if res.status_code == 200:
        data = res.json()['data']
        msg = "📊 **Panel Servers:**\n"
        for server in data[:10]:
            s = server['attributes']
            msg += f"- {s['name']} | {s['uuidShort']} | Owner: {s['user']}\n"
        await ctx.send(msg)
    else:
        await ctx.send(f"❌ Failed to fetch servers: {res.text}")

@bot.command()
async def removeserver(ctx, user_id: int, email: str):
    if ctx.author.id not in admin_ids:
        return await ctx.send("❌ Only admins can use this command.")
    users = requests.get(f"{PANEL_URL}/api/application/users", headers=get_headers()).json()
    for user in users['data']:
        if user['attributes']['email'] == email:
            uid = user['attributes']['id']
            res = requests.delete(f"{PANEL_URL}/api/application/users/{uid}?force=true", headers=get_headers())
            if res.status_code == 204:
                await ctx.send(f"🗑️ Successfully removed user `{email}` and their servers.")
            else:
                await ctx.send(f"❌ Error removing user: {res.text}")
            return
    await ctx.send("❌ User not found.")

@bot.command()
async def removeaccount(ctx, user_id: int, email: str):
    if ctx.author.id not in admin_ids:
        return await ctx.send("❌ Only admins can use this command.")
    users = requests.get(f"{PANEL_URL}/api/application/users", headers=get_headers()).json()
    for user in users['data']:
        if user['attributes']['email'] == email:
            uid = user['attributes']['id']
            res = requests.delete(f"{PANEL_URL}/api/application/users/{uid}?force=true", headers=get_headers())
            if res.status_code == 204:
                await ctx.send(f"🗑️ Successfully removed user `{email}`.")
            else:
                await ctx.send(f"❌ Error: {res.text}")
            return
    await ctx.send("❌ User not found.")

# ---------------------- Registration Alias ----------------------
@bot.command()
async def register(ctx, email: str, password: str):
    await createaccount(ctx, email, password)

# ---------------------- Account Creation ----------------------
@bot.command()
async def createaccount(ctx, email: str, password: str):
    data = {
        "username": email.split('@')[0],
        "email": email,
        "first_name": ctx.author.name,
        "last_name": "PteroDash",
        "password": password
    }
    res = requests.post(f"{PANEL_URL}/api/application/users", json=data, headers=get_headers())
    if res.status_code == 201:
        user_credits[str(ctx.author.id)] = 250
        await ctx.send(f"✅ Account created at {PANEL_URL} with 250 credits.")
    else:
        await ctx.send(f"❌ Error: {res.text}")

# ---------------------- Credits ----------------------
@bot.command()
async def credits(ctx):
    uid = str(ctx.author.id)
    user_credits.setdefault(uid, 250)
    await ctx.send(f"💰 You have {user_credits[uid]} credits.")

@bot.command()
async def redeem(ctx, code: str):
    uid = str(ctx.author.id)
    if code in redeem_codes:
        amount = redeem_codes.pop(code)
        user_credits[uid] = user_credits.get(uid, 250) + amount + 50
        await ctx.send(f"✅ Redeemed {amount}+50 credits! Total: {user_credits[uid]}")
    else:
        await ctx.send("❌ Invalid or already used code.")

@bot.command()
@commands.has_permissions(administrator=True)
async def addredeemcode(ctx, userid: int, amount: int):
    user_credits[str(userid)] = user_credits.get(str(userid), 250) + amount
    await ctx.send(f"✅ Added {amount} credits to user {userid}.")

@bot.command()
@commands.has_permissions(administrator=True)
async def createredeemcode(ctx, codename: str, amount: int):
    redeem_codes[codename] = amount
    await ctx.send(f"✅ Created redeem code `{codename}` for {amount} credits.")

# ---------------------- Server Creation ----------------------
@bot.command()
async def createserver(ctx):
    uid = str(ctx.author.id)
    if user_credits.get(uid, 250) < 250:
        return await ctx.send("❌ You need at least 250 credits.")

    users = requests.get(f"{PANEL_URL}/api/application/users", headers=get_headers()).json()
    email = f"{ctx.author.name.lower()}@pterodash.fake"
    user_id = None
    for user in users['data']:
        if user['attributes']['email'] == email:
            user_id = user['attributes']['id']
            break
    if not user_id:
        return await ctx.send("❌ You must create an account first using `.createaccount`.")

    nodes = requests.get(f"{PANEL_URL}/api/application/nodes", headers=get_headers()).json()
    options = [n for n in nodes['data'] if n['attributes']['name'].lower() not in ['in1', 'paris']]
    if not options:
        return await ctx.send("❌ No available nodes found.")
    node_id = options[0]['attributes']['id']

    server_data = {
        "name": f"{ctx.author.name}-server",
        "user": user_id,
        "egg": 1,
        "docker_image": "ghcr.io/pterodactyl/yolks:java_17",
        "startup": "java -Xms128M -Xmx{{SERVER_MEMORY}}M -jar server.jar",
        "limits": {
            "memory": 4096,
            "swap": 0,
            "disk": 10240,
            "io": 500,
            "cpu": 150
        },
        "feature_limits": {"databases": 0, "allocations": 1, "backups": 0},
        "environment": {},
        "deploy": {
            "locations": [node_id],
            "dedicated_ip": False,
            "port_range": []
        },
        "allocation": {"default": 1}
    }
    res = requests.post(f"{PANEL_URL}/api/application/servers", json=server_data, headers=get_headers())
    if res.status_code == 201:
        user_credits[uid] -= 250
        await ctx.send(f"✅ Server created at {PANEL_URL}. 250 credits deducted.")
    else:
        await ctx.send(f"❌ Error creating server: {res.text}")

# ---------------------- Server Control ----------------------
@bot.command()
async def servercontrol(ctx):
    uid = str(ctx.author.id)
    users = requests.get(f"{PANEL_URL}/api/application/users", headers=get_headers()).json()
    user_id = None
    for user in users['data']:
        if user['attributes']['email'] == f"{ctx.author.name.lower()}@pterodash.fake":
            user_id = user['attributes']['id']
            break
    if not user_id:
        return await ctx.send("❌ You must create an account first.")

    servers = requests.get(f"{PANEL_URL}/api/application/users/{user_id}/servers", headers=get_headers()).json()
    if not servers['data']:
        return await ctx.send("❌ No servers found for your account.")

    for s in servers['data']:
        name = s['attributes']['name']
        ip = s['attributes']['allocation']['ip_alias'] or s['attributes']['allocation']['ip']
        embed = discord.Embed(title=name, description=f"IP: {ip}", color=0x00ff00)
        embed.add_field(name="Start", value="🟢 `.start <uuid>`", inline=True)
        embed.add_field(name="Stop", value="🔴 `.stop <uuid>`", inline=True)
        embed.add_field(name="Reinstall", value="🟡 `.reinstall <uuid>`", inline=True)
        await ctx.send(embed=embed)

bot.run(TOKEN)
