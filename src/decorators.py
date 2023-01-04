# https://stackoverflow.com/questions/71260887/how-to-use-api-key-authentication-with-quart-api
from functools import wraps
from typing import Callable, Any

from quart import has_request_context, has_websocket_context, request, websocket, current_app
from sqlalchemy import Table
from werkzeug.exceptions import Unauthorized

from auth import auth_store, APIKeyModel
from auth.apikey import APIKeyData
from auth.authutils import create_hash, verify_hash, verify_hosts
from sqlite import GenericQuery


def apikey_required() -> Callable:
    """A decorator to restrict route access to requests with an API key.

    This should be used to wrap a route handler (or view function) to
    enforce that only api key authenticated requests can access it. The
    key value is configurable via the app configuration with API_KEY key
    used by default. Note that it is important that this decorator be
    wrapped by the route decorator and not vice, versa, as below.

    .. code-block:: python

        @app.route('/')
        @api_key_required()
        async def index():
            ...

    If the request is not authenticated a
    `werkzeug.exceptions.Unauthorized` exception will be raised.

    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if has_request_context():
                api_key: str = request.headers.get("Authorization").split(" ")[1]
            elif has_websocket_context():
                api_key: str = websocket.headers.get("Authorization").split(" ")[1]
            else:
                raise RuntimeError("Not used in a valid request/websocket context")

            hashed: str = create_hash(api_key, apikey=True)

            auth_table: Table = auth_store.get_table(APIKeyModel.tablename())
            query: GenericQuery = APIKeyModel.fetch_by_hash(auth_table, hashed)
            record: APIKeyModel = auth_store.fetch_first_entity(query)

            if record is None:
                raise Unauthorized("API Key not found")

            record_data: APIKeyData = APIKeyData(**record.kvs)

            if not verify_hash(api_key, record_data.hash):
                raise Unauthorized("API Key not verified")
            if not verify_hosts(request.remote_addr, record_data.allowed_hosts):
                raise Unauthorized("Client Host not allowed")

            return await current_app.ensure_async(func)(*args, **kwargs)

        return wrapper

    return decorator
