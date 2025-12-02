from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: SecretStr | None = None
    REDIS_CACHE_URL: SecretStr | None = None
    BASE_URL: HttpUrl | None = None

    model_config = SettingsConfigDict(extra='forbid')

settings = Settings()
