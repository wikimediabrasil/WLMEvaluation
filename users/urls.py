from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect
from django.urls import path, include

from . import views

app_name = "users"
urlpatterns = [
    path("logout/", LogoutView.as_view(), name="logout"),

]