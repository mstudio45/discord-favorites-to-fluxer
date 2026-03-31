import json
import traceback
import os

class MediaCache:
    def __init__(self, file_path="media_cache.json"):
        self.file_path = file_path
        self.cache = {}

        self.load()

    def log(self, *args):
        print("[MediaCache]", *args)

    def load(self):
        if not os.path.exists(self.file_path) or os.stat(self.file_path).st_size == 0:
            try:
                with open(self.file_path, "w", encoding="utf-8") as f:
                    f.write("{}")
                    f.close()
            except Exception as e:
                self.log("[fail] [init]", traceback.format_exc())
                exit(1)

        try:
            self.read_file = open(self.file_path, "r", encoding="utf-8")
            self.write_file = open(self.file_path, "r+", encoding="utf-8")
        except Exception as e:
            self.log("[fail] [open]", traceback.format_exc())
            exit(1)
        
        try:
            self.read_file.seek(0)
            self.cache = json.load(self.read_file)
        except Exception as e:
            self.log("[fail] [load]", traceback.format_exc())
            exit(1)

    def get(self, url):
        return self.cache.get(url)

    def set(self, url, data):
        if data: self.cache[url] = data

    def save(self):
        try:
            self.write_file.seek(0)
            self.write_file.truncate()
            json.dump(self.cache, self.write_file, indent=4)
            self.write_file.flush()
        except Exception as e:
            self.log("[fail] [save]", traceback.format_exc())

    def close(self):
        try:
            if hasattr(self, "read_file"): self.read_file.close()
            if hasattr(self, "write_file"): self.write_file.close()
        except: pass