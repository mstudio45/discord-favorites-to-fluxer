import re
import requests
from bs4 import BeautifulSoup
import traceback

class TenorCDN:
    def __init__(self, url, parsed_url, skip_mp4=True, convert_mp4_to_gif=False):
        self.url = url
        self.parsed = parsed_url

        self.skip_mp4 = skip_mp4
        self.convert_mp4_to_gif = convert_mp4_to_gif

        self.slug_tried = False
        self.slug_id = None

        self.media_tried = False
        self.media_url = None

        self.response = None

    def log(self, *args):
        print(f"[Tenor CDN] {' '.join(args)}")

    def _response_cache(self):
        if not self.response:
            self.response = requests.get(self.url, headers={
                "Accept": "text/html",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
            })
        
        return self.response

    def _get_slug(self, view_url):
        match = re.search(r'view/([^/?]+)', view_url)
        return ("view/" + match.group(1)) if match else None

    def _fix_media_url(self, url):
        if url.endswith(".mp4"):
            if self.skip_mp4:
                self.log("Skipping tenor MP4 URL:", url)
                return None
            
            if self.convert_mp4_to_gif:
                self.log("Converting tenor MP4 URL to GIF:", url)
                return url[:-4] + ".gif"
        
        return url

    def _scrape_slug_url(self):
        if "tenor.com" in self.url and "/view/" in self.url:
            return self._get_slug(self.url)
        
        elif self.parsed.netloc.startswith("media") and "tenor.com" in self.parsed.netloc:
            if self.url.endswith(".mp4"):
                if self.skip_mp4:
                    self.log("Skipping tenor MP4 URL:", self.url)
                    return None

            self.log("Scraping slug for media URL:", self.url)
            try:
                response = self._response_cache()

                soup = BeautifulSoup(response.text, "html.parser")
                link = soup.find("link", rel="canonical")

                if link and link.has_attr("href"):
                    return self._get_slug(link["href"])
            except Exception as e:
                self.log("Failed to scrape slug for media URL:", self.url, traceback.format_exc())
            
            return None
        else:
            self.log("Invalid Tenor URL:", self.url)
            return None

    def _scrape_media_url(self):
        if "tenor.com" in self.url and "/view/" in self.url:
            try:
                response = self._response_cache()

                soup = BeautifulSoup(response.text, "html.parser")
                for meta in soup.find_all("meta"):
                    if meta.has_attr("property") and meta["property"] == "og:image":
                        content = meta["content"]
                        if ("://media" in content and "tenor.com" in content) and content.endswith(".gif"):
                            return self._fix_media_url(content)

                self.log("Failed to find media URL:", self.url)
            except Exception as e:
                self.log("Failed to scrape media URL:", self.url, traceback.format_exc())
            
            return None
        elif self.parsed.netloc.startswith("media") and "tenor.com" in self.parsed.netloc:
            return self._fix_media_url(self.url)
        else:
            self.log("Invalid Tenor URL:", self.url)
            return None

    async def parse_information(self):
        if self.slug_tried != True:
            self.slug_tried = True
            self.slug_id = self._scrape_slug_url()

        if self.media_tried != True:
            self.media_tried = True
            self.media_url = self._scrape_media_url()