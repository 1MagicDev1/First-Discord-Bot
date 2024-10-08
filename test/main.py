from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents
from discord.ext import commands
from discord import app_commands
from discord import Streaming
import asyncio
from responses import get_response
from buildAndSend import startRetrieval_
from gameBuildAndSend import add_player, remove_player, update_leaderboard_, get_leaderboard
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
        asyncio.create_task(update_leaderboard_(bot))

    try:
        await bot.tree.sync()
        print("Synced commands.")
        await bot.change_presence(activity=Streaming(name="Streaming This", url="https://www.twitch.tv/ferretsoftware")) # CHANGE URL AND NAME
    except Exception as e:
        print(f"Error syncing commands: {e}")
        
# ---------------------------------------------------------------------------------------------

# STEP 3: Slash Command Definition
@bot.tree.command(name="here", description="Test with a Twitter link")
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
        print(f"Error in /here: {e}")
        await interaction.response.send_message("Something went wrong.")
        
# ---------------------------------------------------------------------------------------------

@bot.tree.command(name="dms", description="Send DMs based on a Twitter link")
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
        
# ---------------------------------------------------------------------------------------------

@bot.tree.command(name="add-player", description="Add Player To The Leaderboard For A Chosen Game")
@app_commands.describe(
    game="Select Game",
    player_name="Enter Player Name",
    player_tag="Enter Player Tag (DONT INCLUDE #)"
)
@app_commands.choices(game=[
    app_commands.Choice(name='League of Legends', value=1)
])
async def addPlayer(interaction, game: app_commands.Choice[int], player_name: str, player_tag: str):
    try:
        # Process the chosen game, player name, and player tag
        response = f"Adding {player_name}#{player_tag} to the {game.name} leaderboard."
        response = await add_player(bot, game.name, player_name, player_tag, interaction.guild.id)
        # Respond to the user with the result
        await interaction.response.send_message(response)
    except Exception as e:
        print(f"Error in /addplayer: {e}")
        await interaction.response.send_message("Something went wrong.")
        
# ---------------------------------------------------------------------------------------------
 
@bot.tree.command(name="remove-player", description="Remove Player From The Leaderboard For A Chosen Game")
@app_commands.describe(
    game="Select Game",
    player_name="Enter Player Name",
    player_tag="Enter Player Tag (DONT INCLUDE #)"
)
@app_commands.choices(game=[
    app_commands.Choice(name='League of Legends', value=1)
])       
async def removePlayer(interaction, game: app_commands.Choice[int], player_name: str, player_tag: str):
    try:
        # Process the chosen game, player name, and player tag
        response = f"Removing {player_name}#{player_tag} from the {game.name} leaderboard."
        response = await remove_player(bot, game.name, player_name, player_tag, interaction.guild.id)
        # Respond to the user with the result
        await interaction.response.send_message(response)
    except Exception as e:
        print(f"Error in /addplayer: {e}")
        await interaction.response.send_message("Something went wrong.")
        
# ---------------------------------------------------------------------------------------------

@bot.tree.command(name="leaderboard", description="View Leaderboard For Selected Game")
@app_commands.describe(game="Select Game")
@app_commands.choices(game=[
    app_commands.Choice(name='League of Legends', value=1)
])
async def getleaderboard(interaction, game: app_commands.Choice[int]):
    try:
        result = await get_leaderboard(bot, game.name, interaction.guild.id)
        
        if isinstance(result, tuple):  # Multiple pages (embed, view)
            embed, view = result
            await interaction.response.send_message(embed=embed, view=view)
        else:  # Single page (only embed)
            embed = result
            await interaction.response.send_message(embed=embed)

    except Exception as e:
        print(f"Error in /leaderboard: {e}")
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