import os
import base64
import json
import re
from urllib.parse import unquote

# Credits: https://github.com/Jord38/fluxer-gif-migrator/blob/master/migrate.py

class DiscordAPI:
    def __init__(self):
        pass

    def extract_urls_from_protobuf(self, data: bytes):
        try:              text = data.decode("latin-1")
        except Exception: text = data.decode("utf-8", errors="ignore")

        urls = set()
        for match in re.findall(r'https?://[^\s"\'\x00-\x1F<>)\]]+', text):
            match = match.rstrip(".'\"")
            match = match.split("\\x")[0] if "\\x" in match else match
            match = unquote(match)
            
            if match.startswith(("http://", "https://")) and len(match) > 10:
                urls.add(match)
        
        return list(urls)

    def load_data(self, file_path="discord_data.json"):
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} not found")
            return []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
        except Exception as e:
            print(f"Error: {e}")
            return []
        
        try:
            data = json.loads(content)
            content = data.get("settings", "")
            if not content: pass 
        except json.JSONDecodeError: pass

        try:              protobuf_data = base64.b64decode(content)
        except Exception: protobuf_data = content.encode("utf-8")

        urls = self.extract_urls_from_protobuf(protobuf_data)
        return urls