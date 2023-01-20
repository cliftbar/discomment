import asyncio
import logging

from quart import Quart
from quart_cors import cors
from quart_rate_limiter import RateLimiter
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from basic_log import log
from blueprints.api import api
from blueprints.jinja import jinja
from blueprints.sse import sse
from blueprints.websockets import ws
from config import server_conf
from discord_utils import discord_client

# TODO:
# - package for deploy
# - paid for real time/dedicated deployment/rates
# - cleaner embed js snippet
# - Search server/channel by name
# - Auto create a channel if one isn't set on websocket connection, requires a channel name/id param
# - store account server id, and how to ensure channel is in server
# - add to a project, godin or pixelizor
# - schemas/api docs https://github.com/pgjones/quart-schema,
# - tests
# - user data and account config can be the same object I think?? or nearly so?
# TODO: discord/queue/event/websocket part needs to be re-architected


app: Quart = Quart("Discomment", template_folder="templates", static_url_path="/", static_folder="static")
app = cors(app, allow_origin=server_conf.cors_allowed_origin)
app.asgi_app = ProxyHeadersMiddleware(app.asgi_app, trusted_hosts=server_conf.trusted_proxies)
rate_limiter: RateLimiter = RateLimiter(app)


@app.before_serving
async def before_serving():
    loop = asyncio.get_event_loop()
    await discord_client.login(server_conf.bot_token)
    loop.create_task(discord_client.connect())


app.register_blueprint(api)
app.register_blueprint(ws)
app.register_blueprint(sse)
if server_conf.static_routes_enabled:
    app.register_blueprint(jinja)


def main():
    log("quart started", logging.INFO, __name__)
    app.run(host=server_conf.host, port=server_conf.port, use_reloader=False)


if __name__ == "__main__":
    main()
