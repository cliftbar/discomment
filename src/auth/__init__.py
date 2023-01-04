from auth.apikey import APIKeyModel
from sqlite import SqliteStore

auth_store: SqliteStore = SqliteStore("discomment", [APIKeyModel])
