from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    DEFAULT_MODEL: str
    MAX_TOKENS: int
    DEFAULT_TEMPERATURE: float

    TELEGRAM_API_TOKEN: str

    class Config:
        env_file = ".env"


settings = Settings()
