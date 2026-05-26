"""
Chatbot URL Configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_view, name='chatbot'),
    path('api/', views.chatbot_api, name='chatbot_api'),
    path('api/quick-reply/', views.chatbot_quick_reply, name='chatbot_quick_reply'),
    path('api/search/', views.chatbot_search_products, name='chatbot_search_products'),
    path('api/track-order/', views.chatbot_track_order, name='chatbot_track_order'),
    path('api/history/', views.chatbot_conversation_history, name='chatbot_conversation_history'),
]