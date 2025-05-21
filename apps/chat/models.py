from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError

class Conversation(models.Model):
    """Chat conversation model with metadata and state management"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted')
    ]
    
    # Base relations and fields
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(max_length=255, blank=True)
    
    # Metadata
    summary = models.TextField(blank=True, help_text='Automatic conversation summary')
    tags = models.JSONField(default=list, blank=True, help_text='List of tags associated with the conversation')
    category = models.CharField(max_length=50, blank=True, help_text='Conversation category')
    
    # Gestion d'état
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_pinned = models.BooleanField(default=False, help_text='Pin the conversation')
    last_message_at = models.DateTimeField(null=True, blank=True)
    message_count = models.PositiveIntegerField(default=0)
    
    # Champs temporels
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    
    # Données additionnelles
    additional_data = models.JSONField(default=dict, blank=True, help_text='Additional structured data')
    
    def clean(self):
        # Custom validation
        if self.status == 'archived' and not self.archived_at:
            raise ValidationError('An archived conversation must have an archive date')
    
    def save(self, *args, **kwargs):
        # Generate slug if not defined
        if not self.slug:
            self.slug = slugify(self.title) if self.title else 'nouvelle-conversation'
        
        # Only update message-related fields if the conversation already exists
        if self.pk:
            # Update message counter
            self.message_count = self.messages.count()
            
            # Update last_message_at
            last_message = self.messages.order_by('-created_at').first()
            if last_message:
                self.last_message_at = last_message.created_at
        
        self.clean()
        super().save(*args, **kwargs)
        
        # If this is a new conversation, update the slug with the ID
        if not self.slug or self.slug == 'nouvelle-conversation':
            self.slug = f'conversation-{self.pk}'
            super().save(update_fields=['slug'])
    
    def archive(self):
        """Archive the conversation"""
        from django.utils import timezone
        self.status = 'archived'
        self.archived_at = timezone.now()
        self.save()
    
    def restore(self):
        """Restore an archived conversation"""
        self.status = 'active'
        self.archived_at = None
        self.save()
    
    def __str__(self):
        return f"{self.title or 'Nouvelle conversation'} - {self.user.username} ({self.status})"
    
    class Meta:
        ordering = ['-updated_at']

class Message(models.Model):
    """Message model in a conversation with metadata"""
    
    ROLE_CHOICES = (
        ('user', 'Utilisateur'),
        ('assistant', 'Assistant'),
        ('system', 'Système'),
    )
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('sent', 'Envoyé'),
        ('delivered', 'Reçu'),
        ('error', 'Erreur')
    ]
    
    # Relations
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    
    # Content and metadata
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    content_type = models.CharField(max_length=50, default='text', help_text='Content type (text, code, markdown...)')
    
    # Gestion d'état
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_edited = models.BooleanField(default=False)
    edit_count = models.PositiveIntegerField(default=0)
    
    # Champs temporels
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Données additionnelles
    additional_data = models.JSONField(default=dict, blank=True, help_text='Additional structured data (code, citations...)')
    metadata = models.JSONField(default=dict, blank=True, help_text='Technical metadata (tokens, response time...)')
    
    def save(self, *args, **kwargs):
        # Update edit_count if message is modified
        if self.id and self.is_edited:
            self.edit_count += 1
        
        super().save(*args, **kwargs)
        
        # Update parent conversation
        self.conversation.save()
    
    def mark_as_delivered(self):
        """Mark message as delivered"""
        from django.utils import timezone
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f"Message de {self.role} dans {self.conversation} ({self.status})"
    
    class Meta:
        ordering = ['created_at']