from typing import List
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDSqlBase
from app.models.user import User
from app.models.table import Table
from app.schemas.table import TableCreate, TableUpdate

class CRUDTable(CRUDSqlBase[Table, TableCreate, TableUpdate]):
    def create_with_owner(self, db: Session, *, obj_in: TableCreate, owner_id: int) -> Table:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, owner_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100) -> List[Table]:
        return db.query(self.model).filter(Table.owner_id == owner_id).offset(skip).limit(limit).all()

    def get_shared_tables_by_owner(
            self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Table]:
        user = db.query(User).get(owner_id)
        shared_tables_id_list = [shared_table.id for shared_table in user.shared_tables]
        return db.query(self.model).filter(Table.id.in_(shared_tables_id_list)).offset(skip).limit(limit).all()

    def get_shared_users_by_table(
            self, db: Session, *, table_id: int, skip: int = 0, limit: int = 100
    ) -> List[User]:
        table_db_obj = db.query(Table).get(table_id)
        shared_users_id_list = [shared_user.id for shared_user in table_db_obj.shared_users]
        return db.query(User).filter(User.id.in_(shared_users_id_list)).offset(skip).limit(limit).all()

    def get_by_table_name(self, db: Session, *, table_name: str) -> Table:
        return db.query(Table).filter(Table.table_name == table_name).first()

table = CRUDTable(Table)
