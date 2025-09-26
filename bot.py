# main.py
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# --- BOT SETUP ---
# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# IMPORTANT: Add your Discord User ID to your .env file for the owner-only command.
# Example: OWNER_ID="123456789012345678"
OWNER_ID = os.getenv('OWNER_ID')


# It's recommended to define intents for your bot.
# For the bot to see members in a server, you need to enable the members intent.
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True # <-- IMPORTANT: This is required to get member information reliably.
intents.bans = True # <-- IMPORTANT: This is required to check for bans.

# Create a bot instance with a command prefix and the defined intents
bot = commands.Bot(command_prefix='!', intents=intents)

# --- CONFIGURATION ---
# Server and Role IDs you provided.
SERVER_CONFIG = {
    "your_server": { # <- Change the Name used by the bot for the server
        "id": 0, # <- Change to your Server ID
        "name": "Your Server", # <- Change to the Name you want the Bot to Say
        "pnetwork_verified_role": {
            "id": 0, # <- Change this to the Paw Network Verified Role 
            "name": "Paw Network Verified" 
        },
        "roles_to_check": {
            0: "Verified" # <- Change to your Verifed Role
        },
        "unverified_roles": {
            0: "Unverified" # <- Change to your Unverifed Role
        },
        "owner_roles": {
            0: "Owner" # <- Change to your Owner Role
        },
        "staff_roles": {
            0: "Staff" # <- Change to your Staff Roles
        }
    }
}


# --- EVENTS ---
@bot.event
async def on_ready():
    """
    This event is triggered when the bot has successfully connected to Discord.
    It prints a confirmation message to the console and syncs the slash commands.
    """
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('Bot is ready and online!')
    await bot.change_presence(activity=discord.Game(name="Checking IDs"))
    try:
        # Sync the slash commands to the command tree
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# --- SLASH COMMANDS (Preferred Method) ---
@bot.tree.command(name="ping", description="Replies with the bot's latency.")
async def ping(interaction: discord.Interaction):
    """
    A simple slash command that replies with the bot's latency in milliseconds.
    This is a great way to check if the bot is responsive.
    """
    # Calculate the latency
    latency = round(bot.latency * 1000)
    # Respond to the interaction
    await interaction.response.send_message(f'Pong! Latency: {latency}ms')

@bot.tree.command(name="checkroles", description="Checks a user's verification roles in configured servers.")
@discord.app_commands.describe(user="The user you want to check.")
async def checkroles(interaction: discord.Interaction, user: discord.User): # Changed discord.Member to discord.User
    """
    Checks for specific roles for a given user across two pre-configured servers.
    This now accepts any valid Discord user, not just members of the current server.
    """
    # Defer the response to give the bot time to fetch information
    await interaction.response.defer()

    # Create an embed to display the results
    embed = discord.Embed(
        title=f"Role Verification for {user.name}", # Changed to user.name for global username
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    # Flags to track overall status across all servers
    is_banned_anywhere = False
    is_owner = False
    is_staff = False
    has_any_verified_role = False
    has_any_unverified_role = False
    is_in_at_least_one_server = False
    all_servers_found = True

    # Iterate through the servers defined in the config
    for server_key, config in SERVER_CONFIG.items():
        server_id = config["id"]
        server_name = config["name"]
        
        # Try to find the server (guild) the bot is in
        guild = bot.get_guild(server_id)
        if not guild:
            embed.add_field(
                name=f"❌ Server Not Found: {server_name}",
                value=f"I am not a member of this server. Please invite me.",
                inline=False
            )
            all_servers_found = False
            continue

        # --- BAN CHECK (Highest Priority) ---
        try:
            await guild.fetch_ban(user)
            # If the above line doesn't error, the user is banned.
            is_banned_anywhere = True
            embed.add_field(
                name=f"Status in {guild.name}",
                value="🚫 **BANNED**",
                inline=False
            )
            continue # Skip role checks for this server
        except discord.NotFound:
            # User is not banned, proceed with role checks.
            pass
        except discord.Forbidden:
            # Bot doesn't have ban permissions
            embed.add_field(
                name=f"⚠️ Permission Error in {guild.name}",
                value="I don't have permission to view the ban list.",
                inline=False
            )

        # --- ROLE CHECKS ---
        roles_to_check = config["roles_to_check"]
        unverified_roles_to_check = config.get("unverified_roles", {})
        staff_roles_to_check = config.get("staff_roles", {})
        owner_roles_to_check = config.get("owner_roles", {})
        pnetwork_role_config = config.get("pnetwork_verified_role", {})

        # Try to find the member in that server
        try:
            member = await guild.fetch_member(user.id)
        except discord.NotFound:
            member = None # User is not in this guild
        
        if not member:
            embed.add_field(
                name=f"Status in {guild.name}",
                value=f"User is not a member of this server.",
                inline=False
            )
            continue
        
        is_in_at_least_one_server = True

        # --- Role checks for the CURRENT server ---
        # Local flags for this server iteration
        member_is_owner_in_server = False
        member_is_staff_in_server = False
        
        # Build the display list for this server
        status_lines = []

        # Check for Owner roles first
        for role_id in owner_roles_to_check:
            if any(r.id == role_id for r in member.roles):
                member_is_owner_in_server = True
                is_owner = True # Update the global flag for final footer
                break
        
        if member_is_owner_in_server:
            status_lines.append("👑 Owner")
        else:
            # If not an owner, check for staff
            for role_id in staff_roles_to_check:
                if any(r.id == role_id for r in member.roles):
                    member_is_staff_in_server = True
                    is_staff = True # Update the global flag for final footer
                    break
            if member_is_staff_in_server:
                status_lines.append("🛡️ Staff")

        # Only check for standard roles if not owner or staff in THIS server
        if not member_is_owner_in_server and not member_is_staff_in_server:
            verified_roles_found_in_server = []

            # Check for Paw Network Verified Role
            pnetwork_role_id = pnetwork_role_config.get("id")
            pnetwork_role_name = pnetwork_role_config.get("name")
            if pnetwork_role_id and any(r.id == pnetwork_role_id for r in member.roles):
                verified_roles_found_in_server.append(f"🐾 {pnetwork_role_name}")
                has_any_verified_role = True

            # Check for other standard verification roles
            for role_id, role_name in roles_to_check.items():
                if any(r.id == role_id for r in member.roles):
                    verified_roles_found_in_server.append(f"✅ {role_name}")
                    has_any_verified_role = True
            
            if verified_roles_found_in_server:
                status_lines.extend(verified_roles_found_in_server)
            else:
                status_lines.append("❌ No matching verification roles found.")

        # Always check for unverified roles
        found_unverified = []
        for role_id, role_name in unverified_roles_to_check.items():
            if any(r.id == role_id for r in member.roles):
                found_unverified.append(f"⚠️ {role_name}")
                has_any_unverified_role = True # Update global flag
        
        if found_unverified:
            status_lines.extend(found_unverified)
            
        embed.add_field(
            name=f"Status in {guild.name}",
            value="\n".join(status_lines),
            inline=False
        )

    # Set the final footer and color based on the overall verification status
    if is_banned_anywhere:
        embed.color = discord.Color.dark_red()
        embed.set_footer(text="BANNED")
    elif not all_servers_found:
        embed.color = discord.Color.red()
        embed.set_footer(text="Error: Bot is not in all configured servers.")
    elif is_owner:
        embed.color = discord.Color.gold()
        embed.set_footer(text="Owner")
    elif is_staff:
        embed.color = discord.Color.purple()
        embed.set_footer(text="Staff Verified")
    elif is_in_at_least_one_server and has_any_verified_role and not has_any_unverified_role:
        embed.color = discord.Color.green()
        embed.set_footer(text="Verified 18+")
    else:
        embed.color = discord.Color.orange()
        embed.set_footer(text="Unverified")
        
    # Send the final embed
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="createembed", description="Creates a server embed. (Owner only)")
@discord.app_commands.describe(
    server_name="The name of the server.",
    invite_link="The full invite link for the server.",
    owner_username="The username of the server owner."
)
async def createembed(interaction: discord.Interaction, server_name: str, invite_link: str, owner_username: str):
    """
    Generates a server advertisement embed. This command can only be used by the bot owner.
    """
    # --- Owner Check ---
    if not OWNER_ID or str(interaction.user.id) != OWNER_ID:
        await interaction.response.send_message(
            "Sorry, this command can only be used by the bot owner.", 
            ephemeral=True
        )
        return

    # --- Create Embed ---
    embed = discord.Embed(
        title=f"🐾 {server_name}",
        color=discord.Color.from_rgb(113, 13, 189) # A custom purple color
    )
    embed.add_field(name="🔗 Invite Link", value=invite_link, inline=False)
    embed.add_field(name="👑 Owner", value=owner_username, inline=False)
    embed.set_footer(text="Powered by Paw Network")

    # Send the embed to the channel where the command was used
    await interaction.response.send_message(embed=embed)


# --- PREFIX COMMANDS (Legacy Method) ---
@bot.command(name='hello', help='Responds with a friendly greeting.')
async def hello(ctx):
    """
    A simple prefix command. Users can type `!hello` to trigger this.
    """
    await ctx.send(f'Hello, {ctx.author.mention}!')


# --- RUN THE BOT ---
# This is the final line that runs the bot with your token.
if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: DISCORD_TOKEN not found in .env file.")
    print("Please follow the instructions in README.md to set up your bot token.")

