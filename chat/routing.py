from django.urls import re_path
from .consumers import SalaConsumer


websocket_urlpatterns = [
    re_path(r'ws/chat/sala/$', SalaConsumer.as_asgi()),
]