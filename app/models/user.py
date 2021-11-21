from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship, backref
from typing import TYPE_CHECKING

from app.db.base_class import Base
from app.models.user_bucket_relation import user_bucket_relation
from app.models.user_table_relation import user_table_relation

if TYPE_CHECKING:
    from app.models.bucket import Bucket  # noqa
    from app.models.table import Table  # noqa

class User(Base):
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(256), unique=True, nullable=False, index=True)
    organization = Column(String(256), index=True)
    hashed_password = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    buckets = relationship("Bucket", back_populates="owner")  # Buckets created by user himself
    shared_buckets = relationship(  # Buckets shared to the user by other users
        "Bucket",
        secondary=user_bucket_relation,
        backref=backref("shared_users", lazy="dynamic")
    )
    tables = relationship("Table", back_populates="owner")  # Tables created by user himself
    shared_tables = relationship(
        "Table",
        secondary=user_table_relation,
        backref=backref("shared_users", lazy="dynamic")
    )


