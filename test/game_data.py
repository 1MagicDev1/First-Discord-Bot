from typing import Dict, List
from json import loads, dumps

class Server:
    def __init__(self):
        self.games: Dict[str, Game] = {}

class Game:
    def __init__(self):
        self.players: Dict[str, List[str]] = {}  # Store rank and division as list [rank, division]

class GameData:
    def __init__(self):
        self.servers: Dict[int, Server] = {}  # Use server IDs as keys, just like in data.py
    
    def read(self):
        try:
            with open('game_data.json', 'r') as f:
                read = f.read().strip()
                self.parse(loads(read))
        except FileNotFoundError:
            print('game_data.json doesn\'t exist, creating one...')
            self.write()
        except Exception as e:
            print(f'Unknown error:', e)
    
    def parse(self, obj):
        for server_id, games in obj.items():
            server = Server()
            for game_name, players in games.items():
                game = Game()
                for player, rank_data in players.items():
                    game.players[player] = rank_data  # rank_data is a list [rank, division]
                server.games[game_name] = game
            self.servers[int(server_id)] = server  # Ensure server ID is added as a key
    
    def write(self):
        try:
            with open('game_data.json', 'w') as f:
                obj = {}
                for server_id, server in self.servers.items():
                    obj[server_id] = {}
                    for game_name, game in server.games.items():
                        obj[server_id][game_name] = game.players
                f.write(dumps(obj, indent=2))
        except Exception as e:
            print(f'Unknown error:', e)

    # Add a method to ensure server creation if it doesn't exist
    def ensure_server(self, server_id: int):
        if server_id not in self.servers:
            self.servers[server_id] = Server()

