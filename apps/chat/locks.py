from django.core.cache import cache
from contextlib import contextmanager
from .exceptions import ConcurrentMessageError

LOCK_TIMEOUT = 30  # seconds
LOCK_WAIT_TIMEOUT = 5  # seconds


@contextmanager
def conversation_lock(conversation_id):
    """
    Context manager for locking conversation operations.
    Prevents concurrent modifications to the same conversation.
    """
    lock_id = f'conversation_lock_{conversation_id}'
    
    # Try to acquire the lock
    acquired = cache.add(lock_id, 'lock', LOCK_TIMEOUT)
    
    if not acquired:
        raise ConcurrentMessageError('Conversation is currently locked')
    
    try:
        yield
    finally:
        # Release the lock
        cache.delete(lock_id)


@contextmanager
def message_lock(conversation_id, message_id=None):
    """
    Context manager for locking message operations.
    Prevents concurrent message creation/modification.
    """
    if message_id:
        lock_id = f'message_lock_{conversation_id}_{message_id}'
    else:
        lock_id = f'message_creation_lock_{conversation_id}'
    
    # Try to acquire the lock
    acquired = cache.add(lock_id, 'lock', LOCK_TIMEOUT)
    
    if not acquired:
        raise ConcurrentMessageError('Message operation is currently locked')
    
    try:
        yield
    finally:
        # Release the lock
        cache.delete(lock_id)
