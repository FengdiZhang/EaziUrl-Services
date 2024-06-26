import random
import string
from typing import List
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from .auth_endpoints import get_current_active_user
from .models import URLMapping, URLMappingSchema, CustomUser, UserURLMapping
from django.db import transaction
from fastapi.responses import RedirectResponse
from django.core.cache import cache
import requests
from bs4 import BeautifulSoup

app = FastAPI()

class Shortener:
    def __init__(self):
        # 🔨Base URL prefix
        self.real_base = "http://127.0.0.1:8000/api/"
        self.chars = string.ascii_letters + string.digits

    def _generate_short_key(self):
        # ✅Generate a 6-character random short URL key
        return ''.join(random.choice(self.chars) for _ in range(6))

    def encode(self, longUrl: str, title: str, user: CustomUser) -> dict:
        with transaction.atomic():
            # 1️⃣Check if the long URL exists in cache
            cache_key = f"url:{longUrl}"
            cached_short_urls = cache.get(cache_key)
            if cached_short_urls:
                # 1. Retrieve mapping from the database
                mapping = URLMapping.objects.filter(long_url=longUrl).first()
                # 2. Create/get UserURLMapping for the current user
                user_url_mapping, created = UserURLMapping.objects.get_or_create(
                    user=user,
                    url_mapping=mapping,
                    defaults={'title': title}
                )
                if not created:
                    # 3. Update title
                    user_url_mapping.title = title
                    user_url_mapping.save()
                return cached_short_urls

            # 2️⃣ Check if the long URL exists in the database
            mapping = URLMapping.objects.filter(long_url=longUrl).first()
            if mapping:
                # 1. Create/get UserURLMapping for the current user
                user_url_mapping, created = UserURLMapping.objects.get_or_create(
                    user=user,
                    url_mapping=mapping,
                    defaults={'title': title}
                )
                if not created:
                    # 2. Update title
                    user_url_mapping.title = title
                    user_url_mapping.save()
                short_urls = {
                    "real_url": self.real_base + mapping.short_url,
                }
                # 3. Cache the result
                cache.set(cache_key, short_urls)
                return short_urls

            # ❗️Ensure the generated short key is unique
            while True:
                short_key = self._generate_short_key()
                if not URLMapping.objects.filter(short_url=short_key).exists():
                    break

            # ♻️Save the long URL and short URL to the database
            mapping = URLMapping(long_url=longUrl, short_url=short_key, created_by=user)
            mapping.save()
            UserURLMapping.objects.create(user=user, url_mapping=mapping, title=title)

            short_urls = {
                "real_url": self.real_base + short_key,
            }
            # Cache the result
            cache.set(cache_key, short_urls)
            return short_urls

shortener = Shortener()

class URLItem(BaseModel):
    url: str
    title: str = ''

# ⛳️All my endpoints:
@app.get("/test")
async def read_test():
    return {"message": "⭐️This is a test endpoint"}

# 1️⃣Retrieve all links for the current user:
@app.get("/links", response_model=List[URLMappingSchema])
def get_all_links(current_user: CustomUser = Depends(get_current_active_user)):
    user_links = UserURLMapping.objects.filter(user=current_user).select_related('url_mapping')
    return [
        URLMappingSchema(
            long_url=user_link.url_mapping.long_url,
            short_url=user_link.url_mapping.short_url,
            title=user_link.title,
            created_at=user_link.url_mapping.created_at,
            created_by=user_link.url_mapping.created_by.username
        ) for user_link in user_links
    ]

# 2️⃣Encode long URL -> short URL:
@app.post("/encode")
def encode_url(item: URLItem, current_user: CustomUser = Depends(get_current_active_user)):
    short_urls = shortener.encode(item.url, item.title, current_user)
    return {
        "real_url": short_urls["real_url"],
        "title": item.title
    }

# 3️⃣Redirect to the long URL based on the short key
@app.get("/{short_key}")
def redirect_url(short_key: str):
    cache_key = f"short:{short_key}"
    cached_long_url = cache.get(cache_key)
    if cached_long_url:
        return RedirectResponse(url=cached_long_url)

    mapping = URLMapping.objects.filter(short_url=short_key).first()
    if mapping:
        long_url = mapping.long_url
        cache.set(cache_key, long_url)
        return RedirectResponse(url=long_url)
    else:
        raise HTTPException(status_code=404, detail="URL not found")

# 4️⃣ Fetch the title of a long URL:
@app.post("/fetch_title")
def fetch_title(url: URLItem):
    try:
        response = requests.get(url.url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.title.string if soup.title else "No title found"
        return {"title": title}
    except requests.RequestException as e:
        return {"title": ""}
