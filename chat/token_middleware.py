from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

from urllib.parse import parse_qs
from knox.auth import TokenAuthentication
from knox.models import AuthToken as Token


@database_sync_to_async
def get_user(scope):
    try:
        token_key = parse_qs(scope["query_string"].decode("utf8"))["token"][0]
        auther = TokenAuthentication()
        user, _ = auther.authenticate_credentials(token_key.encode())
        return user
    except Token.DoesNotExist:
        return AnonymousUser()
    except KeyError:
        return AnonymousUser()


class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return TokenAuthMiddlewareInstance(scope, self)


class TokenAuthMiddlewareInstance:
    def __init__(self, scope, middleware):
        self.scope = dict(scope)
        self.inner = middleware.inner

    async def __call__(self, receive, send):
        self.scope["user"] = await get_user(self.scope)
        return await self.inner(self.scope, receive, send)


TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(AuthMiddlewareStack(inner))