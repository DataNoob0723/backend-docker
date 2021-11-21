from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user import User  # noqa
    from app.models.bucket_metadata import BucketMetadata  # noqa

class Bucket(Base):
    id = Column(Integer, primary_key=True, autoincrement=True)
    bucket_name = Column(String(256), nullable=False)
    owner_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    owner = relationship("User", back_populates="buckets")
    bucket_metadata = relationship("BucketMetadata", back_populates="bucket", uselist=False)
