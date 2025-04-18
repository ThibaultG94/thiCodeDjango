from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Conversation, Message
from django.views.decorators.http import require_POST
import json

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import ConversationSerializer, MessageSerializer
from .models import Conversation, Message

@login_required
def conversation_list(request):
    """Vue pour lister toutes les conversations de l'utilisateur courant"""
    conversations = Conversation.objects.filter(user=request.user)
    return render(request, 'chat/conversation_list.html', {'conversations': conversations})

@login_required
def new_conversation(request):
    """Afficher la page pour démarrer une nouvelle conversation"""
    return render(request, 'chat/new_conversation.html')

@login_required
@require_POST
def create_conversation(request):
    """Créer une nouvelle conversation avec le premier message"""
    message = request.POST.get('message', '').strip()
    ai_model = request.POST.get('ai_model', 'mistral')
    
    if not message:
        # Redirect with error message if message is empty
        messages.error(request, "Le message ne peut pas être vide.")
        return redirect('chat:new')
    
    # Creating conversation
    conversation = Conversation.objects.create(
        user=request.user,
        title="Nouvelle Conversation"
    )
    
    # Store selected model in additional data
    conversation.additional_data = {'ai_model': ai_model}
    conversation.save()
    
    # Create the first user message
    user_message = Message.objects.create(
        conversation=conversation,
        role='user',
        content=message
    )
    
    # Get the answer from the AI
    try:
        from .mistral_client import MistralClient
        client = MistralClient()
        
        ai_response = client.generate_response(f"""
        Tu es ThiCodeAI, un assistant de développement web.
        L'utilisateur te demande: {message}
        Réponds de manière claire et utile.
        """)
        
        # Create the AI message
        Message.objects.create(
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
        
    except Exception as e:
        # Create an error message if the AI call fails
        Message.objects.create(
            conversation=conversation,
            role='system',
            content=f"Erreur lors de la génération de la réponse: {str(e)}"
        )
    
    return redirect('chat:conversation_detail', conversation_id=conversation.id)

@login_required
def conversation_detail(request, conversation_id):
    """Voir une conversation spécifique"""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    messages = conversation.messages.all()
    return render(request, 'chat/conversation_detail.html', {
        'conversation': conversation,
        'messages': messages
    })

@login_required
@require_POST
def send_message(request, conversation_id):
    """Endpoint API pour envoyer un nouveau message"""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    
    try:
        data = json.loads(request.body)
        message_content = data.get('message')
        selected_model = data.get('model', 'mistral')  # Retrieve the selected model
        
        # Update the template used for this conversation
        additional_data = conversation.additional_data or {}
        additional_data['ai_model'] = selected_model
        conversation.additional_data = additional_data
        conversation.save()
        
        if not message_content:
            return JsonResponse({'error': 'Le contenu du message est requis'}, status=400)
        
        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=message_content
        )
        
        # Generate response based on selected model
        if selected_model == 'mistral':
            from .mistral_client import MistralClient
            client = MistralClient()
            ai_response = client.generate_response(f"""
            Tu es ThiCodeAI, un assistant de développement web.
            L'utilisateur te demande: {message_content}
            Réponds de manière claire et utile.
            """)
        else:
            # Fallback if the model is not recognized
            ai_response = "Je ne peux pas utiliser ce modèle pour le moment. Veuillez choisir Mistral."
        
        # Save answer
        ai_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=ai_response
        )
        
        # Update timestamp
        conversation.save()
        
        return JsonResponse({
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'created_at': user_message.created_at.isoformat()
            },
            'ai_message': {
                'id': ai_message.id,
                'content': ai_message.content,
                'created_at': ai_message.created_at.isoformat()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
def delete_conversation(request, conversation_id):
    """Supprimer une conversation spécifique"""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    
    if request.method == 'POST':
        conversation.delete()
        return redirect('chat:conversation_list')
    
    return render(request, 'chat/delete_confirmation.html', {
        'conversation': conversation
    })

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
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
            Tu es ThiCodeAI, un assistant de développement web.
            L'utilisateur te demande: {request.data['message']}
            Réponds de manière claire et utile.
            """)
            
            # Create wizard message
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