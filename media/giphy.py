from utils.browser import get_browser

class GiphyCDN:
    def __init__(self, url, parsed_url):
        self.url = url
        self.parsed = parsed_url

        self.media_url_tried = False
        self.media_url = None

    def log(self, *args):
        print(f"[Giphy CDN] {' '.join(args)}")

    def _fix_media_url(self, media_url):
        if media_url.endswith("/giphy.gif"):
            return media_url
        else:
            return media_url.rsplit("/", 1)[0] + "/giphy.gif"

    async def _scrape_media_url(self):
        if self.parsed.netloc.startswith("media") and "giphy.com/media" in self.url:
            return self._fix_media_url(self.url)
        
        elif "giphy.com/gifs/" in self.url:
            try:
                browser = await get_browser()
                page = await browser.new_page()

                # load page #
                await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media"] else route.continue_())
                await page.goto(self.url)

                # find valid media url #
                meta_tags = await page.query_selector_all("meta")
                media_url_found = None

                for meta in meta_tags:
                    property_attr = await meta.get_attribute("property")
                    if property_attr == "og:image":
                        media_url = await meta.get_attribute("content")
                        if media_url and (media_url.endswith("/giphy.gif") or media_url.endswith("/giphy.webp")):
                            media_url_found = self._fix_media_url(media_url)
                            break
                
                await page.close()
                if media_url_found:
                    return media_url_found
                
                self.log("Failed to find media URL:", self.url)
            except Exception as e:
                self.log("Failed to scrape media URL:", self.url, str(e))

            return None
        else:
            self.log("Invalid Giphy URL:", self.url)
            return None

    async def parse_information(self):
        if self.media_url_tried == True:
            return
        
        self.media_url_tried = True
        self.media_url = await self._scrape_media_url()