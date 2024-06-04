# myproject/api/endpoints.py
import random
import string
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .models import URLMapping
from django.db import transaction

app = FastAPI()

class Shortener:
    def __init__(self):
        self.base = "http://eaziurl.com/"
        self.chars = string.ascii_letters + string.digits

    def _generate_short_key(self):
        return ''.join(random.choice(self.chars) for _ in range(6))

    def encode(self, longUrl: str) -> str:
        with transaction.atomic():
            # Check if the long URL already exists
            mapping = URLMapping.objects.filter(long_url=longUrl).first()
            if mapping:
                return self.base + mapping.short_url

            # make sure generated short key is unique
            while True:
                short_key = self._generate_short_key()
                if not URLMapping.objects.filter(short_url=short_key).exists():
                    break

            # Save to the database
            mapping = URLMapping(long_url=longUrl, short_url=short_key)
            mapping.save()

        return self.base + short_key

    def decode(self, shortUrl: str) -> str:
        short_key = shortUrl.replace(self.base, "")
        mapping = URLMapping.objects.filter(short_url=short_key).first()
        if mapping:
            return mapping.long_url
        return ""

shortener = Shortener()

class URLItem(BaseModel):
    url: str

@app.post("/encode")
def encode_url(item: URLItem):
    short_url = shortener.encode(item.url)
    return {"short_url": short_url}

@app.get("/decode")
def decode_url(short_url: str):
    long_url = shortener.decode(short_url)
    if not long_url:
        raise HTTPException(status_code=404, detail="URL not found")
    return {"long_url": long_url}
