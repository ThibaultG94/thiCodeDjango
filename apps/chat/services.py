from django.utils.text import slugify
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from typing import Optional, List, Dict, Any

from .models import Conversation, Message
from .exceptions import (
    InvalidConversationStateError,
    MessageOrderingError,
    OrphanedMessageError,
    ConversationConflictError
)
from .locks import conversation_lock, message_lock
from .retries import retry_on_error, recover_orphaned_messages


class ConversationService:
    """Service class for managing chat conversations"""

    @staticmethod
    def create_conversation(user, title: Optional[str] = None, category: Optional[str] = None, 
                          tags: Optional[List[str]] = None) -> Conversation:
        """Create a new conversation with optional metadata"""
        with transaction.atomic():
            conversation = Conversation.objects.create(
                user=user,
                title=title or "New Conversation",
                category=category,
                tags=tags or []
            )
            return conversation

    @staticmethod
    @retry_on_error()
    def add_message_to_conversation(conversation: Conversation, content: str, role: str,
                                  parent_message: Optional[Message] = None,
                                  content_type: str = 'text',
                                  metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Add a new message to the conversation with concurrency control"""
        # Verify conversation state
        if conversation.status != 'active':
            raise InvalidConversationStateError(
                f'Cannot add message to {conversation.status} conversation'
            )
        
        # Verify parent message belongs to the same conversation
        if parent_message and parent_message.conversation_id != conversation.id:
            raise OrphanedMessageError('Parent message belongs to different conversation')
        
        with transaction.atomic():
            with message_lock(conversation.id):
                # Verify message ordering if it's a reply
                if parent_message:
                    latest_reply = parent_message.replies.order_by('-created_at').first()
                    if latest_reply and latest_reply.role == role:
                        raise MessageOrderingError(
                            f'Cannot add multiple consecutive messages with role {role}'
                        )
                
                message = Message.objects.create(
                    conversation=conversation,
                    content=content,
                    role=role,
                    parent=parent_message,
                    content_type=content_type,
                    metadata=metadata or {},
                    status='sent'
                )
                
                # Update conversation
                conversation.last_message_at = timezone.now()
                conversation.message_count = conversation.messages.count()
                conversation.save()
                
                return message

    @staticmethod
    def generate_title(conversation: Conversation) -> str:
        """Generate a title for the conversation based on its content"""
        # Get the first user message
        first_message = conversation.messages.filter(role='user').first()
        if first_message:
            # Use the first 50 characters of the first message
            title = first_message.content[:50]
            # Clean it up
            title = title.strip()
            if len(first_message.content) > 50:
                title += "..."
            return title
        return "New Conversation"

    @staticmethod
    def update_conversation_title(conversation: Conversation, title: Optional[str] = None) -> Conversation:
        """Update the conversation title, either with a provided title or by generating one"""
        if title is None:
            title = ConversationService.generate_title(conversation)
        
        conversation.title = title
        conversation.slug = slugify(title)
        conversation.save()
        return conversation

    @staticmethod
    def get_user_conversations(user, status: str = 'active', 
                             category: Optional[str] = None,
                             search_query: Optional[str] = None):
        """Get user conversations with optional filters"""
        queryset = Conversation.objects.filter(user=user, status=status)
        
        if category:
            queryset = queryset.filter(category=category)
        
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(summary__icontains=search_query) |
                Q(messages__content__icontains=search_query)
            ).distinct()
        
        return queryset

    @staticmethod
    def archive_conversation(conversation: Conversation) -> Conversation:
        """Archive a conversation with state validation"""
        with conversation_lock(conversation.id):
            if conversation.status == 'deleted':
                raise InvalidConversationStateError('Cannot archive deleted conversation')
            
            # Check for pending messages
            if conversation.messages.filter(status='pending').exists():
                raise ConversationConflictError('Cannot archive conversation with pending messages')
            
            conversation.archive()
            return conversation

    @staticmethod
    def restore_conversation(conversation: Conversation) -> Conversation:
        """Restore an archived conversation with state validation"""
        with conversation_lock(conversation.id):
            if conversation.status == 'deleted':
                raise InvalidConversationStateError('Cannot restore deleted conversation')
            
            # Recover any orphaned messages before restoration
            recover_orphaned_messages(conversation)
            
            conversation.restore()
            return conversation

    @staticmethod
    def update_conversation_metadata(conversation: Conversation,
                                   summary: Optional[str] = None,
                                   category: Optional[str] = None,
                                   tags: Optional[List[str]] = None,
                                   is_pinned: Optional[bool] = None) -> Conversation:
        """Update conversation metadata with concurrency control"""
        with conversation_lock(conversation.id):
            if conversation.status == 'deleted':
                raise InvalidConversationStateError('Cannot update deleted conversation')
            
            if summary is not None:
                conversation.summary = summary
            if category is not None:
                conversation.category = category
            if tags is not None:
                conversation.tags = tags
            if is_pinned is not None:
                conversation.is_pinned = is_pinned
            
            with transaction.atomic():
                conversation.save()
                return conversation


class MessageService:
    """Service class for managing chat messages"""

    @staticmethod
    def mark_message_delivered(message: Message) -> Message:
        """Mark a message as delivered"""
        message.mark_as_delivered()
        return message

    @staticmethod
    def edit_message(message: Message, new_content: str) -> Message:
        """Edit an existing message"""
        message.content = new_content
        message.is_edited = True
        message.save()
        return message

    @staticmethod
    def get_message_thread(message: Message) -> List[Message]:
        """Get all messages in a thread starting from the given message"""
        thread = []
        current = message
        
        # Get parent messages
        while current.parent:
            thread.insert(0, current.parent)
            current = current.parent
        
        # Add the current message
        thread.append(message)
        
        # Get child messages
        replies = message.replies.all().order_by('created_at')
        thread.extend(replies)
        
        return thread
