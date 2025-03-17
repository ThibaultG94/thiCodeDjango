from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Conversation, Message
from django.views.decorators.http import require_POST
import json

@login_required
def conversation_list(request):
    """Vue pour lister toutes les conversations de l'utilisateur courant"""
    conversations = Conversation.objects.filter(user=request.user)
    return render(request, 'chat/conversation_list.html', {'conversations': conversations})

@login_required
def new_conversation(request):
    """Créer une nouvelle conversation et rediriger vers celle-ci"""
    conversation = Conversation.objects.create(user=request.user, title="Nouvelle Conversation")
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
        
        if not message_content:
            return JsonResponse({'error': 'Le contenu du message est requis'}, status=400)
        
        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=message_content
        )
        
        # TODO: This is where you'll integrate your AI department
        # For now, we're just sending back a simple echo
        ai_response = f"Echo: {message_content}"
        
        # Save the AI response
        ai_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=ai_response
        )
        
        # Update conversation timestamp
        conversation.save()  # This triggers the update of updated_at
        
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