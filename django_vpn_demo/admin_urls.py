"""
URL configuration for admin subdomain/host.
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('', admin.site.urls),
]
