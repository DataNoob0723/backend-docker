from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.utils import preprocess_df, preprocess_file_name, get_df
from app.api import deps
from app.db.session import engine
from app import models, crud

router = APIRouter()

@router.post("/")
async def upload_file(
        file: UploadFile = File(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Upload a file and save it into database. \n
    Currently only .csv files and MS Excel files are supported.
    """
    preprocessed_file_name = preprocess_file_name(file.filename)
    table_name = preprocessed_file_name.split(".")[0]
    if table_name.isnumeric():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name cannot be pure numbers."
        )
    # Need to check if table_name is unique
    table = crud.table.get_by_table_name(db, table_name=table_name)
    if table:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Table with table_name: {table_name} already exists in the database, try renaming the file."
        )
    df = get_df(preprocessed_file_name, file)
    df = preprocess_df(df)
    df.index += 1
    df.to_sql(name=table_name, con=engine, if_exists='replace')
    with engine.connect() as con:
        con.execute(f'ALTER TABLE {table_name} RENAME COLUMN `index` TO `id`;')
        con.execute(f'ALTER TABLE {table_name} ADD PRIMARY KEY (`id`);')
    return {
        "message": "Saved to DB successfully.",
        "table_name": table_name,
        "original_file_name": file.filename
    }

@router.delete("/{table_name}")
async def drop_table(
        model=Depends(deps.get_model_with_permission)
):
    """
    Delete a table from database.
    """
    try:
        print(model)
        model.__table__.drop(engine)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete table failed due to {str(e)}."
        )
    return {"message": "Table deleted successfully from database."}
