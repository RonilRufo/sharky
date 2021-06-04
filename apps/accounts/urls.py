"""
URL patterns in lending app
"""
from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import Login, PasswordChange

app_name = "accounts"
urlpatterns = [
    path("login/", Login.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password-change/", PasswordChange.as_view(), name="password-change"),
]
