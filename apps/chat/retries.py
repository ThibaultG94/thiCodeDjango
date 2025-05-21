import time
from functools import wraps
from .exceptions import RetryableError, AIServiceError

def retry_on_error(max_retries=3, delay=1, retryable_exceptions=(RetryableError,)):
    """
    Decorator to retry operations on specific exceptions.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        retryable_exceptions: Tuple of exceptions that should trigger a retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
                    continue
                except Exception as e:
                    # Non-retryable exception
                    raise e
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


def recover_orphaned_messages(conversation):
    """
    Recover orphaned messages in a conversation.
    This happens when a message's parent is deleted or when message creation fails midway.
    """
    from .models import Message
    
    # Find messages with invalid parents
    orphaned_messages = Message.objects.filter(
        conversation=conversation,
        parent__isnull=False
    ).exclude(
        parent__conversation=conversation
    )
    
    # Reset their parent to None
    orphaned_messages.update(parent=None)
    
    return orphaned_messages


def handle_ai_service_error(func):
    """
    Decorator to handle AI service errors gracefully.
    Implements circuit breaker pattern to prevent cascade failures.
    """
    CIRCUIT_BREAKER_KEY = 'ai_service_circuit_breaker'
    ERROR_THRESHOLD = 5
    RESET_TIMEOUT = 300  # 5 minutes
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        from django.core.cache import cache
        
        # Check if circuit is open (service marked as down)
        error_count = cache.get(CIRCUIT_BREAKER_KEY, 0)
        if error_count >= ERROR_THRESHOLD:
            raise AIServiceError('AI service is temporarily unavailable')
        
        try:
            result = func(*args, **kwargs)
            # Reset error count on success
            if error_count > 0:
                cache.delete(CIRCUIT_BREAKER_KEY)
            return result
            
        except Exception as e:
            # Increment error count
            cache.set(
                CIRCUIT_BREAKER_KEY,
                error_count + 1,
                RESET_TIMEOUT
            )
            raise AIServiceError(str(e))
    
    return wrapper
