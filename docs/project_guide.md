# thiCodeDjango Project Documentation

## Project Structure

The thiCodeDjango project is a web application built with Django, organized using a modular architecture with clear separation of concerns. The project follows Django best practices with organization into distinct applications.

```
thiCodeDjango/
│
├── .env                    # Environment variables
├── .gitignore              # Files ignored by Git
├── README.md               # Main documentation
├── db.sqlite3              # SQLite database
├── manage.py               # Django management utility
├── requirements.txt        # Python dependencies
│
├── apps/                   # Directory containing applications
│   ├── accounts/           # User management and authentication
│   ├── chat/               # AI chat functionality
│   └── core/               # Core features and main pages
│
├── config/                 # Django project configuration
│   ├── __init__.py
│   ├── asgi.py             # ASGI configuration for async servers
│   ├── settings.py         # Project settings
│   ├── urls.py             # Main URL configuration
│   └── wsgi.py             # WSGI configuration for web servers
│
├── docs/                   # Additional documentation
│
└── venv/                   # Python virtual environment (not versioned)
```

## Project Configuration (config/)

The `config/` directory contains the main configuration files:

- **settings.py**: Contains all project settings, including:

  - Database configuration (SQLite)
  - Installed applications
  - Middleware
  - Authentication settings
  - Template configuration
  - Security parameters
  - Development and production configuration
  - Frontend integration (CORS, CSRF)
  - Email settings

- **urls.py**: Defines the main application routes:
  - Administrative routes (`/admin/`)
  - API routes (`/api/accounts/`, `/api/chat/`, `/api/csrf/`)
  - Traditional routes (`/accounts/`, `/chat/`, `/`)

## Applications (apps/)

The project is divided into 3 main applications:

### 1. Core Application (apps/core/)

Central application that provides basic functionality:

- Homepage
- CSRF token management for API calls
- Generic views and utilities

### 2. Accounts Application (apps/accounts/)

Handles authentication and user management:

- Custom user model (`User`) extending `AbstractUser`
- Profile functionality (bio, preferences stored as JSON)
- AI model preference management
- Authentication forms
- REST API for user management
- Authentication views (login, register, logout, profile)

### 3. Chat Application (apps/chat/)

Implements AI chat functionality:

- `Conversation` model for storing user conversations
- `Message` model for storing individual messages (user, assistant, system)
- Mistral AI client for generating responses
- REST API for:
  - Creating conversations
  - Sending messages
  - Retrieving conversation history
  - Deleting conversations

## Data Models

### User (accounts/models.py)

```python
class User(AbstractUser):
    bio = models.TextField(max_length=500, blank=True)
    date_modified = models.DateTimeField(auto_now=True)
    preferences = models.JSONField(default=dict, blank=True)
```

Extension of Django's standard user model with additional fields.

### Conversation (chat/models.py)

```python
class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    additional_data = models.JSONField(default=dict, blank=True)
```

Represents a conversation between a user and the AI assistant.

### Message (chat/models.py)

```python
class Message(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    )

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    additional_data = models.JSONField(default=dict, blank=True)
```

Represents an individual message in a conversation, with different possible roles.

## REST APIs

The project provides several API endpoints to enable interaction with the frontend:

### Accounts API

- User creation
- Authentication (login/logout)
- Profile management

### Chat API

- `GET /api/chat/conversations/` - List conversations
- `GET /api/chat/conversations/{id}/` - Conversation details
- `POST /api/chat/conversations/` - Create a new conversation
- `POST /api/chat/conversations/{id}/message/` - Send a message
- `DELETE /api/chat/conversations/{id}/` - Delete a conversation

## AI Integration

The project uses Mistral AI via a client class (`mistral_client.py`) that encapsulates calls to the Mistral API:

```python
class MistralClient:
    def generate_response(self, prompt):
        # Logic for calling Mistral API
        # ...
        return response
```

## Frontend Integration

The project is configured to work with a separate frontend (likely React):

- CORS configuration to allow cross-origin requests
- CSRF protection for API calls
- Templates for server-side rendering (hybrid mode)

## Development Workflow

1. Branch creation

   - feature/[feature-name]
   - bugfix/[bug-name]
   - hotfix/[hotfix-name]

2. Commits

   - Clear, descriptive messages
   - References to issues
   - One feature per commit

3. Tests
   - Mandatory unit tests
   - Integration testing for critical features
   - Performance testing for AI

## Security

Several security measures are in place:

- CSRF protection
- Session and token authentication
- Authentication-based permissions
- Restrictive CORS configuration for production

## Database

The project uses SQLite in development but could easily be configured to use PostgreSQL or MySQL in production.

## Production Configuration

Several settings are provided for production:

- Email sending configuration via SendGrid
- HTTPS settings for cookies
- Disabling DEBUG mode

## Technology Stack

- Django 4.x
- SQLite (development) / PostgreSQL (production)
- Mistral AI API integration
- CORS and CSRF protection
- JWT Authentication
