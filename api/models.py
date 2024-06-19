#✅models.py
from django.db import models
from pydantic import BaseModel
class URLMapping(models.Model):
    long_url = models.URLField()
    short_url = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.short_url

# 🆔authentication
class User(BaseModel):
    username : str
    email: str
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str
class Token(BaseModel):
    access_token: str
    token_type: str
class TokenData(BaseModel):
    username : str | None = None

