from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'chat'

# Creating a router for the REST API
router = DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')

# Les URLs sont gérées automatiquement par le routeur DRF
# Le ViewSet expose les endpoints suivants :
# - GET /api/conversations/ : Liste des conversations
# - POST /api/conversations/ : Créer une conversation
# - GET /api/conversations/{id}/ : Détails d'une conversation
# - PUT/PATCH /api/conversations/{id}/ : Mettre à jour une conversation
# - DELETE /api/conversations/{id}/ : Supprimer une conversation
# - POST /api/conversations/{id}/messages/ : Ajouter un message
# - POST /api/conversations/{id}/archive/ : Archiver une conversation
# - POST /api/conversations/{id}/restore/ : Restaurer une conversation
# - POST /api/conversations/{id}/update_metadata/ : Mettre à jour les métadonnées

urlpatterns = [
    path('api/', include(router.urls)),
]