from sqlalchemy import Column, Table, Integer, ForeignKey

from app.db.base_class import Base

user_table_relation = Table(
    "user_table_relation",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id", ondelete="CASCADE")),
    Column("table_id", Integer, ForeignKey("table.id", ondelete="CASCADE"))
)
