import uuid

from discord import Message
from quart import Blueprint, request
from sqlalchemy import Table

from auth import auth_store, APIKeyModel
from auth.authutils import verify_hash
from config import account_conf
from dctypes import JSON
from discord_utils import discord_client, DiscommentClient
from sqlite import GenericQuery

api: Blueprint = Blueprint("api", __name__)


@api.route("/api/msg", methods=["POST"])
async def send_msg() -> JSON:
    json_data: dict = await request.get_json()
    msg = f"Author: {uuid.uuid4()}\n{json_data['message']}"
    ret: Message = await discord_client.get_channel(account_conf.comment_channel_id).send(msg)
    return DiscommentClient.msg_to_json(ret)


@api.route("/api/msg")
async def get_messages() -> JSON:
    msgs: list = [message async for message in
                  discord_client.get_channel(account_conf.comment_channel_id).history(limit=account_conf.history_count)]
    contents: JSON = [DiscommentClient.msg_to_json(m) for m in msgs]
    return contents


@api.route("/api/auth/test")
async def sqltest() -> JSON:
    apikey: str = request.args.get("apikey")

    auth_table: Table = auth_store.get_table(APIKeyModel.tablename())
    query: GenericQuery = APIKeyModel.fetch_key(auth_table, "localhost", "hash")
    ps_hash: str = auth_store.fetch_first_entity(query)

    return {"result": verify_hash(apikey, ps_hash)}
