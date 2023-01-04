from dataclasses import dataclass


@dataclass
class DCServerConfig:
    bot_token: str
    apikey_salt: str

    host: str = "127.0.0.1"
    port: int = 5000
    log_level: str = "debug"
    msg_queue_max: int = 1000
    msg_queue_fetch_limit: int = 100


@dataclass
class DCAccountConfig:
    comment_channel_id: int

    history_count: int = 200
    websocket_sleep_s: int = 2

    max_msg_length: int = 1000
    linear_moderation_threshold: float = 0.4
    moderation_enabled: bool = True
