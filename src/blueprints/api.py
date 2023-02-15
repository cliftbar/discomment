import dataclasses
import logging
import uuid
from datetime import datetime

from discord import Message
from quart import Blueprint, request, g
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Conflict, NotFound

from auth import auth_store, UserModel
from auth.authutils import verify_hash, create_hash, Scopes
from auth.user import APIKeyData
from basic_log import log
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
    json_data: dict = await request.get_json()
    msg: str = json_data['message']
    author: str = json_data.get("author", uuid.uuid4())

    user: UserModel = g.get("user")
    apikey_hash: str = g.get("api_key_hash")
    api_key_data = user.apikey_data_by_hash(apikey_hash)

    if api_key_data.moderation_enabled:
        if validate_msg(msg):
            raise ModerationApplied()

    msg = f"Author: {author}\n{msg}"
    ret: Message = await discord_client.get_channel(api_key_data.channel_id).send(msg)
    return DiscommentClient.msg_to_json(ret)


@api.route("/api/msg")
@apikey_required(scopes=[Scopes.ACCOUNT_READ])
async def get_messages() -> JSON:
    as_of_str: str = request.args.get("asOf")
    as_of: datetime = None if as_of_str is None else datetime.fromisoformat(as_of_str)

    user: UserModel = g.get("user")
    apikey_hash: str = g.get("api_key_hash")
    api_key_data: APIKeyData = user.apikey_data_by_hash(apikey_hash)

    if api_key_data is None:
        raise NotFound(g.get("api_key"))

    history_limit: int = (api_key_data.history_limit
                          if api_key_data.history_limit is not None
                          else account_conf.history_limit)

    msgs: list = [message
                  async for message
                  in discord_client.get_channel(api_key_data.channel_id).history(limit=history_limit, before=as_of)]

    contents: JSON = [DiscommentClient.msg_to_json(m) for m in msgs]
    return contents


@api.route("/api/auth/apikey/verify")
@apikey_required(scopes=[Scopes.ACCOUNT_READ])
async def verify_apikey() -> JSON:
    user: UserModel = g.get("user")
    apikey_hash: str = g.get("api_key_hash")

    apikey: str = request.headers.get("Authorization").split(" ")[1]

    return {"result": verify_hash(apikey, user.apikey_data_by_hash(apikey_hash).hash),
            "scopes": user.apikey_data_by_hash(apikey_hash).scopes}


@api.route("/api/auth/namespace", methods=["POST"])
async def create_namespace() -> JSON:
    js: JSON = await request.get_json()

    namespace: str = js["namespace"]

    new_apikey: str = f"dsc.{uuid.uuid4()}"
    hashed_apikey: str = create_hash(new_apikey, apikey=True)

    api_key_data: APIKeyData = APIKeyData(identifier="admin", hash=hashed_apikey, allowed_hosts=["*"],
                                          scopes=[Scopes.ADMIN])

    entry: UserModel = UserModel(namespace=namespace, kvs={api_key_data.hash: dataclasses.asdict(api_key_data)})

    try:
        auth_store.store_row(entry)
    except IntegrityError as ie:
        log(str(ie), logging.DEBUG)
        raise Conflict(f"namespace {namespace} already exists")

    return {"namespace": namespace, "adminApiKey": new_apikey}


@api.route("/api/auth/apikey", methods=["POST"])
@apikey_required(scopes=[Scopes.ADMIN])
async def create_apikey() -> JSON:
    js: JSON = await request.get_json()

    namespace: str = js["namespace"]
    apikey_identifier: str = js["identifier"]
    channel_id: int = int(js["channelId"])
    allowed_hosts: list[str] = js.get("allowedHosts", ["*"])
    moderation: bool = js.get("moderation", account_conf.moderation_enabled)
    scopes: list[Scopes] = [Scopes(s)
                            for s
                            in js.get("scopes", [Scopes.ACCOUNT_READ.value, Scopes.ACCOUNT_WRITE.value])
                            if s != Scopes.ADMIN.value]
    max_msg_length: int = js.get("maxMsgLength", account_conf.max_msg_length)
    linear_moderation_threshold: int = js.get("moderationThreshold", account_conf.linear_moderation_threshold)
    websocket_sleep_s: float = js.get("websocketSleepS", account_conf.websocket_sleep_s)

    new_apikey: str = f"dsc.{uuid.uuid4()}"
    hashed_apikey: str = create_hash(new_apikey, apikey=True)

    data: APIKeyData = APIKeyData(identifier=apikey_identifier, hash=hashed_apikey, channel_id=channel_id,
                                  allowed_hosts=allowed_hosts, scopes=scopes, max_msg_length=max_msg_length,
                                  moderation_enabled=moderation,
                                  linear_moderation_threshold=linear_moderation_threshold,
                                  websocket_sleep_s=websocket_sleep_s)

    query_existing: GenericQuery = UserModel.fetch_ns(namespace)
    existing_model: UserModel = auth_store.fetch_first_entity(query_existing)
    if existing_model is None:
        raise NotFound()

    if hashed_apikey in existing_model.kvs:
        raise Conflict(f"API Key {namespace} already exists")

    existing_model.kvs[hashed_apikey] = dataclasses.asdict(data)

    auth_store.store_row(existing_model)

    return {"apikey": new_apikey}
