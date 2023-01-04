import json
import logging
from asyncio import sleep
from typing import Optional

from discord import Message
from quart import websocket, Blueprint, g

from auth import UserModel
from auth.authutils import Scopes
from basic_log import log
from decorators import apikey_required
from discord_utils import DiscommentClient
from msg_queue import channel_msg_manager

ws: Blueprint = Blueprint("ws", __name__)


@ws.websocket("/ws/comments")
@apikey_required(scopes=[Scopes.ACCOUNT_READ])
async def comment_socket():
    user: UserModel = g.get("user")
    channel_id: int = int(websocket.args["channelId"])
    msgs: list = channel_msg_manager.pop(channel_id=channel_id)
    last_msg: Optional[Message] = msgs[-1] if 0 < len(msgs) else None

    while True:
        log("ws alive", logging.DEBUG, __name__)
        await sleep(user.user_data.websocket_sleep_s)
        last_msg = msgs[-1] if 0 < len(msgs) else last_msg
        log(last_msg.content if last_msg is not None else "None", logging.DEBUG, __name__)
        msgs = channel_msg_manager.pop(channel_id=channel_id, as_of=last_msg)
        await websocket.send(json.dumps([DiscommentClient.msg_to_json(m) for m in msgs]))
