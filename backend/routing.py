from channels.routing import ProtocolTypeRouter, URLRouter
from chat.token_middleware import TokenAuthMiddlewareStack

import chat.routing

application = ProtocolTypeRouter(
    {
        "websocket": TokenAuthMiddlewareStack(
            URLRouter(
                chat.routing.websocket_urlpatterns,
            )
        )
    }
)
