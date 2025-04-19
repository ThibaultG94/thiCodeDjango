from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt

from .models import User
from .forms import SignUpForm

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .serializers import UserSerializer

class SignUpView(CreateView):
    model = User
    form_class = SignUpForm 
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')

@login_required
def user_settings(request):
    """Gérer les paramètres utilisateur"""
    if request.method == 'POST':
        # Update AI model
        if 'ai_model' in request.POST:
            request.user.ai_model = request.POST['ai_model']
            messages.success(request, "Préférences mises à jour avec succès.")
        
        return redirect('accounts:settings')
    
    # List of available models
    available_models = [
        {'id': 'llama2', 'name': 'Llama 2'},
        {'id': 'llama2-70b', 'name': 'Llama 2 (70B)'},
        {'id': 'codellama', 'name': 'CodeLlama'}
    ]
    
    return render(request, 'accounts/settings.html', {
        'user': request.user,
        'available_models': available_models,
        'current_model': request.user.ai_model
    })

@api_view(['GET'])
@ensure_csrf_cookie
def current_user(request):
    """Endpoint pour récupérer l'utilisateur connecté"""
    if request.user.is_authenticated:
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    return Response({'detail': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_preferences(request):
    """Endpoint pour mettre à jour les préférences utilisateur"""
    user = request.user
    if 'preferences' in request.data:
        user.preferences = request.data['preferences']
        user.save()
        return Response(UserSerializer(user).data)
    return Response({'error': 'No preferences provided'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
@ensure_csrf_cookie
def api_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    if user:
        login(request, user)
        return Response({
            'user': UserSerializer(user).data,
            'message': 'Connexion réussie'
        })
    return Response(
        {'message': 'Nom d\'utilisateur ou mot de passe incorrect'}, 
        status=status.HTTP_401_UNAUTHORIZED
    )

@api_view(['POST'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def api_register(request):
    from .forms import SignUpForm
    
    form = SignUpForm(request.data)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return Response({
            'user': UserSerializer(user).data,
            'message': 'Inscription réussie'
        })
    return Response(
        {'errors': form.errors}, 
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['POST'])
@ensure_csrf_cookie
def api_logout(request):
    logout(request)
    return Response({'message': 'Déconnexion réussie'})