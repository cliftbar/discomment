import json
import logging
from asyncio import sleep

from quart import websocket, Blueprint

from auth.authutils import Scopes
from basic_log import log
from config import account_conf
from decorators import apikey_required
from discord_utils import DiscommentClient
from msg_queue import msg_queue
from msg_queue.utils import queue_get_many

ws: Blueprint = Blueprint("ws", __name__)


@ws.websocket("/ws/comments")
@apikey_required(scopes=[Scopes.ACCOUNT_READ])
async def comment_socket():
    while True:
        log("ws alive", logging.DEBUG, __name__)
        await sleep(account_conf.websocket_sleep_s)
        msgs: list = queue_get_many(msg_queue)
        await websocket.send(json.dumps([DiscommentClient.msg_to_json(m) for m in msgs]))
