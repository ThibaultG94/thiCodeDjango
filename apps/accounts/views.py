from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, password_validation
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import ValidationError
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str as force_text

from .models import User
from .forms import SignUpForm

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .serializers import UserSerializer

from django.core.mail import send_mail
from django.utils.html import strip_tags
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

@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """Endpoint to request a password reset"""
    email = request.data.get('email')
    
    if not email:
        return Response({'error': 'Email obligatoire'}, status=status.HTTP_400_BAD_REQUEST)
    
    # User search by email
    try:
        user = User.objects.get(email=email)
        
        # Generate a unique token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Building the reset URL
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}-{token}"
        
        # Email preparation
        subject = "Réinitialisation de votre mot de passe ThiCodeAI"
        html_message = f"""
        <h2>Réinitialisation de mot de passe</h2>
        <p>Bonjour {user.username},</p>
        
        <p>Vous avez demandé la réinitialisation de votre mot de passe sur ThiCodeAI.</p>
        
        <p><a href="{reset_url}">Cliquez ici pour définir un nouveau mot de passe</a></p>
        
        <p>Ou copiez-collez ce lien dans votre navigateur :<br>
        {reset_url}</p>
        
        <p>Ce lien est valable pendant 24 heures.</p>
        
        <p>Si vous n'avez pas demandé cette réinitialisation, ignorez simplement cet email.</p>
        
        <p>L'équipe ThiCodeAI</p>
        """
        message = f"""
        Bonjour {user.username},
        
        Vous avez demandé la réinitialisation de votre mot de passe sur ThiCodeAI.
        
        Cliquez sur le lien suivant pour définir un nouveau mot de passe :
        {reset_url}
        
        Ce lien est valable pendant 24 heures.
        
        Si vous n'avez pas demandé cette réinitialisation, ignorez simplement cet email.
        
        L'équipe ThiCodeAI
        """
        
        # Envoi explicite via SendGrid
        from django.core.mail import EmailMultiAlternatives
        from django.utils.html import strip_tags

        email_message = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()
        
    except User.DoesNotExist:
        # Do not inform the user that the email does not exist (security)
        pass
    
    # Always return a success, even if the email doesn't exist
    return Response({'message': 'Si votre email est associé à un compte, vous recevrez un lien de réinitialisation'})

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_reset_token(request, token):
    """Checks the validity of a reset token"""
    try:
        # Uid and token extraction
        parts = token.split('-', 1)
        if len(parts) != 2:
            return Response({'valid': False}, status=status.HTTP_400_BAD_REQUEST)
        
        uid, token = parts
        
        # uid decoding
        user_id = force_text(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
        
        # Token verification
        if default_token_generator.check_token(user, token):
            return Response({'valid': True})
        else:
            return Response({'valid': False})
            
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return Response({'valid': False})

@api_view(['POST'])
@permission_classes([AllowAny])
def confirm_password_reset(request):
    """Confirme la réinitialisation du mot de passe"""
    token = request.data.get('token')
    password = request.data.get('password')
    
    if not token or not password:
        return Response(
            {'error': 'Token et mot de passe obligatoires'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Uid and token extraction
        parts = token.split('-', 1)
        if len(parts) != 2:
            return Response({'error': 'Token invalide'}, status=status.HTTP_400_BAD_REQUEST)
        
        uid, token = parts
        
        # uid decoding
        user_id = force_text(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
        
        # Token validation
        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Token invalide ou expiré'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Password validation
        try:
            password_validation.validate_password(password, user)
        except ValidationError as e:
            return Response({'error': e.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        
        # Password update
        user.set_password(password)
        user.save()
        
        return Response({'message': 'Mot de passe modifié avec succès'})
        
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return Response({'error': 'Token invalide'}, status=status.HTTP_400_BAD_REQUEST)