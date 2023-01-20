import json
import logging
from asyncio import sleep
from dataclasses import dataclass
from typing import Optional

from discord import Message
from quart import Blueprint, abort, make_response, request, g

from auth import UserModel
from auth.authutils import Scopes
from basic_log import log
from decorators import apikey_required
from discord_utils import DiscommentClient
from msg_queue import channel_msg_manager

sse: Blueprint = Blueprint("sse", __name__)


@dataclass
class ServerSentEvent:
    data: str
    retry: int | None
    event: str | None = None
    id: int | None = None

    def encode(self) -> bytes:
        message = f"data: {self.data}"
        if self.event is not None:
            message = f"{message}\nevent: {self.event}"
        if self.id is not None:
            message = f"{message}\nid: {self.id}"
        if self.retry is not None:
            message = f"{message}\nretry: {self.retry}"
        message = f"{message}\r\n\r\n"
        return message.encode('utf-8')


@sse.get("/sse/comments")
@apikey_required(scopes=[Scopes.ACCOUNT_READ])
async def sse_comments():
    if "text/event-stream" not in request.accept_mimetypes:
        abort(400)

    user: UserModel = g.get("user")
    channel_id: int = int(request.args["channelId"])

    async def send_events():
        msgs: list = channel_msg_manager.pop(channel_id=channel_id)
        last_msg: Optional[Message] = msgs[-1] if 0 < len(msgs) else None

        while True:
            log("sse alive", logging.DEBUG, __name__)
            await sleep(user.user_data.websocket_sleep_s)
            last_msg = msgs[-1] if 0 < len(msgs) else last_msg
            log(last_msg.content if last_msg is not None else "None", logging.DEBUG, __name__)
            msgs = channel_msg_manager.pop(channel_id=channel_id, as_of=last_msg)

            event = ServerSentEvent(json.dumps([DiscommentClient.msg_to_json(m) for m in msgs]), retry=3)
            yield event.encode()

    response = await make_response(
        send_events(),
        {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Transfer-Encoding': 'chunked',
        },
    )
    response.timeout = None
    return response
