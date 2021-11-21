from typing import List
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDSqlBase
from app.models.user import User
from app.models.bucket import Bucket
from app.schemas.bucket import BucketCreate, BucketUpdate

class CRUDBucket(CRUDSqlBase[Bucket, BucketCreate, BucketUpdate]):
    def create_with_owner(self, db: Session, *, obj_in: BucketCreate, owner_id: int) -> Bucket:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, owner_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100) -> List[Bucket]:
        return db.query(self.model).filter(Bucket.owner_id == owner_id).offset(skip).limit(limit).all()

    def get_shared_buckets_by_owner(
            self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Bucket]:
        # user = db.query(User).filter(User.id == owner_id).first()
        user = db.query(User).get(owner_id)
        shared_buckets_id_list = [shared_bucket.id for shared_bucket in user.shared_buckets]
        return db.query(self.model).filter(Bucket.id.in_(shared_buckets_id_list)).offset(skip).limit(limit).all()

    def get_shared_users_by_bucket(
            self, db: Session, *, bucket_id: int, skip: int = 0, limit: int = 100
    ) -> List[User]:
        bucket_db_obj = db.query(Bucket).get(bucket_id)
        shared_users_id_list = [shared_user.id for shared_user in bucket_db_obj.shared_users]
        return db.query(User).filter(User.id.in_(shared_users_id_list)).offset(skip).limit(limit).all()

bucket = CRUDBucket(Bucket)


