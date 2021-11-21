from fastapi import APIRouter

from app.api.v1.endpoints import test, files, login, users, queries, save, tables

api_router = APIRouter()
# Test
api_router.include_router(test.router, prefix="/test", tags=["test"])
# Login
api_router.include_router(login.router, tags=["login"])
# Users
api_router.include_router(users.router, prefix="/users", tags=["users"])
# File related Apis
api_router.include_router(files.router, prefix="/files", tags=["files"])
# Save data to database
api_router.include_router(save.router, prefix="/save", tags=["save"])
# Query data from database
api_router.include_router(queries.router, prefix="/queries", tags=["queries"])
# Tables
api_router.include_router(tables.router, prefix="/tables", tags=["tables"])
