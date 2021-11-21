from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def welcome():
    """
    Route to test the server.
    """
    return {"message": "This is file_server!"}
