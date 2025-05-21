from rest_framework.exceptions import APIException
from rest_framework import status


class ChatBaseException(APIException):
    """Base exception for chat application"""
    pass


class MessageCreationError(ChatBaseException):
    """Raised when there's an error creating a message"""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Error creating message'


class ConcurrentMessageError(MessageCreationError):
    """Raised when concurrent message creation is detected"""
    default_detail = 'Concurrent message creation detected'


class OrphanedMessageError(MessageCreationError):
    """Raised when a message becomes orphaned"""
    default_detail = 'Message has no valid parent conversation'


class InvalidConversationStateError(ChatBaseException):
    """Raised when attempting operations on conversations in invalid states"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid conversation state for this operation'


class MessageOrderingError(ChatBaseException):
    """Raised when message ordering constraints are violated"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Message ordering constraint violated'


class ConversationConflictError(ChatBaseException):
    """Raised when there's a conflict in conversation operations"""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Conversation operation conflict detected'


class AIServiceError(ChatBaseException):
    """Raised when there's an error with the AI service"""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'AI service error'


class RetryableError(ChatBaseException):
    """Base class for errors that can be retried"""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    max_retries = 3
    retry_delay = 1  # seconds
