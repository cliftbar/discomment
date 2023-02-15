import dataclasses
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from sqlalchemy import func, DATETIME, TEXT, Column, JSON, Table, BOOLEAN, Select, text
from sqlalchemy.future import select
from sqlalchemy.sql import FromClause
from sqlalchemy_json import mutable_json_type

from auth.authutils import create_hash, Scopes
from config import account_conf
from sqlite import BaseWithMigrations, GenericQuery


@dataclass
class APIKeyData:
    identifier: str
    hash: str
    channel_id: int = -1
    allowed_hosts: list[str] = field(default_factory=list)
    scopes: list[Scopes] = field(default_factory=list)

    history_limit: int = account_conf.history_limit
    websocket_sleep_s: float = account_conf.websocket_sleep_s

    max_msg_length: int = account_conf.max_msg_length
    linear_moderation_threshold: float = account_conf.linear_moderation_threshold
    moderation_enabled: bool = account_conf.moderation_enabled


class UserModel(BaseWithMigrations):
    __tablename__ = "users"

    namespace: str = Column(TEXT, primary_key=True, nullable=False)
    created_at: datetime = Column(DATETIME, nullable=False, server_default=func.now())

    kvs: dict = Column(mutable_json_type(JSON, nested=True), nullable=False)
    deleted: bool = Column(BOOLEAN, nullable=False, server_default="0")

    # More expensive than lookup by hash
    def apikey_data_by_id(self, apikey_id: str) -> Optional[APIKeyData]:
        vals = [v for v in self.kvs.values() if v["identifier"] == apikey_id]

        if len(vals) == 0:
            return None
        elif 1 < len(vals):
            raise Exception(f"Too many keys found for id {apikey_id}")

        return APIKeyData(**vals[0])

    def apikey_data_by_hash(self, apikey_hash) -> Optional[APIKeyData]:
        for k, v in self.kvs.items():
            if k == apikey_hash:
                return APIKeyData(**v)
        return None

    @classmethod
    def migrations(cls) -> list[text]:
        # Write migrations here in order
        migration_1_data: APIKeyData = APIKeyData(
            identifier="basic",
            hash=create_hash("localhost", apikey=True),
            allowed_hosts=["localhost", "127.0.0.1"],
            scopes=[Scopes.ADMIN, Scopes.ACCOUNT_READ, Scopes.ACCOUNT_WRITE, Scopes.WS_READ],
            history_limit=account_conf.history_limit,
            websocket_sleep_s=account_conf.websocket_sleep_s,
            linear_moderation_threshold=account_conf.linear_moderation_threshold,
            max_msg_length=account_conf.max_msg_length,
        )
        migration_1_kvs = json.dumps({
            migration_1_data.hash: dataclasses.asdict(migration_1_data)
        })

        # TODO: text has bind params??
        return [
            # text("INSERT INTO :table (namespace, kvs) VALUES (':ns', json(':data'))")
            # .bindparams(table=cls.__tablename__, ns="localhost", data=migration_1_kvs)
            text(f"-- INSERT INTO {cls.__tablename__} (namespace, kvs) VALUES ('localhost', json('{migration_1_kvs}'))")
        ]

    def to_json(self) -> dict:
        return {
            "apikey_id": self.namespace,
            "created_at": self.created_at.isoformat(),
            "kvs": self.kvs
        }

    @staticmethod
    def fetch_ns(namespace: str) -> Select:
        return select(UserModel).where(UserModel.namespace == namespace)

    @staticmethod
    def fetch_key_ns(table: Table, namespace: str, key: str) -> GenericQuery["UserModel"]:
        return UserModel.fetch_path_ns(table, namespace, [key])

    @staticmethod
    def fetch_path_ns(table: Table, namespace: str, path: list[str]) -> GenericQuery["UserModel"]:
        selector: FromClause = table.c.kvs

        for p in path:
            selector = table.c.kvs[p]
        return select(selector).where(table.c.namespace == namespace)

    @staticmethod
    def fetch_by_hash(table: Table, pw_hash: str) -> Select:
        json_part = func.json_each(table.c["kvs"]).table_valued("key", "value", joins_implicitly=True)
        query: Select = select(UserModel).where(json_part.c.key == pw_hash)
        return query
