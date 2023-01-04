import dataclasses
import uuid

from discord import Message
from quart import Blueprint, request
from sqlalchemy import Table

from auth import auth_store, APIKeyModel
from auth.apikey import APIKeyData
from auth.authutils import verify_hash, create_hash
from config import account_conf
from dctypes import JSON
from decorators import apikey_required
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


@api.route("/api/auth/apikey/verify")
@apikey_required()
async def verify_apikey() -> JSON:
    apikey: str = request.headers.get("Authorization").split(" ")[1]
    namespace: str = request.args.get("ns")

    auth_table: Table = auth_store.get_table(APIKeyModel.tablename())
    query: GenericQuery = APIKeyModel.fetch_key_ns(auth_table, namespace, "hash")
    ps_hash: str = auth_store.fetch_first_entity(query)

    return {"result": verify_hash(apikey, ps_hash)}


@api.route("/api/auth/apikey/create", methods=["POST"])
async def create_apikey() -> JSON:
    js: JSON = await request.get_json()

    namespace: str = js["namespace"]
    allowed_hosts: list[str] = js.get("allowedHosts", ["*"])

    new_apikey: str = f"dsc.{uuid.uuid4()}"
    hashed_apikey: str = create_hash(new_apikey, apikey=True)

    data: APIKeyData = APIKeyData(hashed_apikey, allowed_hosts)

    entry: APIKeyModel = APIKeyModel(apikey_id=namespace, kvs=dataclasses.asdict(data))

    auth_store.store_row(entry)

    return {"apikey": new_apikey}
