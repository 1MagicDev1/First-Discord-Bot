from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents
from discord.ext import commands
from discord import app_commands
import asyncio
from responses import get_response
from buildAndSend import startRetrieval_
from sharedVars import Shared

# Initialize data.json
Shared.data.read()

# Load Token
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# STEP 1: Bot Setup
intents: Intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Global Variables
isRetrieving = False

# STEP 2: Handling The Startup For Bot
@bot.event
async def on_ready():
    global isRetrieving
    print(f'{bot.user} is now running! (MEOW)')
    if not isRetrieving:
        isRetrieving = True
        asyncio.create_task(startRetrieval_(bot))

    try:
        await bot.tree.sync()
        print("Synced commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# STEP 3: Slash Command Definition
@bot.tree.command(name="testhere", description="Test with a Twitter link")
@app_commands.describe(twitter_link="Provide a Twitter link")
async def testhere(interaction, twitter_link: str):
    try:
        guild_id = interaction.guild.id if interaction.guild else None
        channel_id = interaction.channel.id
        author_id = interaction.user.id
        public = True
        
        response = get_response(twitter_link, interaction.user, guild_id, channel_id, author_id, public)
        if response:
            await interaction.response.send_message(response)
    except Exception as e:
        print(f"Error in /testhere: {e}")
        await interaction.response.send_message("Something went wrong.")

@bot.tree.command(name="testdms", description="Send DMs based on a Twitter link")
@app_commands.describe(twitter_link="Provide a Twitter link")
async def dms(interaction, twitter_link: str):
    try:
        guild_id = interaction.guild.id if interaction.guild else None
        channel_id = interaction.channel.id
        author_id = interaction.user.id
        public = False
        
        response = get_response(twitter_link, interaction.user, guild_id, channel_id, author_id, public)
        if response:
            await interaction.user.send(response)  # Send the response as a DM
    except Exception as e:
        print(f"Error in /dms: {e}")
        await interaction.response.send_message("Something went wrong.")

# STEP 4: Handling messages (if needed for additional non-slash command functionality)
@bot.event
async def on_message(message):
    # Optionally handle messages here if needed
    pass

# STEP 5: Main Entry Point
async def main():
    await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())