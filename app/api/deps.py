from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session
from pydantic.networks import EmailStr
from sqlalchemy.ext.automap import automap_base

from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal, engine

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_model(table_name: str):
    AutoMapBase = automap_base()
    AutoMapBase.prepare(engine, reflect=True)
    # print(list(AutoMapBase.classes))
    model = getattr(AutoMapBase.classes, table_name, None)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No corresponding table found!"
        )
    return model

def get_current_user(db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)) -> models.User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials.")
    user = crud.user.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user

def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user.")
    return current_user

def get_current_active_superuser(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not crud.user.is_superuser(current_user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The user doesn't have enough privileges.")
    return current_user

def get_existing_user(
        *,
        db: Session = Depends(get_db),
        user_id: int
):
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No user found with the id provided."
        )
    return user

def get_existing_bucket(
        *,
        db: Session = Depends(get_db),
        bucket_id: int
):
    bucket = crud.bucket.get(db, id=bucket_id)
    if not bucket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No bucket found with the bucket_id provided."
        )
    return bucket

def get_existing_bucket_metadata(
        *,
        db: Session = Depends(get_db),
        bucket_metadata_id: int
):
    bucket_metadata = crud.bucket_metadata.get(db, id=bucket_metadata_id)
    if not bucket_metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No bucket metadata found with the id provided."
        )
    return bucket_metadata

def get_existing_table(
        *,
        db: Session = Depends(get_db),
        table_id: int
):
    table = crud.table.get(db, id=table_id)
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No table found with the id provided."
        )
    return table

def get_existing_user_by_email(
        *,
        db: Session = Depends(get_db),
        user_email: EmailStr
):
    user = crud.user.get_by_email(db, email=user_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No user found with the email provided."
        )
    return user

def get_bucket_with_permission(
        *,
        current_user: models.User = Depends(get_current_user),
        bucket=Depends(get_existing_bucket)
):
    if not crud.user.is_superuser(current_user) and (bucket.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions."
        )
    return bucket

def get_bucket_with_permission_shared(
        *,
        current_user: models.User = Depends(get_current_user),
        bucket=Depends(get_existing_bucket)
):
    if not crud.user.is_superuser(current_user) and (bucket.owner_id != current_user.id) \
            and (bucket.id not in [shared_bucket.id for shared_bucket in current_user.shared_buckets]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions."
        )
    return bucket

def get_bucket_metadata_with_permission(
        *,
        current_user: models.User = Depends(get_current_user),
        bucket_metadata=Depends(get_existing_bucket_metadata)
):
    if not crud.user.is_superuser(current_user) and bucket_metadata.bucket_id not \
            in [bucket.id for bucket in current_user.buckets]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions."
        )
    return bucket_metadata

def get_bucket_metadata_with_permission_shared(
        *,
        current_user: models.User = Depends(get_current_user),
        bucket_metadata=Depends(get_existing_bucket_metadata)
):
    if not crud.user.is_superuser(current_user) and bucket_metadata.bucket_id not \
            in [bucket.id for bucket in current_user.buckets] and \
            bucket_metadata.bucket_id not in [shared_bucket.id for shared_bucket in current_user.shared_buckets]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions."
        )
    return bucket_metadata

def get_table_with_permission(
        *,
        current_user: models.User = Depends(get_current_user),
        table=Depends(get_existing_table)
):
    if not crud.user.is_superuser(current_user) and (table.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions."
        )
    return table

def get_model_with_permission(
        *,
        current_user: models.User = Depends(get_current_user),
        model=Depends(get_model)
):
    if not crud.user.is_superuser(current_user) and model.__table__.name not \
            in [table.table_name for table in current_user.tables]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions."
        )
    return model

def get_model_with_permission_shared(
        *,
        current_user: models.User = Depends(get_current_user),
        model=Depends(get_model)
):
    if not crud.user.is_superuser(current_user) and model.__table__.name not \
            in [table.table_name for table in current_user.tables] and model.__table__.name not \
            in [shared_table.table_name for shared_table in current_user.shared_tables]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions."
        )
    return model

