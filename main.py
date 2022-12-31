import asyncio

from quart import Quart

from blueprints.api import api
from blueprints.jinja import jinja
from blueprints.websockets import ws
from config import env_vals
from discord_utils import discord_client

# https://pgjones.gitlab.io/quart/how_to_guides/websockets.html
# https://quart.palletsprojects.com/en/latest/tutorials/chat_tutorial.html#chat-tutorial
# https://pgjones.gitlab.io/quart/how_to_guides/request_body.html
# TODO:
# - Rate Limit
# - Re-architect
# - package for deploy
# - paid for real time/dedicated deployment/rates
# - lambda based?
# - load messages by api (instead of jinja)
# - cleaner embed js item
# - Search server/channel by name
# - Auto create channel if missing


app = Quart(__name__, template_folder="templates", static_folder="static")


@app.before_serving
async def before_serving():
    loop = asyncio.get_event_loop()
    await discord_client.login(env_vals["token"])
    loop.create_task(discord_client.connect())

app.register_blueprint(api)
app.register_blueprint(jinja)
app.register_blueprint(ws)


def main():
    print("quart started")
    app.run()


if __name__ == "__main__":
    main()
