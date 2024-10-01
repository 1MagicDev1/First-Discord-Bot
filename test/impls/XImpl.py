from impls.impl import *
from data import *
from pyppeteer.page import Page
from discord import Embed
from datetime import datetime
import traceback


# X / Twitter / Nitter
class X(Impl):
    
    async def fetch(self, account: Account, page: Page):
        try:
            await page.goto(f'https://nitter.privacydev.net/{account.username}/')
            await page.screenshot({'path': f'skibidi_{account.username}_toilet_{str(datetime.now().strftime('%c')).replace(':', '.')}.png'})
            return True
        except Exception as e:
            print(f'Error: {e}')
            return None
    
    async def parse(self, account: Account, page: Page) -> Dict[str, List[Embed]]:
        try:
            allEmbeds: Dict[str, List[Embed]] = {}
            
            fullNameOrig = await getOriginalName(page)
            if fullNameOrig is None:
                return None
            print(f"Successfully accessed the '{fullNameOrig}' Twitter account!\n")
            
            doAdd = account.counter > 0
            
            thweets = await page.querySelectorAll(".timeline-item")
            foundPhosts = 0
            toSend = []
            
            for item in thweets:
                
                fullName, username, content, pic, images, videos, isRetweet, tweetLink, polls = await extract(item)
                if fullName is None:
                    continue
                if tweetLink in account.phosts:
                    continue
                
                if doAdd:
                    toSend.append((fullName, username, content, pic, images, videos, isRetweet, tweetLink, polls))
                    
                account.phosts.append(tweetLink)
                
                foundPhosts += 1
                
            account.counter += foundPhosts
            
            toSend.reverse()
            
            for send in toSend:
                embeds: List[Embed] = []
                
                fullName, username, content, pic, images, videos, isRetweet, tweetLink, polls = send
                
                embed = Embed(description=f"---",
                                color=0xfc03e3)
                embeds.append(embed)
                
                if isRetweet:
                    embed = Embed(description=f"{fullNameOrig} Retweeted",
                                  color=0xfc03e3)
                    embeds.append(embed)
                         
                if len(content) > 4096:
                    part = content[0:4095]
                    content = content[4095:] # TODO: Figure out if this should be 4096
                    
                    embed = Embed(description=part,
                                  colour=0x00b0f4,
                                  timestamp=datetime.now())
                    embed.set_author(name=fullName,
                                    url=f"https://x.com/{username}",
                                    icon_url=pic)
                    embeds.append(embed)
                    
                    while len(content) > 0:
                        l = min(len(content), 4095) # TODO: Figure out if this should be 4096
                        part = content[0:l]
                        content = content[l:]
                        
                        embed = Embed(description=part,
                                      colour=0x00b0f4,
                                      timestamp=datetime.now())
                        embeds.append(embed)
                        
                else:
                    embed = Embed(description=content,
                                  colour=0x00b0f4,
                                  timestamp=datetime.now())
                    embed.set_author(name=fullName,
                                    url=f"https://x.com/{username}",
                                    icon_url=pic)
                    embeds.append(embed)
                
                for image in images:
                    embed = Embed(description='',
                                  colour=0x0bfc03)
                    embed.set_image(url=image)
                    embeds.append(embed)
                    
                # for video in videos:
                #     embed = discord.Embed().video()
                #     embed.url = video
                #     embeds.append(embed)

                allEmbeds[tweetLink] = embeds
                
            return allEmbeds
        except Exception as e:
            print('Error:')
            print(traceback.format_exc())
            return None


async def extract(item):
    elem = await item.querySelector('.tweet-body')
    if elem is None:
        return None, None, None, None, None, None, None, None, None
    
    elem = await item.querySelector('.fullname')
    text = await elem.getProperty('textContent')
    fullName = await text.jsonValue()

    elem = await item.querySelector('.username')
    text = await elem.getProperty('textContent')
    userName = await text.jsonValue()

    elem = await item.querySelector('.tweet-content')
    text = await elem.getProperty('textContent')
    tweetContent = await text.jsonValue()

    elem = await item.querySelector('.avatar.round')
    text = await elem.getProperty('src')
    pictureUrl = await text.jsonValue()
    
    elem = await item.querySelector('.tweet-link')
    text = await elem.getProperty('href')
    tweetLink = await text.jsonValue()
    
    images = []
    elem = await item.querySelectorAll('.still-image')
    for image in elem:
        #print('Image found: ', image)
        imgUrl = await image.getProperty('href')
        images.append(await imgUrl.jsonValue())

    videos = []
    elem = await item.querySelectorAll('video')
    for video in elem:
        # print('Video found: ', video)
        elem2 = await video.querySelector('source')
        videoUrl = await elem2.getProperty('src')
        videos.append(await videoUrl.jsonValue())

    polls = []
    elem = await item.querySelector('.poll')
    if elem:
        elem = await elem.querySelectorAll('.poll-meter')
        for pollItem in elem:
            elem2 = await pollItem.querySelector('.poll-choice-option')
            text = await elem2.getProperty('textContent')
            polls.append(await text.jsonValue())

    elem = await item.querySelector('.retweet-header')
    isRetweet = elem is not None

    return fullName, userName, tweetContent, pictureUrl, images, videos, isRetweet, tweetLink, polls

async def getOriginalName(page):
    elem = await page.querySelector('.profile-card-fullname')
    if not elem: return None
    text = await elem.getProperty('textContent')
    if not text: return None
    return await text.jsonValue()