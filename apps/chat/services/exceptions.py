"""Exceptions spécifiques aux services de chat"""

class ChatBaseException(Exception):
    """Exception de base pour les erreurs de chat"""
    pass

class InvalidConversationStateError(ChatBaseException):
    """Erreur levée quand une opération est invalide dans l'état actuel de la conversation"""
    pass

class MessageOrderingError(ChatBaseException):
    """Erreur levée quand il y a un problème avec l'ordre des messages"""
    pass

class InvalidMessageTypeError(ChatBaseException):
    """Erreur levée quand le type de message est invalide"""
    pass

class MistralAPIError(ChatBaseException):
    """Erreur levée quand il y a un problème avec l'API Mistral"""
    pass

class OrphanedMessageError(ChatBaseException):
    """Erreur levée quand un message est orphelin (sans parent valide)"""
    pass

class ConversationConflictError(ChatBaseException):
    """Erreur levée quand il y a un conflit dans l'état de la conversation"""
    pass
