import uuid

from discord import Message

from discord_utils import discord_client, DiscommentClient
from quart import Blueprint, request

from dctypes import JSON

api: Blueprint = Blueprint("api", __name__)


@api.route("/api/msg", methods=["POST"])
async def send_msg() -> JSON:
    json_data: dict = await request.get_json()
    msg = f"Author: {uuid.uuid4()}\n{json_data['message']}"
    ret: Message = await discord_client.get_channel(1057805224024211537).send(msg)
    return DiscommentClient.msg_to_json(ret)


@api.route("/api/msg")
async def get_messages() -> JSON:
    msgs: list = [message async for message in discord_client.get_channel(1057805224024211537).history(limit=200)]
    contents: JSON = [DiscommentClient.msg_to_json(m) for m in msgs]
    return contents
