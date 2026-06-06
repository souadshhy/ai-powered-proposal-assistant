from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_url: str = "sqlite:///./tbr_dev.db"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    use_ai_when_key_present: bool = True
    data_dir: str = str(Path(__file__).resolve().parents[2] / "data")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
