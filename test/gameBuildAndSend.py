import asyncio
import requests
import discord
from discord.ui import Button, View
from game_data import GameData, Game
from datetime import datetime

class LeaderboardView(View):
    def __init__(self, pages):
        super().__init__(timeout=60)  # Timeout in seconds
        self.pages = pages
        self.current_page = 0
        # Disable the 'Previous' button at the beginning
        self.previous_button.disabled = True
        # Disable 'Next' if there is only one page
        self.next_button.disabled = len(self.pages) == 1

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: Button):
        self.current_page -= 1
        # Disable 'Previous' if on the first page
        if self.current_page == 0:
            button.disabled = True
        # Enable 'Next' as we are moving backwards
        self.next_button.disabled = False
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        self.current_page += 1
        # Disable 'Next' if on the last page
        if self.current_page == len(self.pages) - 1:
            button.disabled = True
        # Enable 'Previous' as we are moving forward
        self.previous_button.disabled = False
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

def search_player(game_name, player_name, player_tag):
    game_name = game_name.replace(" ", "")
    print(f"Game: {game_name}\nPlayer Name: {player_name}#{player_tag}")
    if game_name == 'LeagueofLegends':
        api_key = 'YOUR RIOT API KEY'
        api_url = f'https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{player_name}/{player_tag}?api_key={api_key}'

        resp = requests.get(api_url)
        account_data = resp.json()

        # Check if the player exists
        if 'puuid' not in account_data:
            return None, 'invalid'  # Explicitly return None for rank and 'invalid' for division

        # Retrieve summoner details
        puuid = account_data['puuid']
        summoner_url = f'https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={api_key}'
        summoner_resp = requests.get(summoner_url)
        summoner_data = summoner_resp.json()

        # If no summoner ID, return invalid
        if 'id' not in summoner_data:
            return None, 'invalid'

        summonerID = summoner_data['id']
        rank_url = f'https://EUW1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summonerID}?api_key={api_key}'
        rank_resp = requests.get(rank_url)
        player = rank_resp.json()

        # Handle the rank data if available
        try:
            player_rank = player[0]['tier']
            player_division = player[0]['rank']
            return player_rank, player_division  # Return valid rank and division
        except (IndexError, KeyError):
            return 'unranked', 'unranked'  # Handle if player has no rank

    return None, 'invalid'  # For unsupported games or other errors

def get_points(rank, division):
    total = 0
    match rank:
        case "IRON":
            total += 90
        case "BRONZE":
            total += 80
        case "SILVER":
            total += 70
        case "GOLD":
            total += 60
        case "PLATINUM":
            total += 50
        case "EMERALD":
            total += 40
        case "DIAMOND":
            total += 30
        case "MASTER":
            total += 20
        case "GRANDMASTER":
            total += 10
        case "CHALLENGER":
            total += 0
    
    match division:
        case "IV":
            total += 4
        case "III":
            total += 3
        case "II":
            total += 2
        case "I":
            total += 1
    
    return total

async def update_leaderboard_(client: discord.Client):
    # Load game data
    gamedata = GameData()
    gamedata.read()

    while True:
        data_updated = False  # Track if data has been updated
        # Loop through all servers in the game data
        for server_id, server in gamedata.servers.items():
            for game_name, game in server.games.items():
                print("\n--------STARTING UPDATE--------\n")
                players = list(game.players.keys())
                # Break the players into chunks of 20
                for i in range(0, len(players), 20):
                    batch = players[i:i + 20]
                    tasks = []

                    # Process each batch of 20 players
                    for player_name in batch:
                        player_name_split = player_name.split('#')
                        player_name = player_name_split[0]
                        player_tag = player_name_split[1]
                        tasks.append(update_player_rank(client, server_id, game_name, player_name, player_tag))

                    # Run tasks concurrently
                    print(f"Processing {len(tasks)} tasks in batch")
                    await asyncio.gather(*tasks)
                    print("Updated Players in current batch")
                    
                    # Mark that data was updated in this batch
                    if tasks:
                        data_updated = True  # Mark data as updated if players were processed
                    
                    # Sleep for 60 seconds before processing the next batch
                    await asyncio.sleep(60)

        # Save the updated game data after processing all servers
        if data_updated:
            print("Writing updated data to game_data.json")
            gamedata.read()  # Re-read the JSON file to ensure you're working with up-to-date data
            gamedata.write()

        # Add a delay to prevent constant looping of the entire process
        await asyncio.sleep(60)


async def update_player_rank(client: discord.Client, server_id: int, game_name: str, player_name: str, player_tag: str):
    # Fetch player rank and division from the API
    invalid = False
    full_name = player_name + '#' + player_tag
    print(f"SEARCHING PLAYER: {full_name} in game {game_name}")

    player_rank, player_division = search_player(game_name, player_name, player_tag)
    
    # Check if the player is invalid or unranked
    if player_division in ['invalid', 'unranked']:
        print(f"FAILED TO UPDATE: {full_name} is invalid or unranked.")
        invalid = True

    # Load and update game data
    gamedata = GameData()
    gamedata.read()

    # Ensure the server exists in game_data.json
    gamedata.ensure_server(server_id)

    # Access the server data
    server = gamedata.servers[server_id]
    
    game_name_spaceless = game_name.replace(" ", "")
    
    if game_name_spaceless in server.games:
        current_game = server.games[game_name_spaceless]
        
        # Log the current state before modification
        print(f"Before update: {current_game.players}")
        
        if full_name in current_game.players:
            if invalid:
                print(f"Removing {full_name} from leaderboard due to invalid/unranked status.")
                current_game.players.pop(full_name)  # Remove invalid/unranked players
            else:
                print(f"Updating {full_name}'s rank to {player_rank} {player_division}.")
                current_game.players[full_name] = [player_rank, player_division]  # Update valid players
        else:
            print(f"Player {full_name} not found in the leaderboard.")
    
    # Log the state after modification
    print(f"After update: {current_game.players}")

    # Save the updated game data
    gamedata.write()

async def add_player(client: discord.Client, game_name, player_name, player_tag, server_id: int):
    # Fetch player rank and division from the API
    player_rank, player_division = search_player(game_name, player_name, player_tag)
    
    if player_division == 'invalid':
        print(f"Player {player_name}#{player_tag} does not exist...")
        return "This player does not exist..."
    elif player_division == 'unranked':
        print(f"Player {player_name}#{player_tag} is unranked.")
        return "This player is unranked...."

    # Load and update game data
    gamedata = GameData()
    gamedata.read()
    
    print(f"Before add_player: {gamedata.servers}")

    # Ensure the server exists in game_data.json
    gamedata.ensure_server(server_id)

    # Access the server data
    server = gamedata.servers[server_id]

    # Check if the game exists for the server, and if not, create it
    game_name_spaceless = game_name.replace(" ", "")
    if game_name_spaceless not in server.games:
        server.games[game_name_spaceless] = Game()

    current_game = server.games[game_name_spaceless]
    
    full_player_name = player_name + '#' + player_tag
    
    # Add or update the player's rank and division
    if full_player_name not in current_game.players:
        current_game.players[full_player_name] = [player_rank, player_division]
        print(f"Added {full_player_name} with rank {player_rank} {player_division}")
    else:
        print(f"Player {full_player_name} already exists with rank {current_game.players[full_player_name]}")
        return "This Player Is Already Stored For This Game, Do /leaderboard To Check Their Standings!"
    
    # Log the updated data before writing to the file
    print(f"After add_player: {gamedata.servers}")
    
    # Save the updated game data
    gamedata.write()
    
    return f"Added {player_name} to {game_name} with the rank: {player_rank} {player_division}"

async def remove_player(client: discord.Client, game_name, player_name, player_tag, server_id: int):

    # Load and update game data
    gamedata = GameData()
    gamedata.read()

    # Ensure the server exists in game_data.json
    gamedata.ensure_server(server_id)

    # Access the server data
    server = gamedata.servers[server_id]

    # Check if the game exists for the server, and if not, create it
    game_name_spaceless = game_name.replace(" ", "")
    if game_name_spaceless not in server.games:
        server.games[game_name_spaceless] = Game()

    current_game = server.games[game_name_spaceless]
    
    full_player_name = player_name + '#' + player_tag
    
    # Add or update the player's rank and division
    if full_player_name not in current_game.players:
        return "This Player Is Not Stored In The Leaderboard..."
    else:
        current_game.players.pop(full_player_name)

    # Save the updated game data
    gamedata.write()
    
    return f"Removed Player: {player_name}#{player_tag}"

async def get_leaderboard(client: discord.Client, game_name, server_id: int):
    gamedata = GameData()
    gamedata.read()

    # Ensure the server exists in game_data.json
    gamedata.ensure_server(server_id)

    # Access the server data
    server = gamedata.servers[server_id]
    
    # Check if the game exists for the server
    game_name_spaceless = game_name.replace(" ", "")
    if game_name_spaceless not in server.games:
        server.games[game_name_spaceless] = Game()

    current_game = server.games[game_name_spaceless]
    all_players = []

    players = list(current_game.players.keys())
    
    if len(players) > 0:
        for player in players:
            player_data = current_game.players[player]
            if isinstance(player_data, list) and len(player_data) == 2:
                rank = player_data[0]
                division = player_data[1]
                points = get_points(rank, division)
                all_players.append([player, points])

        # Sort players by points (from highest to lowest)
        sorted_players = sorted(all_players, key=lambda x: x[1])

        # Divide the players into chunks of 10 for each page
        pages = []
        for i in range(0, len(sorted_players), 10):
            leaderboard_of_players = ""
            leaderboard_of_ranks = ""
            for j, profile in enumerate(sorted_players[i:i + 10], 1):
                leaderboard_of_players += f"{i + j}. {profile[0]}\n"
                leaderboard_of_ranks += f"{i + j}. {current_game.players[profile[0]][0]} {current_game.players[profile[0]][1]}\n"

            embed = discord.Embed(
                title="League of Legends Leaderboard",
                description="A leaderboard for all of our server's League players!",
                colour=0xFFD700,
                timestamp=datetime.now()
            )
            embed.add_field(name="PLAYERS", value=leaderboard_of_players, inline=True)
            embed.add_field(name="", value="", inline=True)
            embed.add_field(name="RANKS", value=leaderboard_of_ranks, inline=True)
            embed.add_field(name="Add yourself to this leaderboard using /add-player!", value="GOOD LUCK GAMERS", inline=False)
            embed.set_thumbnail(url="https://i.scdn.co/image/ab67616100005174e80d1ffb81aa6503ad41c574")
            embed.set_footer(text="BU Esports Bot", icon_url="https://www.subu.org.uk/asset/Organisation/6423/BU%20BARRACUDAS.jpg?thumbnail_width=250&thumbnail_height=250&resize_type=CropToFit")

            pages.append(embed)

        # If there are multiple pages, return both the first embed and the view for buttons
        if len(pages) > 1:
            view = LeaderboardView(pages)
            return pages[0], view  # Return both embed and view for pagination
        else:
            return pages[0]  # If only one page, return the embed

    # If there are no players, return an empty leaderboard embed
    embed = discord.Embed(
        title="League of Legends Leaderboard",
        description="A leaderboard for all of our server's League players!",
        colour=0x00b0f4,
        timestamp=datetime.now()
    )
    embed.add_field(name="There are 0 players in the leaderboard currently...", value="", inline=False)
    embed.add_field(name="", value="Add yourself to this leaderboard using /add-player!", inline=True)
    embed.set_thumbnail(url="https://i.scdn.co/image/ab67616100005174e80d1ffb81aa6503ad41c574")
    embed.set_footer(text="BU Esports Bot", icon_url="https://www.subu.org.uk/asset/Organisation/6423/BU%20BARRACUDAS.jpg?thumbnail_width=250&thumbnail_height=250&resize_type=CropToFit")
    
    return embed