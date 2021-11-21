from typing import Optional
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDSqlBase
from app.models.bucket_metadata import BucketMetadata
from app.schemas.bucket_metadata import BucketMetadataCreate, BucketMetadataUpdate

class CRUDBucketMetadata(CRUDSqlBase[BucketMetadata, BucketMetadataCreate, BucketMetadataUpdate]):
    def get_by_bucket_id(self, db: Session, bucket_id: int) -> Optional[BucketMetadata]:
        return db.query(self.model).filter(self.model.bucket_id == bucket_id).first()

    def create_with_bucket(self, db: Session, *, obj_in: BucketMetadataCreate, bucket_id: int) -> BucketMetadata:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, bucket_id=bucket_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

bucket_metadata = CRUDBucketMetadata(BucketMetadata)
