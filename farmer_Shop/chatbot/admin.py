"""
Chatbot Admin Configuration
"""
from django.contrib import admin
from .models import ChatConversation, ChatMessage, ChatIntent, QuickReply


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'user', 'created_at', 'updated_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('session_id', 'user__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'message_type', 'message', 'timestamp')
    list_filter = ('message_type', 'timestamp')
    search_fields = ('message', 'conversation__session_id')
    readonly_fields = ('timestamp',)


@admin.register(ChatIntent)
class ChatIntentAdmin(admin.ModelAdmin):
    list_display = ('name', 'action_type', 'priority', 'is_active')
    list_filter = ('is_active', 'priority')
    search_fields = ('name', 'patterns')
    fieldsets = (
        (None, {
            'fields': ('name', 'patterns', 'priority', 'is_active')
        }),
        ('Response', {
            'fields': ('response_template', 'action_type')
        }),
    )


@admin.register(QuickReply)
class QuickReplyAdmin(admin.ModelAdmin):
    list_display = ('label', 'key', 'action', 'order')
    list_filter = ('action',)
    search_fields = ('label', 'key')
    ordering = ('order',)