from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    PORT: int = 8000 # Default port

    class Config:
        env_file = ".env"

settings = Settings()