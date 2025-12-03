from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class RedisConfig(BaseSettings):
    HOST: str = '127.0.0.1'
    PORT: int = 6379
    MAX_CONN: int = 15

    model_config = SettingsConfigDict(env_prefix='REDIS_', extra='forbid')

class Settings(BaseSettings):
    DATABASE_URL: SecretStr | None = None
    redis = RedisConfig()
    BASE_URL: HttpUrl | None = None

    model_config = SettingsConfigDict(extra='forbid')

settings = Settings()
