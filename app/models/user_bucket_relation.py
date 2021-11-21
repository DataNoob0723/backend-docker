from sqlalchemy import Column, Table, Integer, ForeignKey

from app.db.base_class import Base

user_bucket_relation = Table(
    "user_bucket_relation",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id", ondelete="CASCADE")),
    Column("bucket_id", Integer, ForeignKey("bucket.id", ondelete="CASCADE"))
)
