"""Service pour gérer les messages"""
from django.utils import timezone
from ..models import Message

class MessageService:
    """Service pour gérer les messages"""
    
    @staticmethod
    def create_message(conversation, content, role='user', content_type='text', metadata=None):
        """Crée un nouveau message"""
        message = Message.objects.create(
            conversation=conversation,
            content=content,
            role=role,
            content_type=content_type,
            metadata=metadata or {}
        )
        return message
    
    @staticmethod
    def mark_as_delivered(message):
        """Marque un message comme délivré"""
        message.status = 'delivered'
        message.delivered_at = timezone.now()
        message.save()
