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

    class Meta:
        db_table = 'users' # Explicit name in database
