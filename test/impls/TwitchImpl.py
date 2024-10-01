from impls.impl import *


# Twitch
class Twitch(Impl):
    
    async def fetch(self, account: Account, page: Page):
        pass
    
    async def parse(self, account: Account, page: Page) -> Dict[str, List[Embed]]:
        pass