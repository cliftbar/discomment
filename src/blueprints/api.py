import dataclasses
import uuid
from datetime import datetime

from discord import Message
from quart import Blueprint, request, g

from auth import auth_store, UserModel
from auth.authutils import verify_hash, create_hash, Scopes
from auth.user import UserData
from config import account_conf
from dctypes import JSON
from decorators import apikey_required
from discord_utils import discord_client, DiscommentClient
from discord_utils.moderation import validate_msg
from http_exceptions import ModerationApplied

api: Blueprint = Blueprint("api", __name__)


@api.route("/api/msg", methods=["POST"])
@apikey_required(scopes=[Scopes.ACCOUNT_WRITE])
async def send_msg() -> JSON:
    user: UserModel = g.get("user")
    json_data: dict = await request.get_json()
    msg: str = json_data['message']
    channel_id: int = int(json_data["channelId"])

    if user.user_data.moderation:
        if validate_msg(msg):
            raise ModerationApplied()

    msg = f"Author: {uuid.uuid4()}\n{msg}"
    ret: Message = await discord_client.get_channel(channel_id).send(msg)
    return DiscommentClient.msg_to_json(ret)


@api.route("/api/msg")
@apikey_required(scopes=[Scopes.ACCOUNT_READ])
async def get_messages() -> JSON:
    channel_id: int = int(request.args["channelId"])
    as_of_str: str = request.args.get("asOf")
    as_of: datetime = None if as_of_str is None else datetime.fromisoformat(as_of_str)

    user: UserModel = g.get("user")

    history_limit: int = (user.user_data.history_limit
                          if user.user_data.history_limit is not None
                          else account_conf.history_limit)

    msgs: list = [message
                  async for message
                  in discord_client.get_channel(channel_id)
                  .history(limit=history_limit, before=as_of)]

    contents: JSON = [DiscommentClient.msg_to_json(m) for m in msgs]
    return contents


@api.route("/api/auth/apikey/verify")
@apikey_required(scopes=[Scopes.ACCOUNT_READ])
async def verify_apikey() -> JSON:
    user: UserModel = g.get("user")

    apikey: str = request.headers.get("Authorization").split(" ")[1]

    return {"result": verify_hash(apikey, user.user_data.hash), "scopes": user.user_data.scopes}


@api.route("/api/auth/apikey/create", methods=["POST"])
@apikey_required(scopes=[Scopes.ADMIN])
async def create_apikey() -> JSON:
    js: JSON = await request.get_json()

    namespace: str = js["namespace"]
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

    data: UserData = UserData(hash=hashed_apikey, allowed_hosts=allowed_hosts, moderation=moderation, scopes=scopes,
                              max_msg_length=max_msg_length, moderation_enabled=moderation,
                              linear_moderation_threshold=linear_moderation_threshold,
                              websocket_sleep_s=websocket_sleep_s)

    entry: UserModel = UserModel(apikey_id=namespace, kvs=dataclasses.asdict(data))

    auth_store.store_row(entry)

    return {"apikey": new_apikey}
