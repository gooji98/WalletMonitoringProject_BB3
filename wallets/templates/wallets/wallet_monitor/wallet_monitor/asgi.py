import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wallet_monitor.settings")

django_asgi_app = get_asgi_application()

import wallet_monitor.routing

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(wallet_monitor.routing.websocket_urlpatterns)
        ),
    }
)