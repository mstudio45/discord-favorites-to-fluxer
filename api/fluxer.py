import json, os
# Credits: https://github.com/Jord38/fluxer-gif-migrator/blob/master/migrate.py

def load_config(file_path="fluxer_data.json"):
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found")
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("token")
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

class FluxerAPI:
    def __init__(self, token, client):
        self.base_url = "https://api.fluxer.app/v1"
        self.headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }

        self.client = client

    async def verify_token(self):
        try:
            resp = await self.client.get(f"{self.base_url}/users/@me", headers=self.headers)
            if resp.status_code == 200:
                return True, resp.json()
                
            return False, f"Status: {resp.status_code}"
        except Exception as e:
            return False, str(e)

    async def get_favorite_memes(self):
        try:
            resp = await self.client.get(f"{self.base_url}/users/@me/memes", headers=self.headers)
            if resp.status_code == 200:
                return resp.json(), True
            
            return [], False
        except:
            return [], False

    async def add_favorite_meme(self, data):
        try:
            resp = await self.client.post(
                f"{self.base_url}/users/@me/memes",
                headers=self.headers,
                json=data,
            )

            if resp.status_code == 201:
                meme = resp.json()
                return True, meme.get("name", "ok")

            elif resp.status_code == 429:
                return False, "rate_limited"

            elif resp.status_code == 409:
                return True, "duplicate"

            else:
                body = resp.text[:350]
                return False, f"HTTP {resp.status_code}: {body}"
        except Exception as e:
            return False, str(e)[:50]