from pydantic import BaseSettings, EmailStr
import secrets

class Settings(BaseSettings):
    PROJECT_NAME: str = "file_server"

    API_V1_STR: str = "/api/v1"

    # MySQL
    SQLALCHEMY_DATABASE_URI: str = "mysql+pymysql://root:rapid@db:3306/rapid_data_hub"

    SECRET_KEY: str = secrets.token_urlsafe(32)

    # 60 minutes * 24 hours * 7 days = 7 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    FIRST_SUPERUSER: EmailStr = "admin@rapid.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin"
    USERS_OPEN_REGISTRATION: bool = False

    # S3 related
    AWS_ACCESS_KEY_ID: str = "AKIA455JKBQTBCC5WVA7"
    AWS_SECRET_ACCESS_KEY: str = "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"
    REGION: str = "us-west-2"

    class Config:
        case_sensitive = True

settings = Settings()
