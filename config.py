from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Broscience"
    openai_api_key: str
    meilisearch_url: str
    meilisearch_password: str
    meilisearch_index: str = "ingredients"
    model_structure_outputs: str = "gpt-4o-mini"

    # Google Service Account from Firebase
    google_service_account_type: str
    google_service_account_project_id: str
    google_service_account_private_key_id: str
    google_service_account_private_key: str
    google_service_account_client_email: str
    google_service_account_client_id: str
    google_service_account_auth_uri: str
    google_service_account_token_uri: str
    google_service_account_auth_provider_x509_cert_url: str
    google_service_account_client_x509_cert_url: str
    google_service_account_universe_domain: str

    fatsecret_consumer_secret: str
    fatsecret_consumer_key: str

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings():
    return Settings()