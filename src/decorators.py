# https://stackoverflow.com/questions/71260887/how-to-use-api-key-authentication-with-quart-api
import logging
from functools import wraps
from typing import Callable, Any

from quart import has_request_context, has_websocket_context, request, websocket, current_app, g
from sqlalchemy import Table
from werkzeug.exceptions import Unauthorized, Forbidden

from auth import auth_store, UserModel
from auth.authutils import create_hash, verify_hash, verify_hosts, verify_scopes, Scopes
from auth.user import APIKeyData
from basic_log import log
from sqlite import GenericQuery


def apikey_required(scopes: list[Scopes] = None) -> Callable:
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
                ctx = request

            elif has_websocket_context():
                ctx = websocket
            else:
                raise RuntimeError("Not used in a valid request/websocket context")
            api_key_header: str = ctx.headers.get("Authorization")
            api_key_arg: str = ctx.args.get("auth")
            if (api_key_header is None or "Bearer " not in api_key_header) and api_key_arg is None:
                raise Unauthorized("API Key not provided")

            api_key: str = api_key_arg if api_key_arg is not None else api_key_header.split(" ")[1]

            hashed: str = create_hash(api_key, apikey=True)

            auth_table: Table = auth_store.get_table(UserModel.tablename())
            query: GenericQuery = UserModel.fetch_by_hash(auth_table, hashed)
            record: UserModel = auth_store.fetch_first_entity(query)

            if record is None:
                raise Unauthorized("API Key not recognized")

            g.user = record
            g.api_key = api_key
            g.api_key_hash = hashed

            log(str(ctx.headers), logging.DEBUG)

            api_key_data: APIKeyData = record.apikey_data_by_hash(hashed)

            if not verify_hash(api_key, api_key_data.hash):
                raise Forbidden("API Key not verified")
            if not verify_hosts(ctx.remote_addr, api_key_data.allowed_hosts):
                raise Forbidden("Client Host not allowed")
            if not verify_scopes(api_key_data.scopes, scopes):
                raise Forbidden("API Key has insufficient permissions")

            return await current_app.ensure_async(func)(*args, **kwargs)

        return wrapper

    return decorator
