from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Broscience"
    openai_api_key: str
    model_structure_outputs: str = "gpt-4o-mini"
    model_config = SettingsConfigDict(env_file=".env")
