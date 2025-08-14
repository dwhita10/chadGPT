from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Literal, Optional


from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON


class ActionTable(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user: str = Field(index=True)
    timestamp: datetime = Field(default_factory=datetime.now(timezone.utc))
    category: str
    action: dict = Field(sa_column=Column(JSON))


class BaseDatabase(ABC):
    def write(self, user: str, category: str, action: dict) -> None:
        """
        Write an action to the database.
        :param user: The user performing the action.
        :param category: The category of the action.
        :param action: The action details as a dictionary.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    def read(self, **filters) -> list[ActionTable]:
        """
        Read actions from the database with optional filters.
        :param filters: Filters to apply to the query.
        :return: A list of ActionTable records matching the filters.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

class SQLiteDatabase(BaseDatabase):
    def __init__(self, db_url: str):
        from sqlmodel import create_engine, Session
        self.engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine)

    def write(self, user: str, category: str, action: dict) -> None:
        from sqlmodel import Session
        with Session(self.engine) as session:
            action_record = ActionTable(user=user, category=category, action=action)
            session.add(action_record)
            session.commit()

    def read(self, **filters) -> list[ActionTable]:
        from sqlmodel import select, Session
        with Session(self.engine) as session:
            query = select(ActionTable).where(**filters)
            return session.exec(query).all()
