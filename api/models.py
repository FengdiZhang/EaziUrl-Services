#✅models.py
from django.db import models

class URLMapping(models.Model):
    long_url = models.URLField()
    short_url = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.short_url


