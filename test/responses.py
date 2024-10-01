from discord import Message
from random import choice, randint
from discord import Message, Client
from sharedVars import Shared
from data import Account, Server
from typing import List


def trimMessage(msg: str) -> str:
    if msg.startswith('https://'):
        msg = msg[8:]
    if msg.startswith('www.'):
        msg = msg[4:]
    return msg

def extractCommand(msg: str):
    print(f'IN FUNCTION: {msg}')
    if 'twitter.com/' in msg:
        username = msg[12:]
        atype = 'x'
        message = f'Sending posts from the {username} X account'
    elif 'x.com/' in msg:
        username = msg[6:]
        atype = 'x'
        message = f'Sending posts from the {username} X account'
    elif 'instagram.com/' in msg:
        username = msg[14:]
        atype = 'i'
        message = f'Sending posts from the {username} Insta account'
    elif 'twitch.tv/' in msg:
        username = msg[10:]
        atype = 't'
        message = f'Sending posts from the {username} Twitch account'
    else:
        message = 'pls do /testhere [link]'
        return False, '', '', message
    return True, username, atype, message



def get_response(msg, user, guild_id: int, channel_id: int, author_id: int, public) -> tuple:
    
    # if user_input.startswith('testhere x@magic'):
    #     if not message.author.guild_permissions.administrator:
    #         return "You don't have permission to do that."
    
    print(f"User: {user}, Guild ID: {guild_id}, Channel ID: {channel_id}, Author ID: {author_id}")
    print(f'BEFORE TRIM: {msg}')
    
    accounts: List[Account]
    if guild_id not in Shared.data.servers:
        server = Server()
        server.active = True
        accounts = server.accounts = []
        Shared.data.servers[guild_id] = server
    else:
        msg = trimMessage(msg)
        print(f'AFTER TRIM: {msg}')
        accounts = Shared.data.servers[guild_id].accounts
        
        print(f'RIGHT BEFORE{msg}')
        success, username, atype, msg = extractCommand(msg)
        if not success:
            return 'Error 5'
        
        if not public:
            account = None
            for acc in accounts:
                if acc.username == username and acc.type == atype:
                    if author_id in acc.dms:
                        return 'Error 6'
                    account = acc
                    break
                
            if not account:
                acc = Account()
                acc.active = True
                acc.type = atype
                acc.username = username
                acc.dms = [author_id]
                accounts.append(acc)
            else:
                account.dms.append(author_id)
        
        else:
            for account in accounts:
                if account.username == username and account.type == atype and account.channel == channel_id:
                    return 'This already exists so no...'
            
            acc = Account()
            acc.active = True
            acc.type = atype
            acc.username = username
            acc.channel = channel_id
            acc.dms = []
            accounts.append(acc)
        
        Shared.data.write()
        
        return msg