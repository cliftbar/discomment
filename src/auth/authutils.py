from passlib.handlers.argon2 import argon2

from config import server_conf


def create_hash(secret: str, apikey: bool = False):
    salt: bytes = bytes(server_conf.apikey_salt, "utf-8") if apikey else None
    return argon2.using(salt=salt).hash(secret)


def verify_hash(secret: str, pw_hash: str) -> bool:
    return argon2.verify(secret, pw_hash)
