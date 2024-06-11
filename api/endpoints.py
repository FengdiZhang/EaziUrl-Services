# endpoints.py
import random
import string
from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from .models import URLMapping
from django.db import transaction
from fastapi.responses import RedirectResponse

router = APIRouter()
app = FastAPI()

class Shortener:
    def __init__(self):
        self.real_base = "http://127.0.0.1:8000/api/"
        self.display_base = "eaziurl.fz/"
        self.chars = string.ascii_letters + string.digits

    def _generate_short_key(self):
        return ''.join(random.choice(self.chars) for _ in range(6))

    def encode(self, longUrl: str, title: str= '') -> dict:
        with transaction.atomic():
            # Check if the longURL exists
            mapping = URLMapping.objects.filter(long_url=longUrl).first()
            if mapping:
                return {
                    "real_url": self.real_base + mapping.short_url,
                    "display_url": self.display_base + mapping.short_url
                }

            # make sure generated short_key is unique
            while True:
                short_key = self._generate_short_key()
                if not URLMapping.objects.filter(short_url=short_key).exists():
                    break

            # Save to database
            mapping = URLMapping(long_url=longUrl, short_url=short_key, title=title)
            mapping.save()

        return {
            "real_url": self.real_base + short_key,
            "display_url": self.display_base + short_key
        }

shortener = Shortener()

class URLItem(BaseModel):
    url: str
    title: str = ''

@app.get("/test")
async def read_test():
    return {"message": "This is a test endpoint"}

@app.post("/encode")
def encode_url(item: URLItem):
    short_urls = shortener.encode(item.url, item.title)
    return {
        "real_url": short_urls["real_url"],
        "display_url": short_urls["display_url"],
        "title": item.title
    }

# redirect
@app.get("/{short_key}")
def redirect_url(short_key: str):
    mapping = URLMapping.objects.filter(short_url=short_key).first()
    if mapping:
        return RedirectResponse(url=mapping.long_url)
    else:
        raise HTTPException(status_code=404, detail="URL not found")
