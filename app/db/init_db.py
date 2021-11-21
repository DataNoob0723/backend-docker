from sqlalchemy.orm import Session
import datetime

from app import crud, schemas
from app.core.config import settings
from app.db import base  # noqa

# make sure all SQL Alchemy models are imported (app.db.base) before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly

def init_db(db: Session) -> None:
    user = crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER)
    if not user:
        user_in = schemas.UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
            create_at=datetime.datetime.now(),
            update_at=datetime.datetime.now()
        )
        user = crud.user.create(db, obj_in=user_in)

