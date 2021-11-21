from fastapi import APIRouter, HTTPException, status, Request, UploadFile, File, Depends
from typing import List, Any
import concurrent.futures
from starlette.responses import StreamingResponse
import io
import zipfile
from fastapi.responses import JSONResponse
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
# from pydantic.networks import EmailStr

from app.core.config import settings
from app.api.utils import helper_func
from app.api import deps
from app import crud, models, schemas

router = APIRouter()

# @router.post("/create-bucket")
# async def create_bucket(request: Request, bucket_name: str):
#     try:
#         request.app.state.boto3_client.create_bucket(
#             Bucket=bucket_name,
#             CreateBucketConfiguration={"LocationConstraint": request.app.state.boto3_client.meta.region_name}
#         )
#     except ClientError as e:
#         raise HTTPException(
#                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                   detail=f"Bucket creation failed due to: {str(e)}."
#               )
#     return {"message": "Bucket created successfully."}

@router.post("/create-bucket")
async def create_bucket(
        *,
        db: Session = Depends(deps.get_db),
        bucket_in: schemas.BucketCreate,
        current_user: models.User = Depends(deps.get_current_active_user),
        request: Request
) -> Any:
    """
    Create a bucket on AWS S3 under the current user.
    """
    try:
        request.app.state.boto3_client.create_bucket(
            Bucket=jsonable_encoder(bucket_in)["bucket_name"],
            CreateBucketConfiguration={"LocationConstraint": request.app.state.boto3_client.meta.region_name}
        )
    except ClientError as e:
        raise HTTPException(
                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                  detail=f"Bucket creation failed due to: {str(e)}."
              )
    # Create bucket in DB
    bucket = crud.bucket.create_with_owner(db, obj_in=bucket_in, owner_id=current_user.id)
    return bucket

# @router.delete("/delete-bucket")
# async def delete_bucket(
#         *,
#         db: Session = Depends(deps.get_db),
#         bucket_id: int,
#         current_user: models.User = Depends(deps.get_current_active_user),
#         request: Request
# ) -> Any:
#     """
#     Delete a bucket on AWS S3.\n
#     If the current user is a superuser, then he will be able to delete all of the buckets in DB.\n
#     If the current user is not a superuser, then he will only be able to delete the buckets under his account.
#     """
#     bucket_db_obj = crud.bucket.get(db, id=bucket_id)
#     if not bucket_db_obj:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No bucket found with the bucket_id provided."
#         )
#     if not crud.user.is_superuser(current_user) and (bucket_db_obj.owner_id != current_user.id):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     try:
#         bucket = request.app.state.s3.Bucket(bucket_db_obj.bucket_name)
#         bucket.objects.all().delete()
#         bucket.delete()
#         crud.bucket.remove(db, id=bucket_id)
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Deleting bucket failed due to: {str(e)}."
#         )
#     return {"message": "Bucket deleted successfully."}

@router.delete("/delete-bucket")
async def delete_bucket(
        *,
        db: Session = Depends(deps.get_db),
        bucket_id: int,
        bucket_db_obj=Depends(deps.get_bucket_with_permission),
        request: Request
) -> Any:
    """
    Delete a bucket on AWS S3.\n
    If the current user is a superuser, then he will be able to delete all of the buckets in DB.\n
    If the current user is not a superuser, then he will only be able to delete the buckets under his account.
    """
    try:
        bucket = request.app.state.s3.Bucket(bucket_db_obj.bucket_name)
        bucket.objects.all().delete()
        bucket.delete()
        crud.bucket.remove(db, id=bucket_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deleting bucket failed due to: {str(e)}."
        )
    return {"message": "Bucket deleted successfully."}

# @router.get("/list-all-buckets")
# async def list_all_buckets(request: Request):
#     try:
#         response = request.app.state.boto3_client.list_buckets()
#     except ClientError as e:
#         raise HTTPException(
#                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                   detail=f"List all buckets failed due to: {str(e)}."
#               )
#     bucket_name_list = [bucket["Name"] for bucket in response["Buckets"]]
#     return JSONResponse(content=bucket_name_list)

@router.get("/list-all-buckets", response_model=List[schemas.Bucket])
def read_all_buckets(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Retrieve all existing buckets.\n
    User needs to be a superuser to use this api. \n
    Use parameters {skip} and {limit} to control the number of records to return.
    """

    buckets = crud.bucket.get_multi(db, skip=skip, limit=limit)
    return buckets

@router.get("/list-owned-buckets", response_model=List[schemas.Bucket])
def read_owned_buckets(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve buckets owned/created by the current user.\n
    Use parameters {skip} and {limit} to control the number of records to return.
    """

    buckets = crud.bucket.get_multi_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return buckets

@router.get("/list-shared-buckets", response_model=List[schemas.Bucket])
def read_shared_buckets(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve buckets shared to the current user.\n
    Use parameters {skip} and {limit} to control the number of records to return.
    """
    buckets = crud.bucket.get_shared_buckets_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return buckets

# @router.post("/upload")  # Multi-thread version
# async def upload_files(
#         *,
#         db: Session = Depends(deps.get_db),
#         bucket_id: int,
#         request: Request,
#         files: List[UploadFile] = File(...),
#         current_user: models.User = Depends(deps.get_current_active_user)
# ) -> Any:
#     """
#     Upload single/multiple files to the AWS S3 bucket with the given bucket_id.\n
#     If the current user is a superuser, then he will be able to upload to any bucket in DB.\n
#     If the current user is not a superuser, then he will only be able to upload to buckets under his account.
#     """
#     bucket = crud.bucket.get(db, id=bucket_id)
#     if not bucket:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No bucket found with the bucket_id provided."
#         )
#     if not crud.user.is_superuser(current_user) and (bucket.owner_id != current_user.id):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         for file in files:
#             executor.submit(lambda p: request.app.state.boto3_client.upload_fileobj(*p),
#                             (file.file, bucket.bucket_name, file.filename))
#     return {"message": "Uploading has been finished."}

@router.post("/upload")  # Multi-thread version
async def upload_files(
        *,
        request: Request,
        files: List[UploadFile] = File(...),
        bucket=Depends(deps.get_bucket_with_permission)
) -> Any:
    """
    Upload single/multiple files to the AWS S3 bucket with the given bucket_id.\n
    If the current user is a superuser, then he will be able to upload to any bucket in DB.\n
    If the current user is not a superuser, then he will only be able to upload to buckets under his account.
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for file in files:
            executor.submit(lambda p: request.app.state.boto3_client.upload_fileobj(*p),
                            (file.file, bucket.bucket_name, file.filename))
    return {"message": "Uploading has been finished."}

# @router.get("/download")
# async def download_file(request: Request, bucket_name: str, file_name: str):
#     io_stream = io.BytesIO()
#     try:
#         request.app.state.boto3_client.download_fileobj(
#             bucket_name,
#             file_name,
#             io_stream
#         )
#     except ClientError as e:
#         raise HTTPException(
#                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                   detail=f"Downloading file failed due to: {str(e)}."
#               )
#     io_stream.seek(0)
#     return StreamingResponse(io_stream,
#                              headers={"Content-Disposition": f"attachment; filename={file_name}"})

# @router.get("/download")
# async def download_file(
#         *,
#         db: Session = Depends(deps.get_db),
#         bucket_id: int,
#         request: Request,
#         file_name: str,
#         current_user: models.User = Depends(deps.get_current_active_user)
# ) -> Any:
#     """
#     Download a single file with the given file_name from the AWS S3 bucket with the given bucket_id.\n
#     If the current user is a superuser, then he will be able to download from any bucket in DB.\n
#     If the current user is not a superuser, then he will only be able to download from buckets under his account.
#     """
#     bucket = crud.bucket.get(db, id=bucket_id)
#     if not bucket:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No bucket found with the bucket_id provided."
#         )
#     if not crud.user.is_superuser(current_user) and (bucket.owner_id != current_user.id):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     io_stream = io.BytesIO()
#     try:
#         request.app.state.boto3_client.download_fileobj(
#             bucket.bucket_name,
#             file_name,
#             io_stream
#         )
#     except ClientError as e:
#         raise HTTPException(
#                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                   detail=f"Downloading file failed due to: {str(e)}."
#               )
#     io_stream.seek(0)
#     return StreamingResponse(io_stream,
#                              headers={"Content-Disposition": f"attachment; filename={file_name}"})

@router.get("/download")
async def download_file(
        *,
        request: Request,
        file_name: str,
        bucket=Depends(deps.get_bucket_with_permission_shared)
) -> Any:
    """
    Download a single file with the given file_name from the AWS S3 bucket with the given bucket_id.\n
    If the current user is a superuser, then he will be able to download from any bucket in DB.\n
    If the current user is not a superuser, then he will only be able to download from buckets under his account or shared to him.
    """
    io_stream = io.BytesIO()
    try:
        request.app.state.boto3_client.download_fileobj(
            bucket.bucket_name,
            file_name,
            io_stream
        )
    except ClientError as e:
        raise HTTPException(
                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                  detail=f"Downloading file failed due to: {str(e)}."
              )
    io_stream.seek(0)
    return StreamingResponse(io_stream,
                             headers={"Content-Disposition": f"attachment; filename={file_name}"})

# @router.get("/download-zip")
# async def download_zip(request: Request, bucket_name: str):
#     bucket = request.app.state.s3.Bucket(bucket_name)
#     file_names = [obj.key for obj in bucket.objects.all()]
#     zip_io = io.BytesIO()
#     with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zipped:
#         for file_name in file_names:
#             io_stream = io.BytesIO()
#             request.app.state.boto3_client.download_fileobj(
#                 bucket_name,
#                 file_name,
#                 io_stream
#             )
#             io_stream.seek(0)
#             zipped.writestr(file_name, io_stream.read())
#     zip_io.seek(0)
#     response = StreamingResponse(zip_io, media_type="application/x-zip-compressed")
#     response.headers["Content-Disposition"] = f"attachment; filename={bucket_name}.zip"
#     return response

# @router.get("/download-zip")  # Multi-thread version
# async def download_zip(request: Request, bucket_name: str):
#     bucket = request.app.state.s3.Bucket(bucket_name)
#     file_names = [obj.key for obj in bucket.objects.all()]
#     zip_io = io.BytesIO()
#     with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zipped:
#         with concurrent.futures.ThreadPoolExecutor() as executor:
#             for file_name in file_names:
#                 executor.submit(lambda p: helper_func(*p),
#                                 (zipped, request, bucket_name, file_name))
#     zip_io.seek(0)
#     response = StreamingResponse(zip_io, media_type="application/x-zip-compressed")
#     response.headers["Content-Disposition"] = f"attachment; filename={bucket_name}.zip"
#     return response

# @router.get("/download-zip")  # Multi-thread version
# async def download_zip(
#         *,
#         db: Session = Depends(deps.get_db),
#         bucket_id: int,
#         request: Request,
#         current_user: models.User = Depends(deps.get_current_active_user)
# ) -> Any:
#     """
#     Download all the files as a zip from the AWS S3 bucket with the given bucket_id.\n
#     If the current user is a superuser, then he will be able to download from any bucket in DB.\n
#     If the current user is not a superuser, then he will only be able to download from buckets under his account.
#     """
#     bucket_db_obj = crud.bucket.get(db, id=bucket_id)
#     if not bucket_db_obj:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No bucket found with the bucket_id provided."
#         )
#     if not crud.user.is_superuser(current_user) and (bucket_db_obj.owner_id != current_user.id):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     # bucket = request.app.state.s3.Bucket(bucket_db_obj.bucket_name)
#     try:
#         bucket = request.app.state.s3.Bucket(bucket_db_obj.bucket_name)
#     except ClientError as e:
#         raise HTTPException(
#                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                   detail=f"Getting bucket info failed due to: {str(e)}."
#               )
#     file_names = [obj.key for obj in bucket.objects.all()]
#     zip_io = io.BytesIO()
#     with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zipped:
#         with concurrent.futures.ThreadPoolExecutor() as executor:
#             for file_name in file_names:
#                 executor.submit(lambda p: helper_func(*p),
#                                 (zipped, request, bucket_db_obj.bucket_name, file_name))
#     zip_io.seek(0)
#     response = StreamingResponse(zip_io, media_type="application/x-zip-compressed")
#     response.headers["Content-Disposition"] = f"attachment; filename={bucket_db_obj.bucket_name}.zip"
#     return response

@router.get("/download-zip")  # Multi-thread version
async def download_zip(
        *,
        request: Request,
        bucket_db_obj=Depends(deps.get_bucket_with_permission_shared)
) -> Any:
    """
    Download all the files as a zip from the AWS S3 bucket with the given bucket_id.\n
    If the current user is a superuser, then he will be able to download from any bucket in DB.\n
    If the current user is not a superuser, then he will only be able to download from buckets under his account or shared to him.
    """
    try:
        bucket = request.app.state.s3.Bucket(bucket_db_obj.bucket_name)
    except ClientError as e:
        raise HTTPException(
                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                  detail=f"Getting bucket info failed due to: {str(e)}."
              )
    file_names = [obj.key for obj in bucket.objects.all()]
    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zipped:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for file_name in file_names:
                executor.submit(lambda p: helper_func(*p),
                                (zipped, request, bucket_db_obj.bucket_name, file_name))
    zip_io.seek(0)
    response = StreamingResponse(zip_io, media_type="application/x-zip-compressed")
    response.headers["Content-Disposition"] = f"attachment; filename={bucket_db_obj.bucket_name}.zip"
    return response

# @router.delete("/delete")
# async def delete_file(
#         *,
#         db: Session = Depends(deps.get_db),
#         bucket_id: int,
#         request: Request,
#         file_name: str,
#         current_user: models.User = Depends(deps.get_current_active_user)
# ) -> Any:
#     """
#     Download a single file with the given file_name from the AWS S3 bucket with the given bucket_id.\n
#     If the current user is a superuser, then he will be able to download from any bucket in DB.\n
#     If the current user is not a superuser, then he will only be able to download from buckets under his account.
#     """
#     bucket_db_obj = crud.bucket.get(db, id=bucket_id)
#     if not bucket_db_obj:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No bucket found with the bucket_id provided."
#         )
#     if not crud.user.is_superuser(current_user) and (bucket_db_obj.owner_id != current_user.id):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     try:
#         obj = request.app.state.s3.Object(bucket_db_obj.bucket_name, file_name)
#         obj.delete()
#     except ClientError as e:
#         raise HTTPException(
#                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                   detail=f"Deleting file failed due to: {str(e)}."
#               )
#     return {"message": "File deleted successfully."}

@router.delete("/delete")
async def delete_file(
        *,
        request: Request,
        file_name: str,
        bucket_db_obj=Depends(deps.get_bucket_with_permission)
) -> Any:
    """
    Delete a single file with the given file_name from the AWS S3 bucket with the given bucket_id.\n
    If the current user is a superuser, then he will be able to delete from any bucket in DB.\n
    If the current user is not a superuser, then he will only be able to delete from buckets under his account.
    """
    try:
        obj = request.app.state.s3.Object(bucket_db_obj.bucket_name, file_name)
        obj.delete()
    except ClientError as e:
        raise HTTPException(
                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                  detail=f"Deleting file failed due to: {str(e)}."
              )
    return {"message": "File deleted successfully."}

# @router.delete("/empty-bucket")
# async def empty_bucket(
#         *,
#         db: Session = Depends(deps.get_db),
#         bucket_id: int,
#         current_user: models.User = Depends(deps.get_current_active_user),
#         request: Request
# ) -> Any:
#     """
#     Empty a bucket on AWS S3.\n
#     If the current user is a superuser, then he will be able to empty all of the buckets in DB.\n
#     If the current user is not a superuser, then he will only be able to empty the buckets under his account.
#     """
#     bucket_db_obj = crud.bucket.get(db, id=bucket_id)
#     if not bucket_db_obj:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No bucket found with the bucket_id provided."
#         )
#     if not crud.user.is_superuser(current_user) and (bucket_db_obj.owner_id != current_user.id):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     try:
#         bucket = request.app.state.s3.Bucket(bucket_db_obj.bucket_name)
#         bucket.objects.all().delete()
#     except ClientError as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Emptying bucket failed due to: {str(e)}."
#         )
#     return {"message": "Bucket emptied successfully."}

@router.delete("/empty-bucket")
async def empty_bucket(
        *,
        bucket_db_obj=Depends(deps.get_bucket_with_permission),
        request: Request
) -> Any:
    """
    Empty a bucket on AWS S3.\n
    If the current user is a superuser, then he will be able to empty all of the buckets in DB.\n
    If the current user is not a superuser, then he will only be able to empty the buckets under his account.
    """
    try:
        bucket = request.app.state.s3.Bucket(bucket_db_obj.bucket_name)
        bucket.objects.all().delete()
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Emptying bucket failed due to: {str(e)}."
        )
    return {"message": "Bucket emptied successfully."}

# @router.get("/get-s3-info")
# async def get_s3_info(
#         *,
#         current_user: models.User = Depends(deps.get_current_active_user)
# ) -> Any:
#     """
#     Retrieve the AWS S3 related info.\n
#     To use this route, user must be authenticated as a superuser.
#     """
#     if not crud.user.is_superuser(current_user):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     return {
#         "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
#         "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
#         "region": settings.REGION
#     }

@router.get("/get-s3-info")
async def get_s3_info(
        *,
        current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Retrieve the AWS S3 related info.\n
    To use this route, user must be authenticated as a superuser.
    """
    return {
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        "region": settings.REGION
    }

# @router.get("/get-file-names-in-bucket")
# async def get_file_names_in_bucket(
#         *,
#         db: Session = Depends(deps.get_db),
#         bucket_id: int,
#         request: Request,
#         current_user: models.User = Depends(deps.get_current_active_user)
# ) -> Any:
#     """
#     Retrieve all the file names from the AWS S3 bucket with the given bucket_id.\n
#     If the current user is a superuser, then he will be able to retrieve the info from any bucket in DB.\n
#     If the current user is not a superuser, then he will only be able to retrieve the info from buckets under his
#     account.
#     """
#     bucket_db_obj = crud.bucket.get(db, id=bucket_id)
#     if not bucket_db_obj:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No bucket found with the bucket_id provided."
#         )
#     if not crud.user.is_superuser(current_user) and (bucket_db_obj.owner_id != current_user.id):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     try:
#         bucket = request.app.state.s3.Bucket(bucket_db_obj.bucket_name)
#     except ClientError as e:
#         raise HTTPException(
#                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                   detail=f"Getting bucket info failed due to: {str(e)}."
#               )
#     file_names = [obj.key for obj in bucket.objects.all()]
#     return JSONResponse(content=file_names)

@router.get("/get-file-names-in-bucket")
async def get_file_names_in_bucket(
        *,
        request: Request,
        bucket_db_obj=Depends(deps.get_bucket_with_permission_shared)
) -> Any:
    """
    Retrieve all the file names from the AWS S3 bucket with the given bucket_id.\n
    If the current user is a superuser, then he will be able to retrieve the info from any bucket in DB.\n
    If the current user is not a superuser, then he will only be able to retrieve the info from buckets under his
    account or shared to him.
    """
    try:
        bucket = request.app.state.s3.Bucket(bucket_db_obj.bucket_name)
    except ClientError as e:
        raise HTTPException(
                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                  detail=f"Getting bucket info failed due to: {str(e)}."
              )
    file_names = [obj.key for obj in bucket.objects.all()]
    return JSONResponse(content=file_names)

# @router.post("/share")
# async def share_with_user(
#         *,
#         db: Session = Depends(deps.get_db),
#         bucket_id: int,
#         user_email: EmailStr,
#         current_user: models.User = Depends(deps.get_current_user)
# ) -> Any:
#     """
#     Share bucket with other users (registered email needs to be provided) by bucket id.\n
#     The bucket to share needs to belong to the current user, otherwise, the current user needs to be a superuser.
#     """
#     bucket = crud.bucket.get(db, id=bucket_id)
#     if not bucket:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No bucket found with the bucket_id provided."
#         )
#     user_to_share = crud.user.get_by_email(db, email=user_email)
#     if not user_to_share:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No user found with the email provided."
#         )
#     if not crud.user.is_superuser(current_user) and bucket not in current_user.buckets:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     if user_to_share.id == bucket.owner_id:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Cannot share his own bucket to himself."
#         )
#     # Share the bucket to user_to_share
#     if bucket not in user_to_share.shared_buckets:
#         user_to_share.shared_buckets.append(bucket)
#         db.commit()
#     return {"message": "Bucket shared with user successfully."}

@router.post("/share")
async def share_with_user(
        *,
        db: Session = Depends(deps.get_db),
        bucket=Depends(deps.get_bucket_with_permission),
        user_to_share=Depends(deps.get_existing_user_by_email)
) -> Any:
    """
    Share bucket with other users (registered email needs to be provided) by bucket id.\n
    The bucket to share needs to belong to the current user, otherwise, the current user needs to be a superuser.
    """
    if user_to_share.id == bucket.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot share his own bucket to himself."
        )
    # Share the bucket to user_to_share
    if bucket not in user_to_share.shared_buckets:
        user_to_share.shared_buckets.append(bucket)
        db.commit()
    return {"message": "Bucket shared with user successfully."}

# @router.post("/stop-share")
# async def stop_share_with_user(
#         *,
#         db: Session = Depends(deps.get_db),
#         bucket_id: int,
#         user_id: int,
#         current_user: models.User = Depends(deps.get_current_user)
# ) -> Any:
#     """
#     Stop sharing buckets with other users.\n
#     User id and bucket id needs to be provided.\n
#     The bucket to stop sharing needs to belong to the current user, otherwise, the current user needs to be a superuser.
#     """
#     bucket = crud.bucket.get(db, id=bucket_id)
#     if not bucket:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No bucket found with the bucket_id provided."
#         )
#     user = crud.user.get(db, id=user_id)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No user found with the id provided."
#         )
#     if not crud.user.is_superuser(current_user) and bucket not in current_user.buckets:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     # Stop sharing the bucket to user_to_share
#     if bucket in user.shared_buckets:
#         user.shared_buckets.remove(bucket)
#         db.commit()
#     return {"message": "Bucket sharing stopped with user successfully."}

@router.post("/stop-share")
async def stop_share_with_user(
        *,
        db: Session = Depends(deps.get_db),
        bucket=Depends(deps.get_bucket_with_permission),
        user=Depends(deps.get_existing_user)
) -> Any:
    """
    Stop sharing bucket with other users.\n
    User id and bucket id needs to be provided.\n
    The bucket to stop sharing needs to belong to the current user, otherwise, the current user needs to be a superuser.
    """
    # Stop sharing the bucket to user_to_share
    if bucket in user.shared_buckets:
        user.shared_buckets.remove(bucket)
        db.commit()
    return {"message": "Bucket sharing stopped with user successfully."}

# @router.get("/retrieve-shared-users", response_model=List[schemas.User])
# async def retrieve_shared_users(
#         *,
#         db: Session = Depends(deps.get_db),
#         bucket_id: int,
#         current_user: models.User = Depends(deps.get_current_active_user)
# ) -> Any:
#     """
#     Retrieve the shared users for a bucket (bucket id needs to be provided).\n
#     The bucket to retrieve shared users needs to belong to the current user, otherwise, the current user needs to be a superuser.
#     """
#     bucket = crud.bucket.get(db, id=bucket_id)
#     if not bucket:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No bucket found with the bucket_id provided."
#         )
#     if not crud.user.is_superuser(current_user) and bucket not in current_user.buckets:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     return list(bucket.shared_users)

@router.get("/retrieve-shared-users", response_model=List[schemas.UserReduced])
async def retrieve_shared_users(
        *,
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        bucket=Depends(deps.get_bucket_with_permission)
) -> Any:
    """
    Retrieve the shared users for a bucket (bucket id needs to be provided).\n
    The bucket to retrieve shared users needs to belong to the current user, otherwise, the current user needs to be a superuser.
    """
    # return list(bucket.shared_users)
    return crud.bucket.get_shared_users_by_bucket(db, bucket_id=bucket.id, skip=skip, limit=limit)

# @router.get("/retrieve-metadata-by-bucket", response_model=schemas.BucketMetadata)
# async def retrieve_metadata_by_bucket(
#         bucket_id: int,
#         db: Session = Depends(deps.get_db),
#         current_user: models.User = Depends(deps.get_current_active_user)
# ) -> Any:
#     """
#     Retrieve bucket metadata with given bucket id.\n
#     The bucket to retrieve metadata needs to belong to the current user, otherwise, the current user needs to be a superuser.
#     """
#     bucket = crud.bucket.get(db, id=bucket_id)
#     if not bucket:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No bucket found with the bucket_id provided."
#         )
#     if not crud.user.is_superuser(current_user) and bucket not in current_user.buckets:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     return crud.bucket_metadata.get_by_bucket_id(db, bucket_id=bucket_id)

@router.get("/retrieve-metadata-by-bucket", response_model=schemas.BucketMetadata)
async def retrieve_metadata_by_bucket(
        # bucket_id: int,
        db: Session = Depends(deps.get_db),
        bucket=Depends(deps.get_bucket_with_permission_shared)
) -> Any:
    """
    Retrieve bucket metadata with given bucket id.\n
    The bucket to retrieve metadata needs to belong to the current user or shared to him, otherwise, the current user needs to be a superuser.
    """
    return crud.bucket_metadata.get_by_bucket_id(db, bucket_id=bucket.id)

# @router.post("/metadata", response_model=schemas.BucketMetadata)
# async def create_metadata(
#         *,
#         db: Session = Depends(deps.get_db),
#         metadata_in: schemas.BucketMetadataCreate,
#         bucket_id: int,
#         current_user: models.User = Depends(deps.get_current_active_user)
# ) -> Any:
#     """
#     Create new metadata with provided bucket id.\n
#     The bucket needs to belong to the current user, otherwise, the current user needs to be a superuser.
#     """
#     bucket = crud.bucket.get(db, id=bucket_id)
#     if not bucket:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No bucket found with the bucket_id provided."
#         )
#     if not crud.user.is_superuser(current_user) and bucket not in current_user.buckets:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     bucket_metadata = crud.bucket_metadata.create_with_bucket(db, obj_in=metadata_in, bucket_id=bucket_id)
#     return bucket_metadata

@router.post("/metadata", response_model=schemas.BucketMetadata)
async def create_metadata(
        *,
        db: Session = Depends(deps.get_db),
        metadata_in: schemas.BucketMetadataCreate,
        bucket=Depends(deps.get_bucket_with_permission)
) -> Any:
    """
    Create new metadata with provided bucket id.\n
    The bucket needs to belong to the current user, otherwise, the current user needs to be a superuser.
    """
    bucket_metadata = crud.bucket_metadata.create_with_bucket(db, obj_in=metadata_in, bucket_id=bucket.id)
    return bucket_metadata

# @router.put("/metadata/{id}", response_model=schemas.BucketMetadata)
# def update_metadata(
#         *,
#         db: Session = Depends(deps.get_db),
#         id: int,
#         metadata_in: schemas.BucketMetadataUpdate,
#         current_user: models.User = Depends(deps.get_current_active_user)
# ) -> Any:
#     """
#     Update a bucket metadata with given id (bucket metadata's id).\n
#     The bucket the metadata belongs to needs to belong to the current user, otherwise, the current user needs to be a superuser.
#     """
#     bucket_metadata = crud.bucket_metadata.get(db, id=id)
#     if not bucket_metadata:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No bucket metadata found with the id provided."
#         )
#     if not crud.user.is_superuser(current_user) and bucket_metadata.bucket_id not \
#             in [bucket.id for bucket in current_user.buckets]:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     bucket_metadata = crud.bucket_metadata.update(db, db_obj=bucket_metadata, obj_in=metadata_in)
#     return bucket_metadata

@router.put("/metadata", response_model=schemas.BucketMetadata)
def update_metadata(
        *,
        db: Session = Depends(deps.get_db),
        metadata_in: schemas.BucketMetadataUpdate,
        bucket_metadata=Depends(deps.get_bucket_metadata_with_permission)
) -> Any:
    """
    Update a bucket metadata with given id (bucket metadata's id).\n
    The bucket the metadata belongs to needs to belong to the current user, otherwise, the current user needs to be a superuser.
    """
    bucket_metadata = crud.bucket_metadata.update(db, db_obj=bucket_metadata, obj_in=metadata_in)
    return bucket_metadata

# @router.get("/metadata/{id}", response_model=schemas.BucketMetadata)
# async def retrieve_metadata_by_id(
#         *,
#         db: Session = Depends(deps.get_db),
#         id: int,
#         current_user: models.User = Depends(deps.get_current_active_user)
# ) -> Any:
#     """
#     Retrieve metadata by id (bucket metadata's id).\n
#     The bucket the metadata belongs to needs to belong to the current user, otherwise, the current user needs to be a superuser.
#     """
#     bucket_metadata = crud.bucket_metadata.get(db, id=id)
#     if not bucket_metadata:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No bucket metadata found with the id provided."
#         )
#     if not crud.user.is_superuser(current_user) and bucket_metadata.bucket_id not \
#             in [bucket.id for bucket in current_user.buckets]:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     return bucket_metadata

@router.get("/metadata", response_model=schemas.BucketMetadata)
async def retrieve_metadata_by_id(
        *,
        bucket_metadata=Depends(deps.get_bucket_metadata_with_permission_shared)
) -> Any:
    """
    Retrieve metadata by id (bucket metadata's id).\n
    The bucket the metadata belongs to needs to belong to the current user or shared to him, otherwise, the current user needs to be a superuser.
    """
    return bucket_metadata

# @router.delete("/metadata/{id}", response_model=schemas.BucketMetadata)
# async def delete_metadata(
#         *,
#         db: Session = Depends(deps.get_db),
#         id: int,
#         current_user: models.User = Depends(deps.get_current_active_user)
# ) -> Any:
#     """
#     Delete an bucket metadata by id (bucket metadata's id).\n
#     The bucket the metadata belongs to needs to belong to the current user, otherwise, the current user needs to be a superuser.
#     """
#     bucket_metadata = crud.bucket_metadata.get(db, id=id)
#     if not bucket_metadata:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"No bucket metadata found with the id provided."
#         )
#     if not crud.user.is_superuser(current_user) and bucket_metadata.bucket_id not \
#             in [bucket.id for bucket in current_user.buckets]:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Not enough permissions."
#         )
#     bucket_metadata = crud.bucket_metadata.remove(db, id=id)
#     return bucket_metadata

@router.delete("/metadata", response_model=schemas.BucketMetadata)
async def delete_metadata(
        *,
        db: Session = Depends(deps.get_db),
        bucket_metadata=Depends(deps.get_bucket_metadata_with_permission)
) -> Any:
    """
    Delete an bucket metadata by id (bucket metadata's id).\n
    The bucket the metadata belongs to needs to belong to the current user, otherwise, the current user needs to be a superuser.
    """
    bucket_metadata = crud.bucket_metadata.remove(db, id=bucket_metadata.id)
    return bucket_metadata

