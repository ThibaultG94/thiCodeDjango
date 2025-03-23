from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Extension of Django's basic User model.
    Allows us to add custom fields.
    """

    bio = models.TextField(max_length=500, blank=True)
    date_modified = models.DateTimeField(auto_now=True)

    # Store user preferences (theme, AI settings, etc.)
    preferences = models.JSONField(default=dict, blank=True)
    
    # Default AI model preference
    @property
    def ai_model(self):
        return self.preferences.get('ai_model', 'llama2')
    
    @ai_model.setter
    def ai_model(self, model_name):
        preferences = self.preferences.copy()
        preferences['ai_model'] = model_name
        self.preferences = preferences
        self.save()

    class Meta:
        db_table = 'users' # Explicit name in database