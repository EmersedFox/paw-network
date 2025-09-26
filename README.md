🐾 Paw Network Discord Bot

Paw Network is a custom Discord bot designed to facilitate cross-server user verification. It can check for specific roles, staff/owner status, and ban status across multiple configured Discord servers, providing a comprehensive verification summary in a clean embed.
Features

    Cross-Server Verification: Checks user roles across any number of configured servers.

    Hierarchical Status: Prioritizes user status in the following order:

        Banned: The highest priority status.

        Owner: Recognizes server owners.

        Staff: Recognizes staff members.

        Verified: Confirms a user has valid verification roles.

        Unverified: Flags users who are unverified or have negative roles.

    Custom Role Recognition: Specifically highlights a "Paw Network Verified" role.

    Ban Check: Actively checks if a user is banned in any of the participating servers.

    Owner-Only Commands: Includes secure commands that can only be used by the designated bot owner.

    Custom Bot Status: Sets a "Playing Checking IDs" status on Discord.

Setup Instructions

Follow these steps carefully to get your bot up and running.
Step 1: Create Your Bot on the Discord Developer Portal

    Go to the Developer Portal: Navigate to the Discord Developer Portal.

    New Application: Click "New Application" and give your bot a name (e.g., "Paw Network").

    Go to the "Bot" Tab: On the left menu, select the "Bot" tab.

    Get Your Token: Click "Reset Token" and copy the token that appears. Treat this like a password and never share it.

    Enable Privileged Intents: Scroll down to "Privileged Gateway Intents" and enable ALL THREE intents:

        PRESENCE INTENT

        SERVER MEMBERS INTENT (Crucial for checking roles)

        MESSAGE CONTENT INTENT

Step 2: Configure Your .env File

The .env file stores your secret keys. Create a file named .env in the same directory as bot.py and add the following lines, replacing the placeholder values with your own.

DISCORD_TOKEN="YOUR_BOT_TOKEN_HERE"
OWNER_ID="YOUR_DISCORD_USER_ID_HERE"

    DISCORD_TOKEN: The token you copied in Step 1.

    OWNER_ID: Your personal Discord User ID. To get this, enable Developer Mode in Discord settings (Advanced), then right-click your profile and select "Copy User ID".

Step 3: Configure Servers in bot.py

Open bot.py and edit the SERVER_CONFIG dictionary to add, remove, or modify the servers and roles you want the bot to track. The structure is straightforward and can be easily expanded.
Step 4: Install Dependencies

You need to install the Python libraries the bot depends on. Open your terminal or command prompt in the bot's folder and run:

pip install -r requirements.txt

Step 5: Invite Your Bot to Your Servers

You must invite the bot to every server listed in your SERVER_CONFIG.

    Go to OAuth2 URL Generator: In the Developer Portal, go to the "OAuth2" tab and then "URL Generator".

    Select Scopes: Check bot and applications.commands.

    Select Bot Permissions: Check the following permissions:

        Read Messages/View Channels

        Send Messages

        Embed Links

        Ban Members (Required for the ban check feature)

    Copy and Use the URL: Copy the generated URL at the bottom and paste it into your browser to invite the bot to each of your servers.

Step 6: Run the Bot

Once everything is configured, run the bot from your terminal:

python bot.py

Commands Guide

    /checkroles [user]

        This is the main command. It fetches the roles and status of a specified user across all configured servers.

        The user can be specified by their @username or User ID.

        The final status in the footer will be determined by their highest-priority role across all servers.

    /createembed [server_name] [invite_link] [owner_username]

        Owner-only. This command generates a clean, formatted embed for advertising a server.

        This command will fail if your OWNER_ID is not set correctly in the .env file.

    /ping

        A simple utility command to check if the bot is online and responsive. It replies with its current latency.

Troubleshooting

    Slash Commands Not Appearing? It can take Discord up to an hour to register new slash commands. If they don't appear, try re-inviting the bot to your server using a fresh URL from the OAuth2 URL Generator (Step 5). Ensure both bot and applications.commands scopes are checked.

    "Permission Error in [Server Name]"? If you see a message that the bot can't view the ban list, it means the bot does not have the "Ban Members" permission in that server's roles.

    Bot Not Finding a Server? Ensure the server ID in your SERVER_CONFIG is correct and that you have successfully invited the bot to that server.
