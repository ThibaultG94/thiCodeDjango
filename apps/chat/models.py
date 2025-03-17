from django.db import models
from django.conf import settings

class Conversation(models.Model):
    """Modèle représentant une conversation de chat"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title or 'Nouvelle conversation'} - {self.user.username}"
    
    class Meta:
        ordering = ['-updated_at']

class Message(models.Model):
    """Modèle représentant un message dans une conversation"""
    ROLE_CHOICES = (
        ('user', 'Utilisateur'),
        ('assistant', 'Assistant'),
        ('system', 'Système'),
    )
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # To store code extracts or structured data
    additional_data = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"Message de {self.role} dans {self.conversation}"
    
    class Meta:
        ordering = ['created_at']