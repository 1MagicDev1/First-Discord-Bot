from typing import Dict, List
from json import loads, dumps


class Account:
    def __init__(self):
        self.active: bool
        self.type: str           # x = twitter, i = insta, t = twitch
        self.username: str
        self.counter: int = 0
        self.channel: int = 0    # optional #1 (one or the other)
        self.dms: List[int] = [] # optional #2
        self.phosts: List[str] = []


class Server:
    def __init__(self):
        self.active: bool = False
        self.accounts: List[Account] = []


class Data:
    def __init__(self):
        self.servers: Dict[int, Server] = {}
    
    
    def read(self):
        try:
            with open('data.json', 'r') as f:
                read = f.read().strip()
                # print(f'data.json read: `{read}`')
                self.parse(loads(read))
        except FileNotFoundError:
            print('data.json file doesn\'t exist, creating one...')
            self.write()
        except Exception as e:
            print(f'Unknown error:', e)
    
    
    def parse(self, obj):
        for server_id, val in obj.items():
            server = Server()
            # print(f'New server found, id: {server_id}, server ref: {server}, server account len: {len(server.accounts)}')
            for k, value in val.items():
                if k == 'active':
                    server.active = bool(value)
                    # print(f'\tServer active: {server.active}, server ref: {server}')
                elif '@' in k:
                    account = Account()
                    # print(f'New account, account ref: {account}')
                    split = k.split('@')
                    account.type = split[0]
                    account.username = split[1]
                    # print(f'\tFound user {account.type}@{account.username}, account ref: {account}, server ref: {server}')
                    for kk, value2 in value.items():
                        # print(f'\t\t{kk} = {value2}, account ref: {account}, server ref: {server}')
                        if kk == 'active':
                            account.active = bool(value2)
                        elif kk == 'counter':
                            account.counter = int(value2)
                        elif kk == 'channel':
                            account.channel = int(value2)
                        elif kk == 'dms':
                            account.dms = value2
                        elif kk == 'phosts':
                            account.phosts = value2
                    # print(f'\tAdding account ref {account} to server ref: {server}')
                    server.accounts.append(account)
                else:
                    print(f'\tUnknown: {k} = {value}, account ref: {account}, server ref: {server}')
            
            # print(f'\tAdding server {server_id}, server ref: {server}')
            self.servers[int(server_id)] = server
    
    
    def write(self):
        try:
            with open('data.json', 'w') as f:
                obj = {}
                for server_id, value in self.servers.items():
                    obj2 = {
                        'active': value.active
                    }
                    for account in value.accounts:
                        obj3 = {
                            'active': account.active,
                            'counter': account.counter,
                            'channel': account.channel,
                            'dms': account.dms,
                            'phosts': account.phosts
                        }
                        obj2[f'{account.type}@{account.username}'] = obj3
                    obj[server_id] = obj2
                f.write(dumps(obj, indent=2))
        except Exception as e:
            print(f'Unknown error:', e)