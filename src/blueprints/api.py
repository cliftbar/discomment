import dataclasses
import uuid

from discord import Message
from quart import Blueprint, request, g
from sqlalchemy import Table
from werkzeug.exceptions import BadRequest

from auth import auth_store, UserModel
from auth.authutils import verify_hash, create_hash, Scopes
from auth.user import UserData
from config import account_conf
from dctypes import JSON
from decorators import apikey_required
from discord_utils import discord_client, DiscommentClient
from discord_utils.moderation import validate_msg
from http_exceptions import ModerationApplied
from sqlite import GenericQuery

api: Blueprint = Blueprint("api", __name__)


@api.route("/api/msg", methods=["POST"])
@apikey_required(scopes=[Scopes.ACCOUNT_WRITE])
async def send_msg() -> JSON:
    user: UserModel = g.get("user")
    json_data: dict = await request.get_json()
    msg: str = json_data['message']

    if user.user_data.moderation:
        if validate_msg(msg):
            raise ModerationApplied()

    msg = f"Author: {uuid.uuid4()}\n{msg}"
    ret: Message = await discord_client.get_channel(account_conf.comment_channel_id).send(msg)
    return DiscommentClient.msg_to_json(ret)


@api.route("/api/msg")
@apikey_required(scopes=[Scopes.ACCOUNT_READ])
async def get_messages() -> JSON:
    msgs: list = [message async for message in
                  discord_client.get_channel(account_conf.comment_channel_id).history(limit=account_conf.history_count)]
    contents: JSON = [DiscommentClient.msg_to_json(m) for m in msgs]
    return contents


@api.route("/api/auth/apikey/verify")
@apikey_required(scopes=[Scopes.ACCOUNT_READ])
async def verify_apikey() -> JSON:
    apikey: str = request.headers.get("Authorization").split(" ")[1]
    namespace: str = request.args.get("ns")

    auth_table: Table = auth_store.get_table(UserModel.tablename())
    query: GenericQuery = UserModel.fetch_key_ns(auth_table, namespace, "hash")
    ps_hash: str = auth_store.fetch_first_entity(query)

    return {"result": verify_hash(apikey, ps_hash)}


@api.route("/api/auth/apikey/create", methods=["POST"])
@apikey_required(scopes=[Scopes.ADMIN])
async def create_apikey() -> JSON:
    js: JSON = await request.get_json()

    namespace: str = js["namespace"]
    allowed_hosts: list[str] = js.get("allowedHosts", ["*"])
    moderation: bool = js.get("moderation", True)
    scopes: list[Scopes] = [Scopes(s)
                            for s
                            in js.get("scopes", [Scopes.ACCOUNT_READ.value, Scopes.ACCOUNT_WRITE.value])
                            if s != Scopes.ADMIN.value]

    new_apikey: str = f"dsc.{uuid.uuid4()}"
    hashed_apikey: str = create_hash(new_apikey, apikey=True)

    data: UserData = UserData(hash=hashed_apikey, allowed_hosts=allowed_hosts, moderation=moderation, scopes=scopes)

    entry: UserModel = UserModel(apikey_id=namespace, kvs=dataclasses.asdict(data))

    auth_store.store_row(entry)

    return {"apikey": new_apikey}
