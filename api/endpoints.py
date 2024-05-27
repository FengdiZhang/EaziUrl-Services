# myproject/api/endpoints.py
import random
import string
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Shortener:
    def __init__(self):
        self.base = "http://faye.com/"
        self.chars = string.ascii_letters + string.digits
        self.long_to_short = {}
        self.short_to_long = {}

    def _generate_short_key(self):
        return ''.join(random.choice(self.chars) for _ in range(6))

    def encode(self, longUrl: str) -> str:
        if longUrl in self.long_to_short:
            return self.base + self.long_to_short[longUrl]

        while True:
            short_key = self._generate_short_key()
            if short_key not in self.short_to_long:
                break

        self.long_to_short[longUrl] = short_key
        self.short_to_long[short_key] = longUrl

        return self.base + short_key

    def decode(self, shortUrl: str) -> str:
        short_key = shortUrl.replace(self.base, "")
        return self.short_to_long.get(short_key, "")

shortener = Shortener()

# → schemas.py later
class URLItem(BaseModel):
    url: str

@app.post("/encode")
def encode_url(item: URLItem):
    short_url = shortener.encode(item.url)

    # print("short_url", short_url)
    return {"short_url": short_url}

@app.get("/decode")
def decode_url(short_url: str):
    long_url = shortener.decode(short_url)
    if not long_url:
        raise HTTPException(status_code=404, detail="URL not found")

    # print("long_url", long_url)
    return {"long_url": long_url}

@app.get("/hello")
def hello():
    return {"message": "Hello from FastAPI"}
