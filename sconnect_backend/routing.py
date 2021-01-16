from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from chat.token_middleware import TokenAuthMiddlewareStack


import chat.routing

application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(
            URLRouter(
                chat.routing.websocket_urlpatterns,
            )
        )
    }
)
