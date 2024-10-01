from pyppeteer.page import Page
from data import Account
from discord import Embed
from typing import Dict, List


class Impl:
    
    async def fetch(self, account: Account, page: Page): pass
    
    async def parse(self, account: Account, page: Page) -> Dict[str, List[Embed]]: pass