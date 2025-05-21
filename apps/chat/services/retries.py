"""Fonctions de retry pour la gestion des erreurs"""
import time
from functools import wraps
from typing import Optional, List

from django.db import transaction
from ..models import Message, Conversation
from .exceptions import OrphanedMessageError

def retry_on_error(max_retries: int = 3, delay: float = 0.1):
    """Décorateur pour réessayer une opération en cas d'erreur"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator

def recover_orphaned_messages(conversation: Conversation) -> List[Message]:
    """Récupère les messages orphelins d'une conversation"""
    with transaction.atomic():
        # Chercher les messages sans parent qui devraient en avoir un
        orphaned_messages = Message.objects.filter(
            conversation=conversation,
            parent__isnull=False
        ).select_related('parent')
        
        recovered = []
        for message in orphaned_messages:
            try:
                # Vérifier si le parent existe toujours
                if not message.parent:
                    message.parent = None
                    message.save()
                    recovered.append(message)
            except Message.DoesNotExist:
                message.parent = None
                message.save()
                recovered.append(message)
        
        return recovered
