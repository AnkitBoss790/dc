import discord
from discord.ext import commands
import requests
import json
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()
BOT_TOKEN = 'BOT_TOKEN'
PANEL_URL = "http://panel.dragoncloud.ggff.net"
API_KEY = 'ptla_9M4qmqeDpJSioG4L2ZyX5hXfi5QCFq3fOSvslNzPaZR'

# Initialize bot with slash commands support
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Serving in {len(bot.guilds)} servers')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Test API connection function
async def test_api_connection():
    """Test if the API is accessible"""
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Accept": "application/json"
        }
        
        # Test with a simple API call
        response = requests.get(f"{PANEL_URL}/api/application/users?per_page=1", headers=headers, timeout=10)
        return response.status_code, response.text
    except requests.exceptions.RequestException as e:
        return None, str(e)

# Slash command for registration
@bot.tree.command(name="register", description="Register a new user with the Dragon Cloud panel")
async def register_slash(interaction: discord.Interaction, email: str, password: str):
    """Register a new user with the Dragon Cloud panel"""
    
    # Defer the response to avoid timeout
    await interaction.response.defer(ephemeral=True)
    
    # Test API connection first
    status_code, response_text = await test_api_connection()
    if status_code is None:
        await interaction.followup.send(f"❌ Cannot connect to Dragon Cloud panel. Error: {response_text}", ephemeral=True)
        return
    elif status_code != 200:
        await interaction.followup.send(f"❌ API connection failed. Status: {status_code}. Please check API key.", ephemeral=True)
        return
    
    # API endpoint for registration
    endpoint = f"{PANEL_URL}/api/application/users"
    
    # Registration data with more specific fields
    payload = {
        "email": email,
        "username": interaction.user.name[:16],  # Pterodactyl has username length limits
        "first_name": interaction.user.display_name[:32] if interaction.user.display_name else interaction.user.name[:32],
        "last_name": "User",
        "password": password,
        "language": "en",
        "root_admin": False
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "DragonCloudBot/1.0"
    }
    
    try:
        # First check if user already exists by email
        check_endpoint = f"{PANEL_URL}/api/application/users"
        check_params = {"filter[email]": email}
        check_response = requests.get(check_endpoint, headers=headers, params=check_params, timeout=10)
        
        if check_response.status_code == 200:
            existing_users = check_response.json().get('data', [])
            if len(existing_users) > 0:
                await interaction.followup.send(f"❌ Registration failed. A user with email `{email}` already exists.", ephemeral=True)
                return
        
        # Also check by username
        check_params = {"filter[username]": payload["username"]}
        check_response = requests.get(check_endpoint, headers=headers, params=check_params, timeout=10)
        
        if check_response.status_code == 200:
            existing_users = check_response.json().get('data', [])
            if len(existing_users) > 0:
                # Append numbers to make username unique
                original_username = payload["username"]
                for i in range(1, 100):
                    new_username = f"{original_username}{i}"
                    check_params = {"filter[username]": new_username}
                    check_response = requests.get(check_endpoint, headers=headers, params=check_params, timeout=10)
                    if check_response.status_code == 200 and len(check_response.json().get('data', [])) == 0:
                        payload["username"] = new_username
                        break
        
        # Proceed with registration
        print(f"Attempting registration with payload: {json.dumps(payload, indent=2)}")
        response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        
        print(f"Registration response status: {response.status_code}")
        print(f"Registration response text: {response.text}")
        
        if response.status_code == 201:
            user_data = response.json().get('attributes', {})
            user_id = user_data.get('id')
            username = user_data.get('username')
            
            embed = discord.Embed(
                title="✅ Registration Successful!",
                description=f"{interaction.user.mention}, your account has been created on the Dragon Cloud panel.",
                color=discord.Color.green()
            )
            embed.add_field(name="Username", value=username, inline=True)
            embed.add_field(name="Email", value=email, inline=True)
            embed.add_field(name="User ID", value=user_id, inline=True)
            embed.add_field(name="Panel Link", value=PANEL_URL, inline=False)
            embed.add_field(name="Next Steps", 
                           value="You can now log in to the panel with your email and password. Use the `/createpaper` command to create your server!", 
                           inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        elif response.status_code == 422:
            # Validation errors
            try:
                error_data = response.json()
                errors = error_data.get('errors', {})
                error_messages = []
                for field, field_errors in errors.items():
                    for error in field_errors:
                        error_messages.append(f"**{field}**: {error}")
                
                error_text = "\n".join(error_messages) if error_messages else "Validation failed"
                await interaction.followup.send(f"❌ Registration failed due to validation errors:\n{error_text}", ephemeral=True)
            except:
                await interaction.followup.send(f"❌ Registration failed. Validation error. Response: {response.text}", ephemeral=True)
        else:
            error_message = "Unknown error"
            try:
                error_data = response.json()
                error_message = error_data.get('message', f'HTTP {response.status_code}')
                if 'errors' in error_data:
                    error_message += f"\nDetails: {json.dumps(error_data['errors'])}"
            except:
                error_message = f"HTTP {response.status_code}: {response.text}"
            
            await interaction.followup.send(f"❌ Registration failed. Error: {error_message}", ephemeral=True)
            
    except requests.exceptions.Timeout:
        await interaction.followup.send("❌ Registration failed. Request timed out. Please try again.", ephemeral=True)
    except requests.exceptions.ConnectionError:
        await interaction.followup.send("❌ Registration failed. Cannot connect to Dragon Cloud panel.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)
        print(f"Registration error: {e}")

# Check if user already has a server
async def check_user_servers(username):
    """Check how many servers a user has"""
    try:
        # First get user by username
        users_endpoint = f"{PANEL_URL}/api/application/users"
        users_params = {"filter[username]": username}
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Accept": "application/json"
        }
        
        users_response = requests.get(users_endpoint, headers=headers, params=users_params, timeout=10)
        
        if users_response.status_code != 200 or len(users_response.json().get('data', [])) == 0:
            return -1  # User not found
        
        user_id = users_response.json()['data'][0]['attributes']['id']
        
        # Get user's servers
        servers_endpoint = f"{PANEL_URL}/api/application/users/{user_id}?include=servers"
        servers_response = requests.get(servers_endpoint, headers=headers, timeout=10)
        
        if servers_response.status_code == 200:
            user_data = servers_response.json().get('attributes', {})
            servers = user_data.get('relationships', {}).get('servers', {}).get('data', [])
            return len(servers)
        else:
            return 0
            
    except Exception as e:
        print(f"Error checking user servers: {e}")
        return 0

# Slash command for creating Paper server
@bot.tree.command(name="createserver", description="Create a new Paper Minecraft server (limit 1 per user)")
async def createpaper_slash(interaction: discord.Interaction, server_name: str, node_id: int = 1):
    """Create a new Paper Minecraft server (limit 1 per user)"""
    
    # Defer the response
    await interaction.response.defer()
    
    # Clean server name (remove special characters)
    import re
    clean_server_name = re.sub(r'[^a-zA-Z0-9\-_\s]', '', server_name)[:40]
    
    # Test API connection
    status_code, response_text = await test_api_connection()
    if status_code is None:
        await interaction.followup.send(f"❌ Cannot connect to Dragon Cloud panel. Error: {response_text}")
        return
    elif status_code != 200:
        await interaction.followup.send(f"❌ API connection failed. Status: {status_code}")
        return
    
    # Check if user is registered
    username = interaction.user.name[:16]
    server_count = await check_user_servers(username)
    
    if server_count == -1:
        await interaction.followup.send(f"❌ You need to register first using `/register [email] [password]`")
        return
    
    if server_count >= 1:
        await interaction.followup.send(f"❌ You already have {server_count} server(s). Only 1 server is allowed per user.")
        return
    
    # Get user data for server creation
    try:
        users_endpoint = f"{PANEL_URL}/api/application/users"
        users_params = {"filter[username]": username}
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Accept": "application/json"
        }
        
        users_response = requests.get(users_endpoint, headers=headers, params=users_params, timeout=10)
        user_id = users_response.json()['data'][0]['attributes']['id']
        
        # API endpoint for server creation
        endpoint = f"{PANEL_URL}/api/application/servers"
        
        # Paper server creation settings
        memory = 8192  # 8GB RAM
        cpu = 200      # 200% CPU
        disk = 20000   # 20GB Disk
        
        payload = {
            "name": clean_server_name,
            "user": user_id,
            "egg": 3,  # Paper egg ID (adjust if needed)
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
        
        headers["Content-Type"] = "application/json"
        
        print(f"Creating server with payload: {json.dumps(payload, indent=2)}")
        response = requests.post(endpoint, json=payload, headers=headers, timeout=20)
        
        print(f"Server creation response status: {response.status_code}")
        print(f"Server creation response: {response.text}")
        
        if response.status_code == 201:
            server_data = response.json().get('attributes', {})
            server_id = server_data.get('id')
            server_identifier = server_data.get('identifier')
            
            embed = discord.Embed(
                title="🎮 Paper Server Created Successfully!",
                description=f"Your Paper Minecraft server has been created with high-performance resources.",
                color=discord.Color.green()
            )
            embed.add_field(name="Server Name", value=clean_server_name, inline=True)
            embed.add_field(name="Server ID", value=server_id, inline=True)
            embed.add_field(name="Memory", value="8GB", inline=True)
            embed.add_field(name="CPU Limit", value="200%", inline=True)
            embed.add_field(name="Disk Space", value="20GB", inline=True)
            embed.add_field(name="Panel Link", value=f"{PANEL_URL}/server/{server_identifier}", inline=False)
            embed.add_field(name="Server Status", value="🚀 Installing & starting automatically", inline=False)
            embed.set_footer(text="Dragon Cloud | High-Performance Minecraft Hosting")
            
            await interaction.followup.send(embed=embed)
        else:
            error_message = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_message = error_data['message']
                elif 'errors' in error_data:
                    error_message = json.dumps(error_data['errors'])
            except:
                error_message = response.text
            
            await interaction.followup.send(f"❌ Paper server creation failed. Error: {error_message}")
            
    except Exception as e:
        await interaction.followup.send(f"❌ An error occurred during server creation: {str(e)}")
        print(f"Server creation error: {e}")

# Slash command for help
@bot.tree.command(name="help", description="Show available commands for Dragon Cloud bot")
async def help_slash(interaction: discord.Interaction):
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
        value="`/createserver [server_name] [node_id]` - Create a Paper Minecraft server\n" +
              "**Example:** `/createserver MySurvivalServer 1`\n" +
              "**Limits:** 1 server per user, 8GB RAM, 200% CPU, 20GB Disk",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Bot Help",
        value="`/help` - Show this help message",
        inline=False
    )
    
    embed.set_footer(text="Dragon Cloud | Premium Minecraft Hosting")
    
    await interaction.response.send_message(embed=embed)

# Debug command to test API
@bot.tree.command(name="testapi", description="Test API connection (admin only)")
async def test_api_slash(interaction: discord.Interaction):
    """Test API connection"""
    await interaction.response.defer(ephemeral=True)
    
    status_code, response_text = await test_api_connection()
    
    if status_code is None:
        await interaction.followup.send(f"❌ API Connection Failed: {response_text}", ephemeral=True)
    else:
        await interaction.followup.send(f"✅ API Connection Successful: Status {status_code}", ephemeral=True)

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)
