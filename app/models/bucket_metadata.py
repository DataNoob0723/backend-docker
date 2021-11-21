from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.bucket import Bucket  # noqa

class BucketMetadata(Base):
    id = Column(Integer, primary_key=True, autoincrement=True)
    author = Column(String(256), nullable=False)
    description = Column(Text)
    bucket_id = Column(Integer, ForeignKey("bucket.id", ondelete="CASCADE"))
    bucket = relationship("Bucket", back_populates="bucket_metadata")
