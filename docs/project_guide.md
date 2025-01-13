# Project Guide

## Project structure

```
thiCodeAI/
├── apps/
│   ├── core/           # Main application
│   ├── accounts/       # User management
│   └── chat/          # Chat interface
├── config/            # Django configuration
├── templates/         # Global Django templates
├── static/           # Static Files
├── ai_service/       # FastAPI service
│   ├── app.py
│   ├── models/
│   └── utils/
└── docs/            # Documentation
```

## Development Guidelines

### Architecture

1. MVC pattern with Django

   - Models: Data and business logic
   - Views: Presentation logic
   - Templates : User interface

2. Separation of responsibilities
   - Django: Main application and user management
   - FastAPI: Isolated AI service
   - ChromaDB: Knowledge base management

### Frontend (Django Templates)

1. Template structure

   - Base template with reusable blocks
   - Modular components
   - Consistent theme system

2. CSS conventions
   - BEM for class naming
   - CSS variables for consistency
   - Mobile-first responsive design

### Backend

1. Code organization

   - Django applications separated by domain
   - Isolated services for complex logic
   - Using form validators

2. Database
   - Versioned migrations
   - Optimized indexes
   - Appropriate caching

### AI Service

1. Prompts management

   - Versioned prompts templates
   - Fallback system
   - Interaction logging

2. Optimization
   - Caching frequently asked questions
   - Spleen limitation
   - Performance monitoring

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

## Technology stack

- Django 4.x
- PostgreSQL
- FastAPI
- llama2
- ChromaDB
- Redis (cache)
- Nginx (production)
