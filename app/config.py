from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# BaseSettings loads and validates setting from .env file.
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # These values are in .env file. We validate their types here with pydantic-settings.
    database_url: str
    # Used to create JWT tokens, and later to verify JWT tokens
    secret_key: SecretStr = Field(min_length=32)
    access_token_expire_minutes: int = Field(default=30, gt=0)

# This settings object has all the app settings. Now we can import it, when we need it.
# It will be used in database.py, security.py, dependencies.py...
settings = Settings()
