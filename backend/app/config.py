from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # File Storage
    UPLOAD_DIR: Path = Path("uploads")
    MAX_FILE_SIZE_MB: int = 5
    ALLOWED_IMAGE_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp"}
    ALLOWED_IMAGE_MIME_TYPES: set[str] = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    # API Settings
    APP_NAME: str = "Nagrik Setu API"
    APP_VERSION: str = "0.2.0"
    DEBUG: bool = False

    # Authentication and browser clients
    FRONTEND_ORIGINS: list[str] = Field(default_factory=list)
    JWT_SECRET_KEY: str = ""
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=1, le=1440)
    JWT_ISSUER: str = "nagrik-setu-api"
    JWT_AUDIENCE: str = "nagrik-setu-client"

    # ML & Preprocessing Models
    FASTTEXT_MODEL_PATH: Path = Path(__file__).resolve().parent.parent.parent / "ml" / "models" / "fasttext" / "lid.176.ftz"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()