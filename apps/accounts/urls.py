"""
URL patterns in lending app
"""
from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import Login

app_name = "accounts"
urlpatterns = [
    path("login/", Login.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
