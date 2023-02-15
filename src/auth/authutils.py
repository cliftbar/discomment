import logging
from enum import Enum
import socket

from passlib.handlers.argon2 import argon2

from basic_log import log
from config import server_conf


def create_hash(secret: str, apikey: bool = False):
    salt: bytes = bytes(server_conf.apikey_salt, "utf-8") if apikey else None
    return argon2.using(salt=salt).hash(secret)


def verify_hash(secret: str, pw_hash: str) -> bool:
    return argon2.verify(secret, pw_hash)


def verify_hosts(remote_ip: str, host_list: list[str]) -> bool:
    if "*" in host_list:
        return True
    ip_list: list[str] = [socket.gethostbyname(host) for host in host_list]
    log(f"hosts: {host_list}", logging.DEBUG)
    log(f"ips: {ip_list}", logging.DEBUG)
    return remote_ip in ip_list


class Scopes(str, Enum):
    ADMIN = "admin"
    ACCOUNT_READ = "account_read"
    ACCOUNT_WRITE = "account_write"
    WS_READ = "ws_read"


def verify_scopes(user_scopes: list[str], allowed_scopes: list[Scopes]) -> bool:
    if allowed_scopes is None:
        return False
    for s in allowed_scopes:
        if s.value in user_scopes:
            return True
    return False
