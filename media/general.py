class GeneralCDN:
    def __init__(self, url, parsed_url):
        self.url = url
        self.parsed = parsed_url

        if self.parsed.netloc in ("cdn.discordapp.com", "media.discordapp.net", "images-ext-1.discordapp.net", "images-ext-2.discordapp.net", "images-ext-3.discordapp.net", "images-ext-4.discordapp.net"):
            self.is_valid_gif = False # discord cdn urls can be migrated, but they will expire so its useless
        else:
            is_valid_gif = any(self.parsed.path.lower().endswith(ext) for ext in [".gif", ".webp", ".avif", ".mp4", ".png"])
            is_valid_gif = is_valid_gif or "imgur.com" in self.parsed.netloc

            self.is_valid_gif = is_valid_gif
            if not is_valid_gif:
                self.log("[invalid] [general]", self.url)

    def log(self, *args):
        print("[GeneralCDN]", *args)

    def parse_information(self):
        pass