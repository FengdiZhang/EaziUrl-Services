# EaziUrl-Services


## Overview
URL Shortener Backend Services built using Django and FastAPI. The backend is powered by Django for database management and FastAPI for handling API requests. PostgreSQL is used as the database, and Redis is used for caching.

## Requirements
- Docker
- Django
- fastapi
- uvicorn
- django-redis
- pydantic
- python-jose
- passlib



## Access application:
- FastAPI documentation: http://127.0.0.1:8000/api/docs
- Django admin panel: http://127.0.0.1:8000/admin

## Get started:
### Build and start container:
- docker-compose up --build
### Data migration:
- python manage.py makemigrations
- python manage.py migrate
### Start database:
- docker exec -it <container_id>
### Start application:
- uvicorn myproject.asgi:app --reload


