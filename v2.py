import discord
from discord.ext import commands
import requests
import json
import os
from dotenv import load_dotenv
import rn

# Load environment variables
load_dotenv()
BOT_TOKEN = 'BOT_TOKEN'
PANEL_URL = "http://panel.dragoncloud.ggff.net"
API_KEY = 'ptla_9M4qmqeDpJSioG4L2ZyX5hXfi5QCFq3fOSvslNzPaZR'

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Serving in {len(bot.guilds)} servers')

def sanitize_username(username):
    # Remove invalid characters
    username = re.sub(r'[^a-zA-Z0-9._-]', '', username)
    # Remove leading non-alphanumeric characters
    username = re.sub(r'^[^a-zA-Z0-9]+', '', username)
    # Remove trailing non-alphanumeric characters
    username = re.sub(r'[^a-zA-Z0-9]+$', '', username)
    return username

# Command to register a user
@bot.command(name='register')
async def register(ctx, email: str, password: str):
    """Register a new user with the Dragon Cloud panel"""
    # Security check - delete the message to hide credentials
    try:
        await ctx.message.delete()
    except:
        pass
    
    # API endpoint for registration
    endpoint = f"{PANEL_URL}/api/application/users"
    
    # Registration data
    original_username = interaction.user.name[:16]
sanitized_username = sanitize_username(original_username)

payload = {
    "email": email,
    "username": sanitized_username,
    "first_name": interaction.user.display_name[:32] if interaction.user.display_name else interaction.user.name[:32],
    "last_name": "User",
    "password": password,
    "language": "en",
    "root_admin": False
}

    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        # First check if user already exists
        users_endpoint = f"{PANEL_URL}/api/application/users"
        users_params = {"filter[email]": email}
        users_response = requests.get(users_endpoint, headers=headers, params=users_params)
        
        if users_response.status_code == 200 and len(users_response.json().get('data', [])) > 0:
            await ctx.send(f"❌ Registration failed. A user with email {email} already exists.")
            return
            
        # If user doesn't exist, proceed with registration
        response = requests.post(endpoint, json=payload, headers=headers)
        
        if response.status_code == 201:
            user_data = response.json().get('attributes', {})
            user_id = user_data.get('id')
            
            embed = discord.Embed(
                title="✅ Registration Successful!",
                description=f"{ctx.author.mention}, your account has been created on the Dragon Cloud panel.",
                color=discord.Color.green()
            )
            embed.add_field(name="Username", value=ctx.author.name, inline=True)
            embed.add_field(name="Email", value=email, inline=True)
            embed.add_field(name="User ID", value=user_id, inline=True)
            embed.add_field(name="Panel Link", value=PANEL_URL, inline=False)
            embed.add_field(name="Next Steps", 
                           value="You can now log in to the panel with your email and password. Use the `/createpaper` command to create your server!", 
                           inline=False)
            
            # Send confirmation via DM for extra security
            try:
                await ctx.author.send(embed=embed)
                await ctx.send(f"✅ Registration successful! Check your DMs for details, {ctx.author.mention}.")
            except:
                # If DM fails, send in channel but with less sensitive info
                embed.remove_field(1)  # Remove email field
                await ctx.send(embed=embed)
        else:
            error_message = "Unknown error"
            try:
                error_data = response.json()
                error_message = error_data.get('message', 'Unknown error')
            except:
                pass
            await ctx.send(f"❌ Registration failed. Error: {error_message}")
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

# Check if user already has a server
async def check_user_servers(user_id):
    endpoint = f"{PANEL_URL}/api/application/users/{user_id}?include=servers"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            servers = response.json().get('attributes', {}).get('relationships', {}).get('servers', {}).get('data', [])
            return len(servers)
        else:
            return 0
    except:
        return 0

# Command to create a Paper server with 1 server limit per user
@bot.command(name='createpaper')
async def create_paper_server(ctx, server_name: str, node_id: str = "1"):
    """Create a new Paper Minecraft server (limit 1 per user)"""
    await ctx.send(f"⏳ Processing your Paper server request for '{server_name}'...")
    
    # Attempt to get user ID from the panel based on Discord username
    users_endpoint = f"{PANEL_URL}/api/application/users"
    users_params = {"filter[username]": ctx.author.name}
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }
    
    try:
        # Find user on panel
        users_response = requests.get(users_endpoint, headers=headers, params=users_params)
        
        if users_response.status_code != 200 or len(users_response.json().get('data', [])) == 0:
            await ctx.send(f"❌ You need to register first using `/register [email] [password]`")
            return
        
        # Get the user ID from the response
        user_data = users_response.json()['data'][0]
        user_id = user_data['attributes']['id']
        
        # Check if user already has a server
        server_count = await check_user_servers(user_id)
        if server_count >= 1:
            await ctx.send(f"❌ You already have a server. Only 1 server is allowed per user.")
            return
        
        # API endpoint for server creation
        endpoint = f"{PANEL_URL}/api/application/servers"
        
        # Paper server creation settings with fixed resource limits
        memory = 8192  # 8GB RAM
        cpu = 200      # 200% CPU
        disk = 20000   # 20GB Disk
        
        payload = {
            "name": server_name,
            "user": user_id,
            "egg": 3,  # Egg ID for Paper
            "docker_image": "ghcr.io/pterodactyl/yolks:java_21",
            "startup": "java -Xms128M -Xmx{{SERVER_MEMORY}}M -jar {{SERVER_JARFILE}}",
            "environment": {
                "SERVER_JARFILE": "paper.jar",
                "MINECRAFT_VERSION": "latest",
                "BUILD_NUMBER": "latest"
            },
            "limits": {
                "memory": memory,
                "swap": 0,
                "disk": disk,
                "io": 500,
                "cpu": cpu
            },
            "feature_limits": {
                "databases": 2,
                "backups": 3
            },
            "allocation": {
                "default": node_id
            },
            "start_on_completion": True
        }
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        response = requests.post(endpoint, json=payload, headers=headers)
        
        if response.status_code == 201:
            server_data = response.json().get('attributes', {})
            server_id = server_data.get('id')
            server_identifier = server_data.get('identifier')
            
            embed = discord.Embed(
                title="🎮 Paper Server Created Successfully!",
                description=f"Your Paper Minecraft server has been created with high-performance resources.",
                color=discord.Color.green()
            )
            embed.add_field(name="Server Name", value=server_name, inline=True)
            embed.add_field(name="Server ID", value=server_id, inline=True)
            embed.add_field(name="Memory", value="8GB", inline=True)
            embed.add_field(name="CPU Limit", value="200%", inline=True)
            embed.add_field(name="Disk Space", value="20GB", inline=True)
            embed.add_field(name="Panel Link", value=f"{PANEL_URL}/server/{server_identifier}", inline=False)
            embed.add_field(name="Server Status", value="🚀 Installing & starting automatically", inline=False)
            embed.set_footer(text="Dragon Cloud | High-Performance Minecraft Hosting")
            
            await ctx.send(embed=embed)
        else:
            error_message = "Unknown error"
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_message = error_data['message']
                elif 'errors' in error_data:
                    error_message = json.dumps(error_data['errors'])
            except:
                pass
            await ctx.send(f"❌ Paper server creation failed. Error: {error_message}")
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

# Simple help command
@bot.command(name='dragonhelp')
async def dragon_help(ctx):
    """Show available commands for Dragon Cloud bot"""
    embed = discord.Embed(
        title="Dragon Cloud Bot - Help",
        description="Here are the commands available for Dragon Cloud:",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📝 Registration",
        value="`/register [email] [password]` - Register a new user account\n" +
              "**Example:** `/register user@example.com mypassword123`",
        inline=False
    )
    
    embed.add_field(
        name="🖥️ Server Creation",
        value="`/createpaper [server_name] [node_id]` - Create a Paper Minecraft server\n" +
              "**Example:** `/createpaper MySurvivalServer 1`\n" +
              "**Limits:** 1 server per user, 8GB RAM, 200% CPU, 20GB Disk",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Bot Help",
        value="`/dragonhelp` - Show this help message",
        inline=False
    )
    
    embed.set_footer(text="Dragon Cloud | Premium Minecraft Hosting")
    
    await ctx.send(embed=embed)

# Run the bot
bot.run(TOKEN)
