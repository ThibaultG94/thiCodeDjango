from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, views, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .services import ConversationService, MistralService, MessageService
from .exceptions import (
    ChatBaseException,
    InvalidConversationStateError,
    MessageOrderingError,
    OrphanedMessageError,
    ConversationConflictError,
    AIServiceError
)

class ConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing conversations with error handling"""
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']  # Méthodes HTTP autorisées
    
    def handle_exception(self, exc):
        """Custom exception handling for chat-specific errors"""
        if isinstance(exc, ChatBaseException):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)

    def get_queryset(self):
        status = self.request.query_params.get('status', 'active')
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        
        return ConversationService.get_user_conversations(
            user=self.request.user,
            status=status,
            category=category,
            search_query=search
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new conversation with initial message"""
        initial_message = request.data.get('initial_message')
        if not initial_message:
            return Response(
                {'error': 'initial_message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Créer la conversation avec un titre temporaire
                conversation = ConversationService.create_conversation(
                    user=request.user,
                    title=request.data.get('title') or initial_message[:50] + '...'
                )
                
                # Créer le message initial
                user_message = ConversationService.add_message_to_conversation(
                    conversation=conversation,
                    content=initial_message,
                    role='user',
                    content_type='text'
                )
                
                # Générer la réponse Mistral
                from .mistral_client import MistralClient
                client = MistralClient()
                try:
                    ai_response = client.generate_response(initial_message)
                    
                    # Créer le message AI
                    ai_message = ConversationService.add_message_to_conversation(
                        conversation=conversation,
                        content=ai_response,
                        role='assistant',
                        parent_message=user_message,
                        content_type='text'
                    )
                except Exception as e:
                    # En cas d'erreur avec Mistral, on continue quand même
                    print(f"Erreur Mistral: {str(e)}")
                
                # Récupérer la conversation mise à jour avec le message
                conversation.refresh_from_db()
                serializer = self.get_serializer(conversation)
                
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
        except Exception as e:
            return self.handle_exception(e)
    
    @action(detail=True, methods=['get', 'post'])
    def messages(self, request, pk=None):
        """Get all messages or add a new message to the conversation"""
        conversation = self.get_object()
        
        if request.method == 'GET':
            messages = conversation.messages.all().order_by('created_at')
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data)
        
        # POST - Add new message
        content = request.data.get('content')
        if not content:
            return Response(
                {'error': 'content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Add user message with transaction
            with transaction.atomic():
                # Créer le message utilisateur
                user_message = ConversationService.add_message_to_conversation(
                    conversation=conversation,
                    content=content,
                    role='user',
                    content_type='text'
                )
                
                # Retourner immédiatement le message utilisateur
                return Response({
                    'user_message': MessageSerializer(user_message).data,
                    'status': 'pending'
                }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return self.handle_exception(e)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a conversation with error handling"""
        conversation = self.get_object()
        try:
            conversation = ConversationService.archive_conversation(conversation)
            return Response(self.get_serializer(conversation).data)
        except (InvalidConversationStateError, ConversationConflictError) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore an archived conversation with error handling"""
        conversation = self.get_object()
        try:
            conversation = ConversationService.restore_conversation(conversation)
            return Response(self.get_serializer(conversation).data)
        except InvalidConversationStateError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def update_metadata(self, request, pk=None):
        """Update conversation metadata with error handling"""
        conversation = self.get_object()
        try:
            conversation = ConversationService.update_conversation_metadata(
                conversation=conversation,
                summary=request.data.get('summary'),
                category=request.data.get('category'),
                tags=request.data.get('tags'),
                is_pinned=request.data.get('is_pinned')
            )
            return Response(self.get_serializer(conversation).data)
        except (InvalidConversationStateError, ValidationError) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], url_path='messages/(?P<message_id>[^/.]+)/status')
    def message_status(self, request, pk=None, message_id=None):
        """Check the status of a message and get AI response if available"""
        conversation = self.get_object()
        try:
            # Récupérer le message utilisateur
            user_message = get_object_or_404(conversation.messages, id=message_id)
            
            # Vérifier si une réponse AI existe
            ai_message = conversation.messages.filter(
                parent_message=user_message,
                role='assistant'
            ).first()
            
            if ai_message:
                return Response({
                    'status': 'completed',
                    'ai_message': MessageSerializer(ai_message).data
                })
            
            # Si pas de réponse AI, générer une
            try:
                from .mistral_client import MistralClient
                client = MistralClient()
                ai_response = client.generate_response(user_message.content)
                
                # Créer le message AI
                ai_message = ConversationService.add_message_to_conversation(
                    conversation=conversation,
                    content=ai_response,
                    role='assistant',
                    parent_message=user_message,
                    content_type='text'
                )
                
                return Response({
                    'status': 'completed',
                    'ai_message': MessageSerializer(ai_message).data
                })
                
            except Exception as e:
                # En cas d'erreur avec Mistral
                user_message.metadata['error'] = str(e)
                user_message.save()
                return Response({
                    'status': 'error',
                    'error': str(e)
                })
            
        except Exception as e:
            return self.handle_exception(e)


class AskMistralView(views.APIView):
    """Vue pour interroger Mistral AI"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        message = request.data.get('message')
        if not message:
            return Response(
                {'error': 'message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Appeler Mistral et obtenir la réponse
            from .mistral_client import MistralClient
            client = MistralClient()
            response = client.generate_response(message)
            
            return Response({
                'response': response
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get', 'post'])
    def messages(self, request, pk=None):
        """Get all messages or add a new message to the conversation"""
        conversation = self.get_object()
        
        if request.method == 'GET':
            messages = conversation.messages.all()
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data)
        
        # POST method
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Add user message with transaction
            with transaction.atomic():
                user_message = ConversationService.add_message_to_conversation(
                    conversation=conversation,
                    content=request.data.get('content'),
                    role='user',
                    content_type='text'
                )
                
                return Response(
                    MessageSerializer(user_message).data,
                    status=status.HTTP_201_CREATED
                )
        except Exception as e:
            return self.handle_exception(e)