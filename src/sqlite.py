import logging
from abc import abstractmethod
from enum import Enum
from typing import Type, TypeVar, Any, Sequence, Optional

from sqlalchemy import create_engine, Table, Row, RowMapping, Executable
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base, Session, Query

from basic_log import log

Base = declarative_base()


class GenericTypeVar(TypeVar, _root=True):
    def __getitem__(self, item): pass


# add more items to count as a "query" here
GenericQuery = GenericTypeVar("GenericQuery", Query, select)
M = GenericTypeVar("M")


# https://stackoverflow.com/questions/49581907/when-inheriting-sqlalchemy-class-from-abstract-class-exception-thrown-metaclass
class BaseWithMigrations(Base):
    __abstract__ = True

    @classmethod
    def tablename(cls):
        return cls.__tablename__

    @classmethod
    @abstractmethod
    def migrations(cls) -> list[str]:
        pass


class SqliteStore:
    class ParallelizationMode(Enum):
        main = "main"
        threaded = "threaded"

    def __init__(self, db_filename: str, models: list[Type[BaseWithMigrations]], ):
        self.engine = create_engine(f"sqlite:///{db_filename}.sqlite", echo=False, future=True)
        self.metadata = Base.metadata
        self.metadata.create_all(self.engine)
        self.tables: dict[str, Table] = {}

        session: Session = Session(self.engine, expire_on_commit=False)
        with session.begin() as tx:
            for model in models:
                for migration in model.migrations():
                    self.ddl_statement(session, migration)
                self.tables[model.tablename()] = Table(model.tablename(), self.metadata, autoload=True)
            log(f"{db_filename} migrations done", logging.INFO)
            tx.commit()

    @staticmethod
    def ddl_statement(session: Session, statement: str):
        try:
            session.execute(statement)
        except OperationalError as oe:
            msg = str(oe)
            if "duplicate" not in msg:
                raise oe
        except IntegrityError as ie:
            msg = str(ie)
            if "UNIQUE constraint failed" not in msg:
                raise ie

    def store_row(self, row: Base):
        return self.store_rows([row])

    def store_rows(self, rows: list[Base]):
        session: Session = Session(self.engine, expire_on_commit=False)
        with session.begin():
            session.add_all(rows)

    def fetch_entities(self, stmt: Executable) -> Sequence[Row | RowMapping | Any]:
        session: Session = Session(self.engine, expire_on_commit=False)
        with session.begin():
            res: Sequence[Row | RowMapping | Any] = session.execute(statement=stmt).scalars().all()

        return res

    def fetch_first_entity(self, stmt: Executable) -> Optional[M]:
        session: Session = Session(self.engine, expire_on_commit=False)
        with session.begin():
            res: Optional[M] = session.execute(statement=stmt).scalars().first()

        return res

    def get_table(self, tablename: str) -> Table:
        return self.tables[tablename]
