import json
from datetime import datetime

from sqlalchemy import func, DATETIME, TEXT, Column, JSON, Table
from sqlalchemy.future import select
from sqlalchemy.sql import FromClause

from auth.authutils import create_hash
from sqlite import BaseWithMigrations, GenericQuery


class APIKeyModel(BaseWithMigrations):
    __tablename__ = "apikey"

    apikey_id: str = Column(TEXT, primary_key=True, nullable=False)
    created_at: datetime = Column(DATETIME, nullable=False, server_default=func.utcnow())

    kvs: dict = Column(JSON, nullable=False)

    @classmethod
    def migrations(cls) -> list[str]:
        # Write migrations here in order
        migration_1_data: dict = {
            "hash": create_hash("localhost", apikey=True),
            "allowed_urls": ["localhost", "172.0.0.1"],
        }

        return [
            f"INSERT INTO {cls.__tablename__} (apikey_id, kvs) VALUES ('localhost', json('{json.dumps(migration_1_data)}'))"
        ]

    def to_json(self) -> dict:
        return {
            "apikey_id": self.apikey_id,
            "created_at": self.created_at.isoformat(),
            "kvs": self.kvs
        }

    @staticmethod
    def fetch_key(table: Table, namespace: str, key: str) -> GenericQuery["APIKeyModel"]:
        return APIKeyModel.fetch_path(table, namespace, [key])

    @staticmethod
    def fetch_path(table: Table, namespace: str, path: list[str]) -> GenericQuery["APIKeyModel"]:
        selector: FromClause = table.c.kvs

        for p in path:
            selector = table.c.kvs[p]
        return select(selector).where(table.c.apikey_id == namespace)
