import os
import django
from django.core.asgi import get_asgi_application
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

from api.endpoints import app as fastapi_app

# 获取 Django 的 ASGI 应用
django_asgi_app = get_asgi_application()

def get_application() -> FastAPI:
    app = FastAPI(title="My Project", debug=True)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/django", WSGIMiddleware(django_asgi_app))
    app.mount("/api", fastapi_app)
    app.mount("/static", StaticFiles(directory="staticfiles"), name="static")

    return app

app = get_application()