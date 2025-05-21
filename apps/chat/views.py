from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Conversation
from .serializers import ConversationSerializer, MessageSerializer
from .services import ConversationService, MessageService
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
    
    def handle_exception(self, exc):
        """Custom exception handling for chat-specific errors"""
        if isinstance(exc, ChatBaseException):
            return Response(
                {'error': str(exc)},
                status=exc.status_code
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
        """Create a new conversation with error handling"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                conversation = ConversationService.create_conversation(
                    user=request.user,
                    title=serializer.validated_data.get('title'),
                    category=serializer.validated_data.get('category'),
                    tags=serializer.validated_data.get('tags', [])
                )
                
                return Response(
                    self.get_serializer(conversation).data,
                    status=status.HTTP_201_CREATED
                )
        except Exception as e:
            return self.handle_exception(e)
    
    @action(detail=True, methods=['post'])
    def messages(self, request, pk=None):
        """Add a message to the conversation with error handling"""
        conversation = self.get_object()
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Add user message with transaction
            with transaction.atomic():
                user_message = ConversationService.add_message_to_conversation(
                    conversation=conversation,
                    content=request.data['message'],
                    role='user',
                    content_type=request.data.get('content_type', 'text'),
                    metadata={'client_timestamp': request.data.get('timestamp')}
                )
                
                # Generate AI response
                try:
                    model = request.data.get('model', 'mistral')
                    from .mistral_client import MistralClient
                    client = MistralClient()
                    
                    start_time = timezone.now()
                    ai_response = client.generate_response(f"""
                    You are ThiCodeAI, a web development assistant.
                    User asks: {request.data['message']}
                    Respond clearly and helpfully.
                    """)
                    response_time = (timezone.now() - start_time).total_seconds()
                    
                    # Create AI message using service
                    ai_message = ConversationService.add_message_to_conversation(
                        conversation=conversation,
                        content=ai_response,
                        role='assistant',
                        parent_message=user_message,
                        content_type='text',
                        metadata={
                            'model': model,
                            'response_time': response_time
                        }
                    )
                    
                    # Update conversation title if it's the first message
                    if conversation.messages.count() <= 2:  # User message + AI response
                        ConversationService.update_conversation_title(conversation)
                    
                    return Response({
                        'user_message': MessageSerializer(user_message).data,
                        'ai_message': MessageSerializer(ai_message).data
                    })
                    
                except AIServiceError as e:
                    # Save user message even if AI fails
                    return Response({
                        'user_message': MessageSerializer(user_message).data,
                        'error': str(e)
                    }, status=e.status_code)
                
        except (InvalidConversationStateError, MessageOrderingError,
                OrphanedMessageError) as e:
            return Response(
                {'error': str(e)},
                status=e.status_code
            )
    
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
                status=e.status_code
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
                status=e.status_code
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
                status=status.HTTP_400_BAD_REQUEST if isinstance(e, ValidationError)
                else e.status_code
            )