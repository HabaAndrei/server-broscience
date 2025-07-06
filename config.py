from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Broscience"
    openai_api_key: str
    meilisearch_url: str
    meilisearch_password: str
    meilisearch_index: str = "ingredients"
    model_structure_outputs: str = "gpt-4o-mini"
    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings():
    return Settings()