import io
from fastapi import HTTPException, status, File, UploadFile
import pandas as pd

def helper_func(zipped, request, bucket_name, file_name):
    io_stream = io.BytesIO()
    request.app.state.boto3_client.download_fileobj(
        bucket_name,
        file_name,
        io_stream
    )
    io_stream.seek(0)
    zipped.writestr(file_name, io_stream.read())

def preprocess_file_name(file_name):
    try:
        preprocessed_name = file_name.lower()
        preprocessed_name = preprocessed_name.replace(" ", "_")
        if preprocessed_name.count(".") > 1:
            preprocessed_name = preprocessed_name.replace(".", "_", preprocessed_name.count(".") - 1)
        if "+" in preprocessed_name:
            preprocessed_name = preprocessed_name.replace("+", "_")
        if "-" in preprocessed_name:
            preprocessed_name = preprocessed_name.replace("-", "_")
        return preprocessed_name
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preprocessing filename failed due to {str(e)}."
        )

def get_suffix(file_name):
    suffix = file_name.split(".")[-1].lower()
    return suffix

def get_df(preprocessed_file_name: str, file: UploadFile = File(...)):
    # Get file suffix
    suffix = get_suffix(preprocessed_file_name)
    if suffix == "csv":  # For .csv files
        df = pd.read_csv(io.BytesIO(file.file.read()))
    elif suffix in ["xls", "xlsx", "xlsm"]:  # For Excel files
        df = pd.read_excel(io.BytesIO(file.file.read()))
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not supported."
        )
    return df

def preprocess_df(df):
    original_names = list(df.columns)
    new_names = [original_name.lower() for original_name in original_names]
    if "id" in new_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The original file cannot contain columns named id, Id, iD or ID."
        )
    new_names = [new_name.replace(" ", "_") for new_name in new_names]
    new_names_final = []
    for new_name in new_names:
        if "+" in new_name:
            # new_name = new_name.split("+")[0]
            new_name = new_name.replace("+", "_")
        if "." in new_name:
            new_name = new_name.replace(".", "_")
        if "," in new_name:
            new_name = new_name.replace(",", "_")
        if "-" in new_name:
            new_name = new_name.replace("-", "_")
        new_names_final.append(new_name)
    df.columns = new_names_final
    return df
