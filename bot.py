# main.py
import os
import json
import discord
import aiohttp
from discord.ext import commands
from dotenv import load_dotenv

# --- BOT SETUP ---
# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OWNER_ID_STR = os.getenv('OWNER_ID')
CONFIG_URL = os.getenv('CONFIG_URL')

# It's recommended to define intents for your bot.
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # <-- IMPORTANT: This is required to get member information reliably.

# Create a bot instance with a command prefix and the defined intents
bot = commands.Bot(command_prefix='!', intents=intents)

# --- CONFIGURATION ---
SERVER_CONFIG = {}

async def load_config():
    """Loads server configuration from a GitHub raw URL and converts role IDs to integers."""
    if not CONFIG_URL:
        print("Error: CONFIG_URL not found in .env file. Cannot load configuration.")
        return None

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(CONFIG_URL) as response:
                if response.status == 200:
                    # Fix: Tell aiohttp to parse as JSON regardless of the mimetype
                    config = await response.json(content_type=None)
                    # Discord.py requires integer IDs, but JSON keys are strings.
                    # We need to convert them.
                    for server_key, server_data in config.items():
                        for role_group_key, role_group_data in server_data.items():
                            if isinstance(role_group_data, dict) and "id" not in role_group_data:
                                config[server_key][role_group_key] = {int(k): v for k, v in role_group_data.items()}
                    print("Successfully loaded configuration from GitHub.")
                    return config
                else:
                    print(f"Error: Failed to fetch config from GitHub. Status: {response.status}")
                    return None
    except aiohttp.ClientError as e:
        print(f"Error: AIOHTTP client error while fetching config: {e}")
        return None
    except json.JSONDecodeError:
        print("Error: Fetched config file from GitHub is not valid JSON.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading config from GitHub: {e}")
        return None


# --- OWNER CHECK ---
# A check function to see if the command user is the bot owner
def is_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not OWNER_ID_STR:
            await interaction.response.send_message("Owner ID is not set in the `.env` file.", ephemeral=True)
            return False
        try:
            owner_id = int(OWNER_ID_STR)
            if interaction.user.id == owner_id:
                return True
            else:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return False
        except ValueError:
            await interaction.response.send_message("The `OWNER_ID` in the `.env` file is not a valid user ID.", ephemeral=True)
            return False
    return discord.app_commands.check(predicate)

# --- EVENTS ---
@bot.event
async def on_ready():
    """
    This event is triggered when the bot has successfully connected to Discord.
    """
    global SERVER_CONFIG
    SERVER_CONFIG = await load_config()

    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    if not SERVER_CONFIG:
        print('Warning: Server configuration could not be loaded. The bot may not function as expected.')
    else:
        print(f'Loaded configuration for {len(SERVER_CONFIG)} server(s).')

    # Set the bot's presence/activity
    activity = discord.Game(name="Checking IDs")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    print('Bot is ready and online!')
    try:
        # Sync the slash commands to the command tree
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# --- SLASH COMMANDS ---
@bot.tree.command(name="ping", description="Replies with the bot's latency.")
async def ping(interaction: discord.Interaction):
    """
    A simple slash command that replies with the bot's latency in milliseconds.
    """
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'Pong! Latency: {latency}ms')

@bot.tree.command(name="reloadconfig", description="Reloads the server configuration from the GitHub URL.")
@is_owner()
async def reloadconfig(interaction: discord.Interaction):
    """
    Refetches and reloads the config.json from the GitHub URL.
    """
    await interaction.response.defer(ephemeral=True)
    global SERVER_CONFIG
    new_config = await load_config()
    if new_config is not None:
        SERVER_CONFIG = new_config
        await interaction.followup.send(f"✅ Successfully reloaded configuration for {len(SERVER_CONFIG)} server(s).")
    else:
        await interaction.followup.send("❌ Failed to reload configuration. Check the console for errors. The old configuration remains active.")


@bot.tree.command(name="checkroles", description="Checks a user's verification roles in configured servers.")
@discord.app_commands.describe(user="The user you want to check.")
async def checkroles(interaction: discord.Interaction, user: discord.User):
    """
    Checks roles and ban status for a user across all servers defined in the live config.
    """
    await interaction.response.defer()

    embed = discord.Embed(
        title=f"Role Verification for {user.name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    if not SERVER_CONFIG:
        embed.description = "⚠️ The server configuration is currently unavailable. Please try again later."
        embed.color = discord.Color.red()
        await interaction.followup.send(embed=embed)
        return

    is_banned_anywhere = False
    is_owner = False
    is_staff = False
    has_any_verified_role = False
    has_any_unverified_role = False
    is_in_at_least_one_server = False
    all_servers_found = True

    for server_key, config in SERVER_CONFIG.items():
        server_id = config["id"]
        server_name = config["name"]

        guild = bot.get_guild(server_id)
        if not guild:
            embed.add_field(
                name=f"❌ Server Not Found: {server_name}",
                value=f"I am not a member of this server.",
                inline=False
            )
            all_servers_found = False
            continue

        status_lines = []

        # --- Ban Check ---
        try:
            await guild.fetch_ban(user)
            # If the above line doesn't raise an error, the user is banned.
            status_lines.append("🚫 **BANNED**")
            is_banned_anywhere = True
            embed.add_field(name=f"Status in {guild.name}", value="\n".join(status_lines), inline=False)
            continue # Skip other checks for this server if banned
        except discord.NotFound:
            # User is not banned, proceed with other checks.
            pass
        except discord.Forbidden:
            status_lines.append("⚠️ Permission Error: I don't have permission to view the ban list.")
        except Exception as e:
            status_lines.append(f"⚠️ An error occurred during ban check: {e}")

        member = guild.get_member(user.id)
        if not member:
            try:
                member = await guild.fetch_member(user.id)
            except discord.NotFound:
                member = None

        if not member:
            embed.add_field(
                name=f"Status in {guild.name}",
                value=f"User is not a member of this server.",
                inline=False
            )
            continue

        is_in_at_least_one_server = True

        member_is_owner_in_server = False
        member_is_staff_in_server = False

        # Check for Owner roles
        for role_id in config.get("owner_roles", {}):
            if any(r.id == role_id for r in member.roles):
                member_is_owner_in_server = True
                is_owner = True
                break

        if member_is_owner_in_server:
            status_lines.append("👑 Owner")
        else:
            # If not owner, check for staff
            for role_id in config.get("staff_roles", {}):
                if any(r.id == role_id for r in member.roles):
                    member_is_staff_in_server = True
                    is_staff = True
                    break
            if member_is_staff_in_server:
                status_lines.append("🛡️ Staff")

        # Check for standard roles if not owner or staff in this server
        if not member_is_owner_in_server and not member_is_staff_in_server:
            verified_roles_found = []

            pnetwork_role_config = config.get("pnetwork_verified_role", {})
            pnetwork_role_id = pnetwork_role_config.get("id")
            if pnetwork_role_id and any(r.id == pnetwork_role_id for r in member.roles):
                verified_roles_found.append(f"🐾 {pnetwork_role_config.get('name', 'Paw Network Verified')}")
                has_any_verified_role = True

            for role_id, role_name in config.get("roles_to_check", {}).items():
                if any(r.id == role_id for r in member.roles):
                    verified_roles_found.append(f"✅ {role_name}")
                    has_any_verified_role = True

            if verified_roles_found:
                status_lines.extend(verified_roles_found)
            else:
                status_lines.append("❌ No matching verification roles found.")

        # Always check for unverified roles
        unverified_found = []
        for role_id, role_name in config.get("unverified_roles", {}).items():
            if any(r.id == role_id for r in member.roles):
                unverified_found.append(f"⚠️ {role_name}")
                has_any_unverified_role = True

        if unverified_found:
            status_lines.extend(unverified_found)

        embed.add_field(
            name=f"Status in {guild.name}",
            value="\n".join(status_lines) if status_lines else "No relevant status found.",
            inline=False
        )

    # Set final footer and color
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

    await interaction.followup.send(embed=embed)


@bot.tree.command(name="createembed", description="Creates a server advertisement embed.")
@is_owner()
@discord.app_commands.describe(
    server_name="The name of the server.",
    invite_link="The permanent invite link for the server.",
    owner_username="The Discord username of the server owner."
)
async def createembed(interaction: discord.Interaction, server_name: str, invite_link: str, owner_username: str):
    """
    Generates a clean embed for advertising a server. Only usable by the bot owner.
    """
    embed = discord.Embed(
        title=f"Partner Spotlight: {server_name}",
        color=discord.Color.from_rgb(113, 104, 226) # A nice purple color
    )
    embed.add_field(name="Owner", value=owner_username, inline=True)
    embed.add_field(name="Invite Link", value=f"[Click Here to Join!]({invite_link})", inline=True)
    embed.set_footer(text="Paw Network Partner")

    await interaction.response.send_message(embed=embed)


# --- RUN THE BOT ---
if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN not found in .env file.")


