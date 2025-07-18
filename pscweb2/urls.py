"""pscweb2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from production.views import ProdList

urlpatterns = [
    path('', ProdList.as_view(), name='root'),
    # Best practice to namespace social auth urls
    # path('social/', include('social_django.urls', namespace='social')), # Twitterログインは使わないのでコメントアウト

    # accounts/signup/ へのルーティングを追加
    path('accounts/', include('accounts.urls')),
    # Django標準の認証URL (login, logoutなど)
    path('accounts/', include('django.contrib.auth.urls')),

    path('admin/', admin.site.urls),
    path('prod/', include('production.urls')),
    path('rhsl/', include('rehearsal.urls')),
    path('scrpt/', include('script.urls')),
]
