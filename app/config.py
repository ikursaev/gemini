from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    PORT: int = 8000 # Default port
    MODEL_NAME: str = "gemini-pro"
    LOG_FILE_PATH: str = "app/app.log"
    UPLOAD_FOLDER_NAME: str = "uploads"
    HOST: str = "0.0.0.0"
    REDIS_HOST: str = "localhost"

    class Config:
        env_file = ".env"

settings = Settings()