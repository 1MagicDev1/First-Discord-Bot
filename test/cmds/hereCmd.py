from cmd import *
from discord import Member, Guild, TextChannel
from data import *
from sharedVars import *


class Here(Cmd):
    
    def canRun(self, guild: Guild, channel: TextChannel, member: Member) -> bool:
        try:
            if member.guild_permissions.administrator:
                return True
            
            gId = guild.id
            
            
        except Exception as e:
            print('Error:', e)
        return False
    
    
    def run(self, guild: Guild, channel: TextChannel, member: Member, command: str) -> None:
        pass