from quart import render_template, Blueprint, Response

from config import server_conf, account_conf
from dctypes import HTML

jinja: Blueprint = Blueprint("jinja", __name__, template_folder="templates")


@jinja.get("/")
async def index() -> HTML:
    return await render_template("html/home.html")


@jinja.get("/js/<path:template_id>")
async def get_js_template(template_id: str) -> Response:
    tmp: str = await render_template(f"js/{template_id}", host=server_conf.host, port=server_conf.port,
                                     apikey=server_conf.static_route_apikey, channelId=account_conf.comment_channel_id)
    return Response(tmp, mimetype='text/javascript')
