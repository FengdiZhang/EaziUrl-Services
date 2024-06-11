from django.contrib import admin
from django.urls import path, re_path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('test/', views.test_view),
    # re_path(r'^(?P<short_key>\w{6})$', views.redirect_url, name='redirect_url'),
]
