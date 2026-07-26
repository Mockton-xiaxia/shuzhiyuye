from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "数智渔业平台"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./fishery.db"
    jwt_secret: str = "fishery-dev-secret-change-me"
    jwt_alg: str = "HS256"
    access_token_minutes: int = 120
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    ezviz_app_key: str = ""
    ezviz_app_secret: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
