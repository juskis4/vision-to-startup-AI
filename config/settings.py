from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    DEFAULT_MODEL: str
    MAX_TOKENS: int
    DEFAULT_TEMPERATURE: float
    TRANSCRIBE_MODEL: str

    TELEGRAM_API_TOKEN: str

    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Render Managed Redis (primary) - Optional for local development
    REDIS_URL: str = ""

    # Fallback for local development
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
