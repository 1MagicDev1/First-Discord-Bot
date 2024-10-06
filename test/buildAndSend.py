import asyncio
from pyppeteer import launch
import discord
import random
from sharedVars import Shared
import datetime
from data import Data, Server, Account
from typing import Dict, List
from impls.impl import *
from impls.InstagramImpl import Instagram
from impls.TwitchImpl import Twitch
from impls.XImpl import X


def startRetrieval(client: discord.Client):
    asyncio.run(startRetrieval_(client))


async def startRetrieval_(client: discord.Client):
    browser = await launch()
    page = await browser.newPage()
    
    await page.setViewport({"width": 1920, "height": 1080})
    # await page.setViewport({"width": 1280, "height": 720})
    
    data: Data = Shared.data
    
    while True:
        cache: Dict[str, Dict[str, List[discord.Embed]]] = {}
        for server_id, server in data.servers.items():
            if not server.active:
                continue
            
            g = await client.fetch_guild(server_id)
            if not g:
                continue
            
            for account in server.accounts:
                if not account.active:
                    continue
                
                print(f'Guild id: {g.id}')
                
                chn = None
                userRefs: List[discord.User] = []
                dmsLen = len(account.dms)
                
                channel_id = account.channel
                if channel_id > 0:
                    chn = await g.fetch_channel(channel_id)
                    if chn:
                        print(f'Channel id: {channel_id}')
                    elif chn is None and dmsLen == 0:
                        print('You suck and swallow')
                        continue
                
                if dmsLen == 0 and chn is None:
                    print('No channel + no dms = no fetch')
                    continue
                elif dmsLen > 0:
                    for dmId in account.dms:
                        member = (await g.fetch_member(dmId))
                        if member:
                            userRef = (await client.fetch_user(dmId))
                            if userRef:
                                userRefs.append(userRef)
                
                key = f'{account.type}@{account.username}'
                print(f'User to search: {key}')
                if key in cache:
                    cached = cache[key]
                    
                    doSend = account.counter > 0
                    
                    print('Cached embeds:', cached)
                    adds = 0
                    for uid, _ in cached.items():
                        print(f"{uid}: {_}")
                        if not uid in account.phosts:
                            account.phosts.append(uid)
                            adds += 1
                    
                    if adds > 0:
                        account.counter += adds
                        data.write()
                    
                    if doSend:
                        for _, embed in cached.items():  # Note for self, check if there is a url of the post in the cache, if not, dont send (dont think it does that atm)
                            if chn is not None:
                                await chn.send(embeds=embed)
                            for userRef in userRefs:
                                await userRef.send(embeds=embed)
                    continue
                
                impl: Impl
                
                if account.type == Shared.twitter:
                    impl = X()
                elif account.type == Shared.instagram:
                    impl = Instagram()
                elif account.type == Shared.twitch:
                    impl = Twitch()
                else:
                    print('GAY')
                    continue
                
                res = await impl.fetch(account, page)
                if res is None:
                    print('HOMO')
                    continue
                
                embeds = await impl.parse(account, page)
                if embeds is None:
                    print('ur mom gey')
                    await asyncio.sleep(random.randint(30, 60))
                    continue
                
                print('Embeds:', embeds)
                for uid, embed in embeds.items():
                    if chn is not None:
                        await chn.send(embeds=embed)
                    for userRef in userRefs:
                        await userRef.send(embeds=embed)
                
                cache[key] = embeds
                
                print(f'All Cache: {cache}')
                
                data.write()
                
                await asyncio.sleep(random.randint(15, 30))
            await asyncio.sleep(random.randint(15, 30))
        
        # await page.goto('https://nitter.privacydev.net/RiotPhroxzon/')

        # await asyncio.sleep(random.randint(90, 60*3))
        await asyncio.sleep(random.randint(5, 10))