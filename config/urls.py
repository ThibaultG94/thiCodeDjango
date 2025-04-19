"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from apps.core.views import get_csrf_token, home

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints for the React frontend
    path('api/accounts/', include('apps.accounts.urls', namespace='api_accounts')),
    path('api/chat/', include('apps.chat.urls', namespace='api_chat')),
    path('api/csrf/', get_csrf_token, name='csrf_token'),
    
    # Traditional frontend routes (Django templates)
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('chat/', include('apps.chat.urls', namespace='chat')), 
    path('', include('apps.core.urls')),
]