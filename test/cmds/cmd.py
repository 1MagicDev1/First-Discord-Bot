from discord import Member, Guild, TextChannel

class Cmd:
    
    def canRun(self, guild: Guild, channel: TextChannel, member: Member) -> bool:
        return False
    
    
    def run(self, guild: Guild, channel: TextChannel, member: Member, command: str) -> None:
        pass