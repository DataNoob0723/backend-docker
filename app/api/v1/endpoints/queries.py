from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app import models, crud
from app.db.session import engine

router = APIRouter()

@router.get("/all-table-names")
async def get_all_table_names(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Retrieve all tables' names.\n
    User needs to be a superuser to use this api. \n
    Use parameters {skip} and {limit} to control the number of records to return.
    """
    tables = crud.table.get_multi(db, skip=skip, limit=limit)
    table_names = [table.table_name for table in tables]
    return {"table_names": table_names}

@router.get("/owned-table-names")
async def get_owned_table_names(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve the available table names from the database. \n
    The tables must be created by the user. \n
    Use parameters {skip} and {limit} to control the number of records to return.
    """
    tables = crud.table.get_multi_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    table_names = [table.table_name for table in tables]
    return {"table_names": table_names}

# @router.get("/shared-table-names")
# async def get_shared_table_names(
#         db: Session = Depends(deps.get_db),
#         skip: int = 0,
#         limit: int = 100,
#         current_user: models.User = Depends(deps.get_current_active_user)
# ) -> Any:
#     """
#     Retrieve the available table names from the database. \n
#     The tables must be shared to the user by other users. \n
#     Use parameters {skip} and {limit} to control the number of records to return.
#     """
#     tables = crud.table.get_shared_tables_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
#     table_names = [table.table_name for table in tables]
#     return {"table_names": table_names}
#
# @router.get("/{table_name}")
# async def query(
#         *,
#         db: Session = Depends(deps.get_db),
#         model=Depends(deps.get_model_with_permission_shared),
#         attr_names: Optional[List[str]] = Query(None),
#         skip: int = 0,
#         limit: int = 10
# ) -> Any:
#     """
#     Query data from database with table_name provided. \n
#     The table must be owned by the user or shared to the user by other users. \n
#     Use attr_names to control the fields in the response, if none, all the fields in the table will be returned. \n
#     Use parameters {skip} and {limit} to control the number of records to return.
#     """
#     if attr_names:
#         model_attrs = []
#         for attr_name in attr_names:
#             model_attr = getattr(model, attr_name, None)
#             if not model_attr:
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail=f"No corresponding attribute name: {attr_name} for the table!"
#                 )
#             model_attrs.append(model_attr)
#         return db.query(*model_attrs).offset(skip).limit(limit).all()
#     print("aaa")
#     print(model)
#     print(db.query(model).offset(skip).limit(limit).all())
#     return db.query(model).offset(skip).limit(limit).all()

@router.get("/shared-table-names")
async def get_shared_table_names(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve the available table names from the database. \n
    The tables must be shared to the user by other users. \n
    Use parameters {skip} and {limit} to control the number of records to return.
    """
    tables = crud.table.get_shared_tables_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    table_names = [table.table_name for table in tables]
    return {"table_names": table_names}

@router.get("/{table_name}")
async def query(
        *,
        model=Depends(deps.get_model_with_permission_shared),
        attr_names: Optional[List[str]] = Query(None),
        skip: int = 0,
        limit: int = 10,
        table_name: str
) -> Any:
    """
    Query data from database with table_name provided. \n
    The table must be owned by the user or shared to the user by other users. \n
    Use attr_names to control the fields in the response, if none, all the fields in the table will be returned. \n
    Use parameters {skip} and {limit} to control the number of records to return.
    """
    if attr_names:
        model_attrs = []
        for attr_name in attr_names:
            model_attr = getattr(model, attr_name, None)
            if not model_attr:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No corresponding attribute name: {attr_name} for the table!"
                )
            model_attrs.append(attr_name)
        joined_str = ", ".join(model_attrs)
        with engine.connect() as con:
            results = con.execute(f"SELECT {joined_str} FROM {table_name} LIMIT {limit} OFFSET {skip};")
            return [dict(row) for row in results]
    with engine.connect() as con:
        results = con.execute(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {skip};")
    return [dict(row) for row in results]

# @router.get("/{table_name}/total-number-of-records")
# async def get_total_num_of_records(
#         *,
#         db: Session = Depends(deps.get_db),
#         model=Depends(deps.get_model_with_permission_shared)
# ) -> Any:
#     """
#     Retrieve the total number of records from the table. \n
#     The table must be owned by the user or shared to the user by other users.
#     """
#     total_num_of_records = db.query(model).count()
#     return {"total_num_of_records": total_num_of_records}

@router.get("/{table_name}/total-number-of-records")
async def get_total_num_of_records(
        *,
        model=Depends(deps.get_model_with_permission_shared),
        table_name: str
) -> Any:
    """
    Retrieve the total number of records from the table. \n
    The table must be owned by the user or shared to the user by other users.
    """
    with engine.connect() as con:
        result = con.execute(f"SELECT COUNT(*) FROM {table_name};")
        total_num_of_records = list(result)[0][0]
    return {"total_num_of_records": total_num_of_records}

@router.get("/{table_name}/column-names")
async def get_column_names(
        *,
        model=Depends(deps.get_model_with_permission_shared)
) -> Any:
    """
    Retrieve the column names of the table. \n
    The table must be owned by the user or shared to the user by other users.
    """
    column_names = model.__table__.columns.keys()
    return {"column_names": column_names}


