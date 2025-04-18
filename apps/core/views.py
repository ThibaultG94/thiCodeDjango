from django.shortcuts import render
from django.http import JsonResponse
from django.middleware.csrf import get_token

def home(request):
    return render(request, 'core/home.html')

def get_csrf_token(request):
    """Endpoint to obtain a CSRF token"""
    csrf_token = get_token(request)
    return JsonResponse({'csrfToken': csrf_token})