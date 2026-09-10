from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4.1-nano"
    knowledge_base_path: str = "/knowledge-base"


    model_config = SettingsConfigDict(
        case_sensitive=False
    )


settings = Settings()

