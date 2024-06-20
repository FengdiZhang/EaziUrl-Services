from datetime import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser
from pydantic import BaseModel, EmailStr

class URLMapping(models.Model):
    long_url = models.URLField()
    short_url = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.short_url

class URLMappingSchema(BaseModel):
    long_url: str
    short_url: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    disabled = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class User(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
