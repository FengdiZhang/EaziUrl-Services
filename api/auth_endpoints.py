import os
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from datetime import timedelta
from typing import Optional
from jose import JWTError, jwt
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from starlette.config import Config
import requests

from .models import CustomUser, Token, TokenData, UserSchema, UserCreate
from django.db import transaction
from asgiref.sync import sync_to_async
from .auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)

load_dotenv()

auth_app = FastAPI()
auth_app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

# OAuth2 configuration
client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

oauth = OAuth()
oauth.register(
    name='google',
    client_id=client_id,
    client_secret=client_secret,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri='http://127.0.0.1:8000/auth/callback',
    client_kwargs={'scope': 'openid profile email'},
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
)

# Define the constant
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_user(username: str):
    try:
        user = await sync_to_async(CustomUser.objects.get)(username=username)
        return user
    except CustomUser.DoesNotExist:
        return None

async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username = payload["sub"]
    except JWTError:
        raise credentials_exception
    user = await get_user(username=username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: UserSchema = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@sync_to_async
def create_user_in_db(username: str, password: str, email: str):
    with transaction.atomic():
        return CustomUser.objects.create(
            username=username,
            password=get_password_hash(password),
            email=email
        )

# ⛳️ all auth_endpoints:
@auth_app.post("/register")
async def register_user(user: UserCreate):
    existing_user = await sync_to_async(CustomUser.objects.filter(email=user.email).first)()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_username = await sync_to_async(CustomUser.objects.filter(username=user.username).first)()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = await create_user_in_db(user.username, user.password, user.email)
    return {"message": "User registered successfully"}


@auth_app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"sub": user.username}, expires_delta=refresh_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

@auth_app.post("/refresh", response_model=Token)
async def refresh_access_token(request: Request):
    try:
        body = await request.json()
        refresh_token = body.get('refresh_token')
        if not refresh_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token missing")

        payload = decode_access_token(refresh_token)
        username = payload["sub"]
        user = await get_user(username=username)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@auth_app.get("/users/me/", response_model=UserSchema)
async def read_users_me(current_user: UserSchema = Depends(get_current_active_user)):
    return current_user

# OAuth2 login
@auth_app.get("/login")
async def login_via_google(request: Request):
    redirect_uri = 'http://127.0.0.1:8000/auth/callback'
    return await oauth.google.authorize_redirect(request, redirect_uri)

# OAuth2 callback
@auth_app.get("/callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)

        id_token = token.get('id_token')
        if not id_token:
            raise HTTPException(status_code=400, detail="ID token is missing")

        # Decode id_token
        google_public_keys_url = "https://www.googleapis.com/oauth2/v3/certs"
        google_public_keys = requests.get(google_public_keys_url).json()
        header = jwt.get_unverified_header(id_token)
        key = next(
            (key for key in google_public_keys["keys"] if key["kid"] == header["kid"]),
            None
        )

        if key is None:
            raise HTTPException(status_code=400, detail="Unable to find appropriate key")

        decoded_id_token = jwt.decode(
            id_token, key, algorithms=["RS256"], audience=client_id, options={"verify_at_hash": False}
        )

        user_info = decoded_id_token  # Use decoded id_token as user_info

        username = user_info['email']
        email = user_info['email']

        user = await get_user(username)
        if not user:
            existing_user = await sync_to_async(CustomUser.objects.filter(email=email).first)()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered")

            user = await create_user_in_db(username=username, password='', email=email)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        refresh_token = create_access_token(
            data={"sub": user.username}, expires_delta=refresh_token_expires
        )

        redirect_url = f'http://localhost:3000/auth/callback?username={username}&token={access_token}&refresh_token={refresh_token}'
        return RedirectResponse(url=redirect_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
