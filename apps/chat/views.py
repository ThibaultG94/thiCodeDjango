from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import ConversationSerializer, MessageSerializer
from .models import Conversation, Message

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import json

# API to list all conversations
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_list_api(request):
    conversations = Conversation.objects.filter(user=request.user)
    serializer = ConversationSerializer(conversations, many=True)
    return Response(serializer.data)

# API for conversation details
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_detail_api(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    serializer = ConversationSerializer(conversation)
    return Response(serializer.data)

# API for creating a new conversation with a first message
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_conversation_api(request):
    message = request.data.get('message', '').strip()
    ai_model = request.data.get('ai_model', 'mistral')
    
    if not message:
        return Response(
            {'error': 'Message content is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create conversation
    conversation = Conversation.objects.create(
        user=request.user,
        title="New Conversation",
        additional_data={'ai_model': ai_model}
    )
    
    # Create user message
    user_message = Message.objects.create(
        conversation=conversation,
        role='user',
        content=message
    )
    
    # Generate AI response
    try:
        from .mistral_client import MistralClient
        client = MistralClient()
        
        ai_response = client.generate_response(f"""
        You are ThiCodeAI, a web development assistant.
        User asks: {message}
        Respond clearly and helpfully.
        """)
        
        # Create AI message
        ai_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=ai_response
        )
        
        # Update conversation title based on first message
        if len(message) > 50:
            conversation.title = message[:47] + "..."
        else:
            conversation.title = message
        conversation.save()
        
        # Return the complete conversation with messages
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        # Create error message if AI call fails
        Message.objects.create(
            conversation=conversation,
            role='system',
            content=f"Error generating response: {str(e)}"
        )
        
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# API for sending a message in an existing conversation
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message_api(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    
    message_content = request.data.get('message')
    selected_model = request.data.get('model', 'mistral')
    
    if not message_content:
        return Response(
            {'error': 'Message content is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Save user message
    user_message = Message.objects.create(
        conversation=conversation,
        role='user',
        content=message_content
    )
    
    # Generate AI response
    try:
        # Update model preference for this conversation
        additional_data = conversation.additional_data or {}
        additional_data['ai_model'] = selected_model
        conversation.additional_data = additional_data
        conversation.save()
        
        # Generate response with selected model
        from .mistral_client import MistralClient
        client = MistralClient()
        
        ai_response = client.generate_response(f"""
        You are ThiCodeAI, a web development assistant.
        User asks: {message_content}
        Respond clearly and helpfully.
        """)
        
        # Save AI message
        ai_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=ai_response
        )
        
        # Return both messages
        return Response({
            'user_message': MessageSerializer(user_message).data,
            'ai_message': MessageSerializer(ai_message).data
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# API for deleting a conversation
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_conversation_api(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    conversation.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    @action(detail=True, methods=['post'])
    def messages(self, request, pk=None):
        """Ajouter un message à la conversation"""
        conversation = self.get_object()
        
        # Check required data
        if 'message' not in request.data:
            return Response(
                {'error': 'Message content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user message
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=request.data['message']
        )
        
        # Generate AI response
        model = request.data.get('model', 'mistral')
        
        try:
            # Reuse existing Mistral client
            from .mistral_client import MistralClient
            client = MistralClient()
            
            ai_response = client.generate_response(f"""
            You are ThiCodeAI, a web development assistant.
            User asks: {request.data['message']}
            Respond clearly and helpfully.
            """)
            
            # Create AI message
            ai_message = Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=ai_response
            )
            
            # Update conversation timestamp
            conversation.save()
            
            return Response({
                'user_message': MessageSerializer(user_message).data,
                'ai_message': MessageSerializer(ai_message).data
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )