# Config

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service Name
    SERVICE_NAME:str

    PREFIX:str
    TAG:str

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str

    @property
    def db_url(self) -> tuple:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

settings = Settings()