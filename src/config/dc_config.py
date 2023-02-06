from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class DCServerConfig:
    bot_token: str
    apikey_salt: str
    static_route_apikey: str

    protocol: str = "http"
    host: str = "127.0.0.1"
    port: int = 5000
    cors_allowed_origin: str = "*"
    trusted_proxies: list[str] = field(default_factory=lambda: ["127.0.0.1"])
    log_level: str = "debug"
    msg_queue_max: int = 1000
    msg_queue_fetch_limit: int = 100

    static_routes_enabled: bool = False


@dataclass
class DCAccountConfig:
    comment_channel_id: int

    history_limit: int = 200
    websocket_sleep_s: float = 2

    max_msg_length: int = 1000
    linear_moderation_threshold: float = 0.4
    moderation_enabled: bool = True


@dataclass
class DCConfig:
    server: DCServerConfig
    account: DCAccountConfig


def init_config(conf_fi: Path) -> DCConfig:
    with open(conf_fi) as env:
        env_vals: dict = yaml.safe_load(env)

        server_conf: DCServerConfig = DCServerConfig(**env_vals["server"])
        account_conf: DCAccountConfig = DCAccountConfig(**env_vals["account"])

    return DCConfig(server_conf, account_conf)
