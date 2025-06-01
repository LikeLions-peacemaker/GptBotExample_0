# gptbot/urls.py
from django.urls import path
from .views import chatbot_api, chat_page

urlpatterns = [
    path('api/chat/', chatbot_api, name='chatbot_api'),
    path('chat/', chat_page, name='chat_page'),

]
