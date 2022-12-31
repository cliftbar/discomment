import json
from asyncio import sleep

from quart import websocket, Blueprint

from discord_utils import DiscommentClient
from msg_queue import msg_queue
from msg_queue.utils import queue_get_many

ws: Blueprint = Blueprint("ws", __name__)


@ws.websocket('/ws')
async def comment_socket():
    print("ws")
    while True:
        print("ws alive")
        await sleep(2)
        msgs: list = queue_get_many(msg_queue)
        await websocket.send(json.dumps([DiscommentClient.msg_to_json(m) for m in msgs]))
