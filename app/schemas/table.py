from pydantic import BaseModel, Json
from datetime import datetime
from typing import Optional

# Shared properties
class TableBase(BaseModel):
    table_name: str = None
    data_type: Optional[str] = None
    units: Optional[Json] = None
    original_file_name: Optional[str] = None
    added_by: Optional[str] = None
    num_of_rows: Optional[int] = None
    instructions: Optional[Json] = None
    additional_information: Optional[Json] = None
    create_at: Optional[datetime] = None
    update_at: Optional[datetime] = None

# Properties to receive on table creation
class TableCreate(TableBase):
    table_name: str

# Properties to receive on table update
class TableUpdate(TableBase):
    pass

# Properties shared by models stored in DB
class TableInDBBase(TableBase):
    id: int
    table_name: str
    owner_id: int

    class Config:
        orm_mode = True

# Properties to return to client
class Table(TableInDBBase):
    pass

# Properties stored in DB
class TableInDB(TableInDBBase):
    pass
