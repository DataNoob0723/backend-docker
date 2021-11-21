from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Any
from sqlalchemy.orm import Session

from app.api import deps
from app import models, schemas, crud

router = APIRouter()

@router.get("/list-all-tables", response_model=List[schemas.Table])
def read_all_tables(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Retrieve all existing tables.\n
    User needs to be a superuser to use this api. \n
    Use parameters {skip} and {limit} to control the number of records to return.
    """
    tables = crud.table.get_multi(db, skip=skip, limit=limit)
    return tables

@router.get("/list-owned-tables", response_model=List[schemas.Table])
def read_owned_tables(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve tables owned/created by the current user.\n
    Use parameters {skip} and {limit} to control the number of records to return.
    """
    tables = crud.table.get_multi_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return tables

@router.get("/list-shared-tables", response_model=List[schemas.Table])
def read_shared_tables(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve tables shared to the current user.\n
    Use parameters {skip} and {limit} to control the number of records to return.
    """
    tables = crud.table.get_shared_tables_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return tables

@router.post("/", response_model=schemas.Table)
async def create_table(
        *,
        db: Session = Depends(deps.get_db),
        table_in: schemas.TableCreate,
        current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Create new table for the current user.
    """
    table = crud.table.create_with_owner(db, obj_in=table_in, owner_id=current_user.id)
    return table

@router.put("/", response_model=schemas.Table)
def update_table(
        *,
        db: Session = Depends(deps.get_db),
        table_in: schemas.TableUpdate,
        table=Depends(deps.get_table_with_permission)
) -> Any:
    """
    Update a table with given id (table's id).\n
    The table needs to belong to the current user, otherwise, the current user needs to be a superuser.
    """
    table = crud.table.update(db, db_obj=table, obj_in=table_in)
    return table

@router.delete("/", response_model=schemas.Table)
async def delete_table(
        *,
        db: Session = Depends(deps.get_db),
        table=Depends(deps.get_table_with_permission)
) -> Any:
    """
    Delete a table by id (table's id).\n
    The table needs to belong to the current user, otherwise, the current user needs to be a superuser.
    """
    table = crud.table.remove(db, id=table.id)
    return table

@router.post("/share")
async def share_with_user(
        *,
        db: Session = Depends(deps.get_db),
        table=Depends(deps.get_table_with_permission),
        user_to_share=Depends(deps.get_existing_user_by_email)
) -> Any:
    """
    Share table with other users (registered email needs to be provided) by table id.\n
    The table to share needs to belong to the current user, otherwise, the current user needs to be a superuser.
    """
    if user_to_share.id == table.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot share his own table to himself."
        )
    # Share the table to user_to_share
    if table not in user_to_share.shared_tables:
        user_to_share.shared_tables.append(table)
        db.commit()
    return {"message": "Table shared with user successfully."}

@router.post("/stop-share")
async def stop_share_with_user(
        *,
        db: Session = Depends(deps.get_db),
        table=Depends(deps.get_table_with_permission),
        user=Depends(deps.get_existing_user)
) -> Any:
    """
    Stop sharing table with other users.\n
    User id and table id needs to be provided.\n
    The table to stop sharing needs to belong to the current user, otherwise, the current user needs to be a superuser.
    """
    # Stop sharing the table to user_to_share
    if table in user.shared_tables:
        user.shared_tables.remove(table)
        db.commit()
    return {"message": "Table sharing stopped with user successfully."}

@router.get("/retrieve-shared-users", response_model=List[schemas.UserReduced])
async def retrieve_shared_users(
        *,
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        table=Depends(deps.get_table_with_permission)
) -> Any:
    """
    Retrieve the shared users for a table (table id needs to be provided).\n
    The table to retrieve shared users needs to belong to the current user, otherwise, the current user needs to be a superuser.
    """
    return crud.table.get_shared_users_by_table(db, table_id=table.id, skip=skip, limit=limit)
