from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr
import datetime
from sqlalchemy import Column, DateTime

@as_declarative()
class Base:
    id: Any
    __name__: str
    create_at = Column(DateTime, default=datetime.datetime.now)
    update_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

