import asyncio
import logging

from quart import Quart
from quart_cors import cors
from quart_rate_limiter import RateLimiter
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from basic_log import log
from blueprints.api import api
from blueprints.jinja import jinja
from blueprints.websockets import ws
from config import env_vals
from discord_utils import discord_client

# https://pgjones.gitlab.io/quart/how_to_guides/websockets.html
# https://quart.palletsprojects.com/en/latest/tutorials/chat_tutorial.html#chat-tutorial
# https://pgjones.gitlab.io/quart/how_to_guides/request_body.html
# TODO:
# - package for deploy
# - paid for real time/dedicated deployment/rates
# - lambda based? probably not
# - load messages by api (instead of jinja)
# - cleaner embed js item
# - Search server/channel by name
# - Auto create channel if missing
# - Builtin keyword moderation (until discord works on bots)
#   - https://www.reddit.com/r/myautomod/wiki/rules/#wiki_profanity.2Fhate_speech.2Finsults.2Fetc.


app: Quart = Quart("Discomment", template_folder="templates", static_folder="static")
app = cors(app)
app.asgi_app = ProxyHeadersMiddleware(app.asgi_app, trusted_hosts=["127.0.0.1"])
rate_limiter: RateLimiter = RateLimiter(app)


@app.before_serving
async def before_serving():
    loop = asyncio.get_event_loop()
    await discord_client.login(env_vals["token"])
    loop.create_task(discord_client.connect())


app.register_blueprint(api)
app.register_blueprint(jinja)
app.register_blueprint(ws)


def main():
    log("quart started", logging.INFO, __name__)
    app.run(host=env_vals["host"], port=env_vals["port"], use_reloader=False)


if __name__ == "__main__":
    main()
