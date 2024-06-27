import os
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from datetime import timedelta
from typing import Optional
from jose import JWTError
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from .models import CustomUser, Token, UserCreate, User
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
    client_kwargs={
        'scope': 'openid profile email',
    },
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
)

# Define the constant
ACCESS_TOKEN_EXPIRE_MINUTES = 30
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

async def get_current_active_user(current_user: User = Depends(get_current_user)):
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
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@auth_app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# OAuth2 login
@auth_app.get("/login")
async def login_via_google(request: Request):
    redirect_uri = 'http://127.0.0.1:8000/auth/callback'
    return await oauth.google.authorize_redirect(request, redirect_uri)

# OAuth2 callback
@auth_app.route("/callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        if 'id_token' not in token:
            raise HTTPException(status_code=400, detail="ID token is missing")

        user_info = await oauth.google.parse_id_token(request, token)
        print("User Info:", user_info)  # Add this line for debugging

        username = user_info['email']
        email = user_info['email']

        user = await get_user(username)
        if not user:
            user = await create_user_in_db(username=username, password='', email=email)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        response = RedirectResponse(url='/')
        response.set_cookie(key="Authorization", value=f"Bearer {access_token}", httponly=True)
        return response
    except Exception as e:
        print("Error in callback:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
