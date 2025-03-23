from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import User
from .forms import SignUpForm

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