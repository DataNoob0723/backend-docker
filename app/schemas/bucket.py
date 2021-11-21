# from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# from app.schemas.user import User
from app.schemas.bucket_metadata import BucketMetadata

# Shared properties
class BucketBase(BaseModel):
    bucket_name: str = None
    # create_at: datetime
    # update_at: datetime
    create_at: Optional[datetime] = None
    update_at: Optional[datetime] = None

# Properties to receive on bucket creation
class BucketCreate(BucketBase):
    bucket_name: str

# Properties to receive on bucket update
class BucketUpdate(BucketBase):
    pass

# Properties shared by models stored in DB
class BucketInDBBase(BucketBase):
    id: int
    bucket_name: str
    owner_id: int

    class Config:
        orm_mode = True

# Properties to return to client
class Bucket(BucketInDBBase):
    # shared_users: List[User] = []
    bucket_metadata: Optional[BucketMetadata] = None

# Properties stored in DB
class BucketInDB(BucketInDBBase):
    pass

# from app.schemas.user import User
# Bucket.update_forward_refs()
