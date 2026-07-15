import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django_asgi_app = get_asgi_application()

from chat.routing import websocket_urlpatterns
from chat.middleware import QueryParamAuthMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": QueryParamAuthMiddleware(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})