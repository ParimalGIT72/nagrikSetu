from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./complaints.db"

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