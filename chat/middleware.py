from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

@database_sync_to_async
def get_user_from_token(token_key):
    try:
        from rest_framework_simplejwt.tokens import AccessToken
        from django.contrib.auth import get_user_model
        Usuario = get_user_model()
        access_token = AccessToken(token_key)
        user_id = access_token['user_id']
        return Usuario.objects.get(id=user_id)
    except ImportError:
        pass
    except Exception:
        pass

    return AnonymousUser()


class QueryParamAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token_key = query_params.get("token")

        if token_key:
            token_key = token_key[0]
            scope["user"] = await get_user_from_token(token_key)

        return await self.inner(scope, receive, send)
