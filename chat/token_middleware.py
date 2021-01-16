from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

from knox.models import AuthToken as Token
from urllib.parse import parse_qs


@database_sync_to_async
def get_user(scope):
    print(scope["headers"])
    headers = dict(scope["headers"])
    if b"authorization" in headers:
        try:
            token_name, token_key = headers[b"authorization"].decode().split()
            if token_name == "Token":
                token = Token.objects.get(token_key=token_key)
                return token.user
        except Token.DoesNotExist:
            return AnonymousUser()
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