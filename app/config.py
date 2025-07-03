from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    GOOGLE_API_KEY: str = Field(..., description="Google Gemini API key")

    # Server Configuration
    PORT: int = Field(default=8000, description="Server port")
    HOST: str = Field(default="0.0.0.0", description="Server host")

    # AI Model Configuration
    MODEL_NAME: str = Field(
        default="gemini-2.5-flash-lite-preview-06-17",
        description="Gemini model name"
    )

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_DB: int = Field(default=0, description="Redis database number")

    # File Upload Configuration
    UPLOAD_FOLDER_NAME: str = Field(default="uploads", description="Upload folder name")
    MAX_FILE_SIZE: int = Field(default=10485760, description="Max file size in bytes (10MB)")

    # Logging Configuration
    LOG_FILE_PATH: str = Field(default="app/app.log", description="Log file path")
    LOG_LEVEL: str = Field(default="INFO", description="Log level")

    # Development Settings
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment")

    @field_validator("GOOGLE_API_KEY")
    @classmethod
    def validate_api_key(cls, v):
        if not v or v == "your_gemini_api_key_here":
            raise ValueError("GOOGLE_API_KEY must be set to a valid API key")
        return v

    @field_validator("UPLOAD_FOLDER_NAME")
    @classmethod
    def validate_upload_folder(cls, v):
        # Ensure upload folder exists
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @property
    def redis_url(self) -> str:
        """Get Redis URL for connections"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
