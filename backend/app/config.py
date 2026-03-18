from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    use_llm: bool = False
    use_agents_sdk: bool = False
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
