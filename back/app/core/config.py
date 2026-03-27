from pydantic_settings import BaseSettings



class Settings(BaseSettings):

    app_name: str = "traitementImageBack"
    debug: bool = True
    upload_dir: str = "uploads"

    DATABASE_URL: str
    APP_VERSION: str | None = None
    DIRECT_URL: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()

# Si DATABASE_URL n'est pas défini, on le remplace par DIRECT_URL
if settings.DATABASE_URL is None:
    settings.DATABASE_URL = settings.DIRECT_URL