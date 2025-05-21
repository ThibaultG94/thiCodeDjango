"""Locks pour la gestion de la concurrence"""
from contextlib import contextmanager
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT

@contextmanager
def conversation_lock(conversation_id: int, timeout: int = DEFAULT_TIMEOUT):
    """Lock pour les opérations sur une conversation"""
    lock_id = f'conversation_lock_{conversation_id}'
    try:
        # Acquérir le lock
        acquired = cache.add(lock_id, 'locked', timeout)
        if not acquired:
            raise Exception(f'Could not acquire lock for conversation {conversation_id}')
        yield
    finally:
        # Relâcher le lock
        cache.delete(lock_id)

@contextmanager
def message_lock(conversation_id: int, timeout: int = DEFAULT_TIMEOUT):
    """Lock pour les opérations sur les messages d'une conversation"""
    lock_id = f'message_lock_{conversation_id}'
    try:
        # Acquérir le lock
        acquired = cache.add(lock_id, 'locked', timeout)
        if not acquired:
            raise Exception(f'Could not acquire lock for messages in conversation {conversation_id}')
        yield
    finally:
        # Relâcher le lock
        cache.delete(lock_id)
