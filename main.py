import json
import asyncio, httpx
from urllib.parse import urlparse

from media.tenor import TenorCDN
from media.giphy import GiphyCDN
from media.general import GeneralCDN

from api.fluxer import FluxerAPI, load_config
from api.discord import DiscordAPI
from utils.cache import MediaCache
from utils.browser import close_browser

# Config #
BATCH_SIZE = 15
CREATE_TAGS_WITH_PROVIDER = False
SKIP_TENOR_MP4 = True
CONVERT_TENOR_MP4_TO_GIF = False

with open("converter_config.json", "r") as f:
    config = json.load(f)

    BATCH_SIZE = config.get("batch_size", 15)
    CREATE_TAGS_WITH_PROVIDER = config.get("create_tags_with_provider", False)
    SKIP_TENOR_MP4 = config.get("skip_tenor_mp4", True)
    CONVERT_TENOR_MP4_TO_GIF = config.get("convert_tenor_mp4_to_gif", False)

    f.close()

BATCH_SIZE = min(BATCH_SIZE, 20)

# Media Handler #
class MediaHandler:
    def __init__(self, url):
        self.url = url
        self.parsed = urlparse(url)

        # get provider #
        if "tenor.com" in self.parsed.netloc:
            self.provider = "tenor"
            self.tenor = TenorCDN(self.url, self.parsed, skip_mp4=SKIP_TENOR_MP4, convert_mp4_to_gif=CONVERT_TENOR_MP4_TO_GIF)
        elif "giphy.com" in self.parsed.netloc:
            self.provider = "giphy"
            self.giphy = GiphyCDN(self.url, self.parsed)
        else:
            self.provider = "general"
            self.general = GeneralCDN(self.url, self.parsed)

    async def get_information(self, cache=None):
        # check cache first #
        if cache:
            cached_data = cache.get(self.url)
            if cached_data: return cached_data

        # get information #
        info = None
        if self.provider == "tenor":
            await self.tenor.parse_information()

            if self.tenor.media_url:
                info = {
                    "url": self.tenor.media_url,
                    "tenor_slug_id": self.tenor.slug_id or "",
                    "alt_text": self.url,
                    "tags": ["Tenor"] if CREATE_TAGS_WITH_PROVIDER else []
                }
        elif self.provider == "giphy":
            await self.giphy.parse_information()

            if self.giphy.media_url:
                info = { 
                    "url": self.giphy.media_url, 
                    "alt_text": self.url,
                    "tags": ["Giphy"] if CREATE_TAGS_WITH_PROVIDER else []
                }
        else:
            if self.general.is_valid_gif:
                info = { 
                    "url": self.url, 
                    "alt_text": self.url
                }

        # save to cache if valid #
        if info and cache:
            cache.set(self.url, info)
        
        return info

async def __main__():
    # load cache #
    cache = MediaCache()

    # load fluxer api #
    fluxer_token = load_config()
    fluxer = None

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            if fluxer_token and fluxer_token != "":
                fluxer = FluxerAPI(fluxer_token, client)
            else:
                print("[fail] [fluxer] No token found")
                exit(1)

            # verify token #
            valid, data = await fluxer.verify_token()
            if not valid:
                print("[fail] [fluxer] Invalid token")
                exit(1)
            
            print("[success] [fluxer] Token verified")
            print(f"[fluxer] Logged in as: {data.get("username", "???")}")

            # load discord data #
            print("\n[loading discord data]")
            discord = DiscordAPI()
            discord_gifs = discord.load_data()
            
            # get favorited gifs from fluxer #
            print("\n[fetching favorited gifs from fluxer]")
            fluxer_gifs, valid = await fluxer.get_favorite_memes()
            if not valid:
                print("[fail] [fluxer] Failed to get favorited gifs")
                exit(1)
            
            fluxer_alt_texts = [gif["alt_text"] for gif in fluxer_gifs if gif["alt_text"]]
            fluxer_alt_texts = set(fluxer_alt_texts)

            # get information for each media #
            print("\n[fetching media information]")
            media_list = []

            total_valid = 0
            total_invalid = 0
            total_duplicate = 0

            for gif in discord_gifs:
                if gif in fluxer_alt_texts:
                    total_duplicate = total_duplicate + 1
                    continue

                media = MediaHandler(gif)
                info = await media.get_information(cache=cache)

                if info:
                    if info["url"] in fluxer_alt_texts:
                        total_duplicate = total_duplicate + 1
                        continue

                    total_valid = total_valid + 1
                    
                    media_list.append(info)
                    cache.save()
                else: 
                    total_invalid = total_invalid + 1
            
            # re-save cache #
            cache.save()

            # show stats #
            print("\n[media fix stats]")
            print(f"    [valid] {total_valid}")
            print(f"    [invalid] {total_invalid}")
            print(f"    [duplicate] {total_duplicate}")
            print(f"    [total] {total_valid + total_invalid + total_duplicate}")

            # upload to fluxer #
            print("\n[uploading to fluxer]")
            total_added = 0
            total_failed = 0

            index = 1
            current_tries = 0
            total_gifs = len(media_list)
            max_gifs_reached = False

            for gif in media_list:
                if max_gifs_reached:
                    total_failed = total_failed + 1
                    continue
                
                # check batch size #
                if current_tries >= 15:
                    print(f"[info] [ratelimit] 15 gifs reached, sleeping for 60 seconds...")
                    await asyncio.sleep(60)
                    current_tries = 0

                # add to fluxer #
                valid, message = await fluxer.add_favorite_meme(gif)
                if valid:
                    total_added = total_added + 1
                    # print(f"[{index}/{total_gifs}] [success] {gif["url"]}")
                else:
                    total_failed = total_failed + 1
                    print(f"[{index}/{total_gifs}] [fail] {gif["url"]} - {message}")

                    if '"code":"MAX_FAVORITE_MEMES"' in message:
                        max_gifs_reached = True
                        print("[info] [error] Max favorite memes reached")

                    if message == "rate_limited":
                        print("[info] [ratelimit] Rate limited, sleeping for 75 seconds...")
                        await asyncio.sleep(75)
                        current_tries = 0

                # increment tries #
                index = index + 1
                current_tries = current_tries + 1

            # show final stats #
            print("\n[upload stats]")
            print(f"    [success] {total_added}")
            print(f"    [failed] {total_failed}")
            print(f"    [total] {total_added + total_failed}")
    finally:
        await close_browser()
        cache.save()
        cache.close()

        print("\n[done]")

if __name__ == "__main__":
    try:
        asyncio.run(__main__())
    except KeyboardInterrupt:
        print("[info] [exit] Keyboard interrupt")
        exit(0)