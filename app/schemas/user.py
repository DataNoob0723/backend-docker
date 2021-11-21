# from __future__ import annotations
from pydantic import BaseModel
from pydantic.networks import EmailStr
from typing import Optional, List
from datetime import datetime

# from app.schemas.bucket import Bucket
# from app.schemas.table import Table

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    organization: Optional[str] = None
    # create_at: datetime
    # update_at: datetime
    create_at: Optional[datetime] = None
    update_at: Optional[datetime] = None

class UserBaseReduced(BaseModel):
    email: EmailStr
    organization: Optional[str] = None

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str
    organization: Optional[str] = None

# Properties to receive via API on update
class UserUpdate(UserBase):
    # password: Optional[str] = None
    password: str = None

class UserInDBBase(UserBase):
    id: int

    class Config:
        orm_mode = True

class UserInDBBaseReduced(UserBaseReduced):
    id: int

    class Config:
        orm_mode = True

# Additional properties to return via API
class User(UserInDBBase):
    # buckets: List[Bucket] = []
    # tables: List[Table] = []
    # shared_buckets: List[Bucket] = []
    # shared_tables: List[Table] = []
    pass

class UserReduced(UserInDBBaseReduced):
    pass

# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str

# from app.schemas.bucket import Bucket
# User.update_forward_refs()
