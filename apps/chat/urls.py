from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'chat'

# Creating a router for the REST API
router = DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')

# API routes
urlpatterns = [
    # Main conversation routes
    path('api/conversations/', views.conversation_list_api, name='conversation_list_api'),
    path('api/conversations/<int:conversation_id>/', views.conversation_detail_api, name='conversation_detail_api'),
    
    # How to create a new conversation with a first message
    path('api/conversations/create/', views.create_conversation_api, name='create_conversation_api'),
    
    # Route to send a message in an existing conversation
    path('api/conversations/<int:conversation_id>/messages/', views.send_message_api, name='send_message_api'),
    
    # Route to delete a conversation
    path('api/conversations/<int:conversation_id>/delete/', views.delete_conversation_api, name='delete_conversation_api'),
    
    # Include DRF router for other standard REST operations
    path('api/', include(router.urls)),
]