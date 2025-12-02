from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str | None = None
    BASE_URL: HttpUrl | None = None

    model_config = SettingsConfigDict(extra='forbid')

settings = Settings()
