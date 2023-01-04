import dataclasses
import json
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import func, DATETIME, TEXT, Column, JSON, Table
from sqlalchemy.future import select
from sqlalchemy.orm import Query
from sqlalchemy.sql import FromClause

from auth.authutils import create_hash, Scopes
from config import account_conf
from sqlite import BaseWithMigrations, GenericQuery


class UserModel(BaseWithMigrations):
    __tablename__ = "users"

    apikey_id: str = Column(TEXT, primary_key=True, nullable=False)
    created_at: datetime = Column(DATETIME, nullable=False, server_default=func.now())

    kvs: dict = Column(JSON, nullable=False)

    @property
    def user_data(self):
        return UserData(**self.kvs)

    @classmethod
    def migrations(cls) -> list[str]:
        # Write migrations here in order
        migration_1_data: UserData = UserData(
            create_hash("localhost", apikey=True),
            ["localhost", "127.0.0.1"],
            moderation=account_conf.moderation_enabled,
            scopes=[Scopes.ADMIN, Scopes.ACCOUNT_READ, Scopes.ACCOUNT_WRITE],
            history_limit=account_conf.history_limit,
            websocket_sleep_s=account_conf.websocket_sleep_s,
            linear_moderation_threshold=account_conf.linear_moderation_threshold,
            max_msg_length=account_conf.max_msg_length,
        )

        return [
            f"INSERT INTO {cls.__tablename__} (apikey_id, kvs) VALUES ('localhost', json('{json.dumps(dataclasses.asdict(migration_1_data))}'))"
        ]

    def to_json(self) -> dict:
        return {
            "apikey_id": self.apikey_id,
            "created_at": self.created_at.isoformat(),
            "kvs": self.kvs
        }

    @staticmethod
    def fetch_key_ns(table: Table, namespace: str, key: str) -> GenericQuery["UserModel"]:
        return UserModel.fetch_path_ns(table, namespace, [key])

    @staticmethod
    def fetch_path_ns(table: Table, namespace: str, path: list[str]) -> GenericQuery["UserModel"]:
        selector: FromClause = table.c.kvs

        for p in path:
            selector = table.c.kvs[p]
        return select(selector).where(table.c.apikey_id == namespace)

    @staticmethod
    def fetch_by_hash(table: Table, pw_hash: str) -> GenericQuery["UserModel"]:
        json_part = func.json_each(table.c["kvs"]).table_valued('value', joins_implicitly=True)
        query: Query = select(UserModel).where(json_part.c.value == pw_hash)
        return query


@dataclass
class UserData:
    hash: str
    allowed_hosts: list[str]
    moderation: bool = False
    scopes: list[Scopes] = field(default_factory=list)

    history_limit: int = account_conf.history_limit
    websocket_sleep_s: float = account_conf.websocket_sleep_s

    max_msg_length: int = account_conf.max_msg_length
    linear_moderation_threshold: float = account_conf.linear_moderation_threshold
    moderation_enabled: bool = account_conf.moderation_enabled
