from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .models import User
from .forms import SignUpForm

class SignUpView(CreateView):
    model = User
    form_class = SignUpForm 
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')