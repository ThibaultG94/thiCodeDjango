"""Service pour interagir avec Mistral AI"""
import os
import requests
from django.conf import settings

class MistralService:
    """Service pour interagir avec l'API Mistral"""
    
    @staticmethod
    def ask(message: str) -> str:
        """Envoie une requête à Mistral et retourne la réponse"""
        # TODO: Implémenter l'appel réel à Mistral
        # Pour l'instant, on simule une réponse
        return f"Je suis Mistral AI. Vous avez dit : {message}"
