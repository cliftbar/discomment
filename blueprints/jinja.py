import json

from quart import render_template, Blueprint, Response

from config import env_vals
from discord_utils import discord_client, DiscommentClient
from dctypes import HTML, JSON

jinja: Blueprint = Blueprint("jinja", __name__)


@jinja.get("/")
async def index() -> HTML:
    msgs: list = [message
                  async for message
                  in discord_client.get_channel(env_vals["comment_channel_id"]).history(limit=200)]
    contents: JSON = [json.dumps(DiscommentClient.msg_to_json(m)) for m in msgs]
    return await render_template("html/home.html", msgs=contents)


@jinja.get("/js/<template_id>")
async def get_js_template(template_id: str) -> Response:
    tmp: str = await render_template(f"js/{template_id}", host=env_vals["host"], port=env_vals["port"])
    return Response(tmp, mimetype='text/javascript')
