from pydantic import BaseSettings


class Settings(BaseSettings):

    app_name: str = "traitementImageBack"
    debug: bool = True
    upload_dir: str = "uploads"

    class Config:
        env_file = ".env"


settings = Settings()