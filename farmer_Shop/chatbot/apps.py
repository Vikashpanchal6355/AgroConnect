"""
Chatbot App Configuration
"""
from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'
    verbose_name = 'Advanced Chatbot'

    def ready(self):
        # Initialize chatbot data on app startup
        pass