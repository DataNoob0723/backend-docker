from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()

@router.get("/", response_model=List[schemas.User])
def read_users(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Retrieve all users in DB.\n
    To use this route, user must be authenticated as a superuser.\n
    Use parameters {skip} and {limit} to control the number of records to return.
    """
    users = crud.user.get_multi(db, skip=skip, limit=limit)
    return users

@router.post("/", response_model=schemas.User)
def create_user(
        *,
        db: Session = Depends(deps.get_db),
        user_in: schemas.UserCreate,
        current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Create new user.\n
    To use this route, user must be authenticated as a superuser.\n
    Fields 'create_at' and 'update_at' don't need to be provided since they will be automatically generated.
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this username already exists in the system."
        )
    user = crud.user.create(db, obj_in=user_in)
    return user

@router.put("/me", response_model=schemas.User)
def update_user_me(
        db: Session = Depends(deps.get_db),
        password: str = Body(None),
        email: EmailStr = Body(None),
        current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update own user.\n
    Can only provides with the fields which need to be updated.
    """
    current_user_data = jsonable_encoder(current_user)
    user_in = schemas.UserUpdate(**current_user_data)
    if password:
        user_in.password = password
    if email:
        user_in.email = email
    user = crud.user.update(db, db_obj=current_user, obj_in=user_in)
    return user

@router.get("/me", response_model=schemas.User)
def read_user_me(
        current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.post("/open", response_model=schemas.User)
def create_user_open(
        db: Session = Depends(deps.get_db),
        password: str = Body(...),
        email: EmailStr = Body(...)
) -> Any:
    """
    Create new user without the need to be logged in.\n
    This route is used for open-registration.\n
    This route can be turned on/off by toggling {settings.USERS_OPEN_REGISTRATION}.
    """
    if not settings.USERS_OPEN_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Open user registration is forbidden on this server."
        )
    user = crud.user.get_by_email(db, email=email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this username already exists in the system."
        )
    user_in = schemas.UserCreate(password=password, email=email)
    user = crud.user.create(db, obj_in=user_in)
    return user

@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
        user_id: int,
        current_user: models.User = Depends(deps.get_current_active_user),
        db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get a specific user by id.\n
    If the user is not a superuser, then he can only retrieve the user info of himself.
    """
    user = crud.user.get(db, id=user_id)
    if user == current_user:
        return user
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user doesn't have enough privileges."
        )
    return user

# @router.put("/{user_id}", response_model=schemas.User)
# def update_user(
#         *,
#         db: Session = Depends(deps.get_db),
#         user_id: int,
#         user_in: schemas.UserUpdate,
#         current_user: models.User = Depends(deps.get_current_active_superuser)
# ) -> Any:
#     """
#     Update a user.\n
#     To use this route, user must be authenticated as a superuser.
#     """
#     user = crud.user.get(db, id=user_id)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="The user with this username does not exist in the system."
#         )
#     user = crud.user.update(db, db_obj=user, obj_in=user_in)
#     return user

@router.put("/", response_model=schemas.User)
def update_user(
        *,
        db: Session = Depends(deps.get_db),
        user_in: schemas.UserUpdate,
        user=Depends(deps.get_existing_user),
        current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Update a user.\n
    To use this route, user must be authenticated as a superuser.
    """
    user = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user
