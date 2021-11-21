from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Shared properties
class BucketMetadataBase(BaseModel):
    author: str = None
    description: str = None
    create_at: Optional[datetime] = None
    update_at: Optional[datetime] = None

# Properties to receive on bucket metadata creation
class BucketMetadataCreate(BucketMetadataBase):
    author: str

# Properties to receive on bucket metadata update
class BucketMetadataUpdate(BucketMetadataBase):
    pass

# Properties shared by models stored in DB
class BucketMetadataInDBBase(BucketMetadataBase):
    id: int
    author: str
    bucket_id: int

    class Config:
        orm_mode = True

# Properties to return to client
class BucketMetadata(BucketMetadataInDBBase):
    pass

# Properties stored in DB
class BucketMetaInDB(BucketMetadataInDBBase):
    pass
