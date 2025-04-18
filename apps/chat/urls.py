from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.conversation_list, name='conversation_list'),
    path('nouvelle/', views.new_conversation, name='new'),
    path('creer/', views.create_conversation, name='create_conversation'),
    path('<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('<int:conversation_id>/envoyer/', views.send_message, name='send_message'),
    path('<int:conversation_id>/supprimer/', views.delete_conversation, name='delete_conversation'),
]

router = DefaultRouter()
router.register(r'api/conversations', views.ConversationViewSet, basename='api_conversation')

urlpatterns = [
    path('', include(router.urls)),
]