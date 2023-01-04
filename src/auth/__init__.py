from auth.user import UserModel
from sqlite import SqliteStore

auth_store: SqliteStore = SqliteStore("discomment", [UserModel])
