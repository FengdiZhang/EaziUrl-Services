# EaziUrl-Services


## Overview
URL Shortener Backend Services built using Django and FastAPI. The backend is powered by Django for database management and FastAPI for handling API requests. PostgreSQL is used as the database, and Redis is used for caching.


## Requirements
- Python 3.12
- Docker Desktop
- Redis Insight 


## Before start:
- Run Docker Desktop 
- Add docker-compose.yml file
- Run Redis Insight 

## Get started:

- docker-compose up --build
- docker exec -it <container_id>
- docker-compose exec python manage.py createsuperuser
- python -m venv venv
- source venv/bin/activate
- pip install django fastapi uvicorn django-redis pydantic python-jose passlib
- python manage.py makemigrations
- python manage.py migrate
- uvicorn myproject.asgi:app --reload

## Access application:
- FastAPI documentation: http://127.0.0.1:8000/api/docs
- Django admin panel: http://127.0.0.1:8000/admin

