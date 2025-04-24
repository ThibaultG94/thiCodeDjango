from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

app_name = 'accounts'  # Namespace for URLs

urlpatterns = [
    # Traditional frontend routes (Django templates)
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('settings/', views.user_settings, name='settings'),
    
    # API endpoints for the React frontend
    path('api/login/', views.api_login, name='api_login'),
    path('api/register/', views.api_register, name='api_register'),
    path('api/logout/', views.api_logout, name='api_logout'),
    path('current-user/', views.current_user, name='current_user'),
    path('settings/', views.update_preferences, name='api_settings'),
    path('api/reset-password/', views.request_password_reset, name='request_password_reset'),
    path('api/verify-reset-token/<str:token>/', views.verify_reset_token, name='verify_reset_token'),
    path('api/reset-password/confirm/', views.confirm_password_reset, name='confirm_password_reset'),
]