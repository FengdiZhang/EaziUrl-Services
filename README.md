# EaziUrl-Services


## Overview
URL Shortener Backend Services built using Django and FastAPI. The backend is powered by Django for database management and FastAPI for handling API requests. PostgreSQL is used as the database, and Redis is used for caching.

**Frontend ➡️ https://github.com/FengdiZhang/EaziUrl-UI**

## Requirements
- Python 3.12
- Docker Desktop
- Redis Insight 


## Before start:
- Run Docker Desktop: Make sure Docker Desktop is running on your machine.
- Add docker-compose.yml file: Ensure you have a docker-compose.yml file in your project directory.
- Run Redis Insight: Make sure Redis Insight is running to monitor your Redis database.

## Get started:


1. **Build and start Docker containers**:
   ```sh
   docker-compose up --build
- Build the Docker images and starts the containers defined in your docker-compose.yml file. It sets up PostgreSQL and Redis, along with your Django and FastAPI services.
2. **List your running containers:**:
   ```sh
   docker ps
- Lists all running Docker containers. Note the <container_id> of your Django container.
3. **Access the running container's shell::**:
   ```sh
   docker exec -it <container_id> /bin/bash
- Replace <container_id> with the ID of your Django container. This command gives you access to the shell of the running container.
4. **Create a Django Superuser:**
   ```sh
   python manage.py createsuperuser

- Creates a superuser for the Django admin panel. You will be prompted to enter a username, email, and password.
5. **Set Up a Virtual Environment:**
    ```sh
   python -m venv venv
- Creates a virtual environment named venv
6. **Activate the virtual environment:**
    ```sh
   source venv/bin/activate
- Activates the virtual environment.
7. **Install required packages:**
    ```sh
   pip install django fastapi uvicorn django-redis pydantic python-jose passlib authlib itsdangerous python-dotenv PyJWT
- Installs all the necessary packages for your project.
8. **Make and apply migrations:**
    ```sh
   python manage.py makemigrations
    python manage.py migrate
- Create and apply database migrations, setting up your database schema.
9. **Start the FastAPI server:**
   ```sh 
   uvicorn myproject.asgi:app --reload
- Starts the FastAPI server and reloads it automatically when code changes are detected.

## Access application:
- FastAPI documentation: http://127.0.0.1:8000/api/docs
- Django admin panel: http://127.0.0.1:8000/admin

