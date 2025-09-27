# Paw Network Discord Bot

Paw Network is a specialized Discord bot designed to facilitate cross-server verification and moderation. It allows staff to check a user's roles, ban status, and special permissions across a network of configured Discord servers, all managed through a live configuration file hosted on GitHub.
Features

    Cross-Server Verification: Check a user's roles in multiple servers from a single command.

    Live Configuration: Update the list of servers and roles by editing a JSON file on GitHub, with no need to restart the bot.

    Priority Status Checks: Automatically identifies and prioritizes statuses like Banned, Owner, and Staff over standard verification roles.

    Network Management: Includes owner-only commands to view network-wide statistics and reload the configuration on the fly.

    Secure & Permission-Based: Owner-only commands are restricted to a specific user ID for security.

Setup Instructions

Follow these steps to get your instance of the Paw Network bot running.
Prerequisites

    Python 3.8+

    A Discord Account with permissions to create applications.

    A GitHub Account to host the configuration file.

Step 1: Get the Bot Code

You will need to have the bot's files (bot.py, requirements.txt, .env) in a folder on your computer or server.
Step 2: Create the Discord Bot Application

    Go to the Developer Portal: Navigate to the Discord Developer Portal.

    New Application: Create a new application and give it a name (e.g., "Paw Network").

    Go to the Bot Tab: Click on the "Bot" tab on the left.

    Enable Privileged Intents:

        Scroll down to Privileged Gateway Intents.

        Enable the SERVER MEMBERS INTENT. This is critical for the bot to find users and check their roles.

    Get Your Bot Token: Click "Reset Token" to reveal and copy your bot's token. This is a secret key.

Step 3: Set Up the Configuration File on GitHub

The bot loads its server list from a server.json file you host on GitHub.

    Create a Public GitHub Repository: Create a new public repository on GitHub (e.g., Paw-Network-Config).

    Create server.json: Inside this repository, create a new file named server.json.

    Add Your Server Data: Copy the structure below into server.json and fill it with your server details. All keys, including the role IDs, must be in double quotes.

    {
        "server_one_key": {
            "id": 1333237935268561017,
            "name": "Emersed Den",
            "pnetwork_verified_role": { "id": 1421184692706607225, "name": "Paw Network Verified" },
            "roles_to_check": { "1333248688738406453": "Manually Age Verified" },
            "unverified_roles": { "1405276168202096646": "Unverified" },
            "owner_roles": { "1333238516204830772": "Owner" },
            "staff_roles": { "1414622599819821088": "Staff" }
        },
        "another_server_key": {
            "id": 1303588446132109342,
            "name": "NeoCity",
            "roles_to_check": { "1303758361904414750": "Verified Adult" }
        }
    }

    Get the Raw URL:

        Once the file is saved, view it on GitHub and click the "Raw" button.

        Copy the URL from your browser's address bar. This is your permanent config URL.

Step 4: Set Up Your .env File

In the same folder as bot.py, create a file named .env and add the following, filling in your own values:

DISCORD_TOKEN="YOUR_BOT_TOKEN_HERE"
OWNER_ID="YOUR_DISCORD_USER_ID_HERE"
CONFIG_URL="YOUR_GITHUB_RAW_JSON_URL_HERE"

Step 5: Install Dependencies

Open your terminal or command prompt in the bot's folder and run:

pip install -r requirements.txt

Step 6: Invite the Bot and Run It

    Invite the Bot: In the Discord Developer Portal, go to OAuth2 -> URL Generator. Select the bot and applications.commands scopes. Then, grant it the following Bot Permissions:

        Read Messages/View Channels

        Send Messages

        Embed Links

        Ban Members (Required for the ban check)

        Copy the generated URL and use it to invite the bot to all servers listed in your config.

    Run the Bot: Open your terminal in the bot's folder and run the script:

    python bot.py

Command Usage
Public Commands

    /checkroles [user]

        Checks a specified user's roles, ban status, and permissions across all configured servers.

        Displays a detailed embed showing the user's status in each server.

Owner-Only Commands

    /reloadconfig

        Forces the bot to re-download and load the server.json file from GitHub. Use this after you've updated your server list.

    /networkstats

        Displays an embed with a list of all configured servers, their online status, and current member counts.

    /createembed [server_name] [invite_link] [owner_username]

        Generates a formatted partner embed, which can be used for server advertisements.

Troubleshooting

    Slash Commands Not Appearing?

        This usually means the bot was invited without the applications.commands scope. Re-invite the bot using a newly generated URL with the correct scopes checked. It can take Discord a few minutes to register new commands.

    "Permission Error: I don't have permission to view the ban list."

        In the server where this error appears, go to Server Settings -> Roles. Find the bot's role and ensure it has the "Ban Members" permission enabled.

    "Fetched config file... is not valid JSON."

        Your server.json file has a syntax error. Use an online JSON validator to find and fix issues like missing quotes on keys or trailing commas.
