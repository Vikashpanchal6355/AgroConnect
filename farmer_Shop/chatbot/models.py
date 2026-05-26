"""
Advanced Chatbot for AgroConnect
Provides intelligent responses for product inquiries, order tracking, and agricultural support
"""
from django.db import models
from django.contrib.auth.models import User


class ChatConversation(models.Model):
    """Stores chat conversation sessions"""
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Chat {self.session_id}"


class ChatMessage(models.Model):
    """Stores individual chat messages"""
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('bot', 'Bot'),
        ('system', 'System'),
    ]
    
    conversation = models.ForeignKey(ChatConversation, related_name='messages', on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(null=True, blank=True, help_text="Additional data like suggested actions, quick replies")
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.message_type}: {self.message[:50]}"


class ChatIntent(models.Model):
    """Defines chatbot intents for NLU"""
    name = models.CharField(max_length=100, unique=True)
    patterns = models.TextField(help_text="Comma-separated keywords/patterns")
    response_template = models.TextField()
    action_type = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., search_products, track_order")
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Chat Intents"
        ordering = ['-priority']
    
    def __str__(self):
        return self.name


class QuickReply(models.Model):
    """Pre-defined quick reply buttons"""
    key = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    response = models.TextField()
    action = models.CharField(max_length=50, blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.label