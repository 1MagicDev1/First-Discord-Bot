from impls.impl import *
from data import *
from pyppeteer.page import Page
from discord import Embed
from datetime import datetime
import traceback


# Instagram
class Instagram(Impl):
    
    async def fetch(self, account: Account, page: Page):
        try:
            await page.goto(f'https://www.instagram.com/{account.username}/')
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
            print(f"Successfully accessed the '{fullNameOrig}' Instagram account!\n")
            
            doAdd = account.counter > 0
            
            phosts = await page.querySelectorAll(".x1lliihq.x1n2onr6.xh8yej3.x4gyw5p.xfllauq.xubrtap.x11i5rnm.x2pgyrj")
            foundPhosts = 0
            toSend = []
            
            for item in phosts:  # Extract only links, if new posts, then create new page to see them posts. Similar to X, it only posts new ones so...
                
                username, content, pic, images, videos, instalink = await extract(item)
                if instalink in account.phosts:
                    continue
                
                if doAdd:
                    toSend.append((username, content, pic, images, videos, instalink))
                    
                account.phosts.append(instalink)
                
                foundPhosts += 1
                
            account.counter += foundPhosts
            
            toSend.reverse()
            
            for send in toSend:
                embeds: List[Embed] = []
                
                username, content, pic, images, videos, instalink= send
                
                embed = Embed(description=f"---",
                                color=0xfc03e3)
                embeds.append(embed)
                         
                if len(content) > 4096:
                    part = content[0:4095]
                    content = content[4095:] # TODO: Figure out if this should be 4096
                    
                    embed = Embed(description=part,
                                  colour=0x00b0f4,
                                  timestamp=datetime.now())
                    embed.set_author(name=username,
                                    url=f"https://www.instagram.com/{username}/",
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
                    embed.set_author(name=username,
                                    url=f"https://www.instagram.com/{username}/",
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

                allEmbeds[instalink] = embeds
                
            return allEmbeds
        except Exception as e:
            print('Error:')
            print(traceback.format_exc())
            return None


async def extract(item):  # NEED HELP UWU
    elem = await item.querySelector('.tweet-body')
    if elem is None:
        return None, None, None, None, None, None
    
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
    elem = await page.querySelector('.x1lliihq.x193iq5w.x6ikm8r.x10wlt62.xlyipyv.xuxw1ft')
    if not elem: return None
    text = await elem.getProperty('textContent')
    if not text: return None
    return await text.jsonValue()