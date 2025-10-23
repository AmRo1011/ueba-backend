from pydantic import BaseModel
import os
from urllib.parse import quote_plus

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

class Settings(BaseModel):
    APP_ENV: str = os.getenv("APP_ENV", "dev")
    PORT: int = int(os.getenv("PORT", "8001"))
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change_me")

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    @property
    def DATABASE_URL(self) -> str:
        # URL-encode user/password لتفادي أي رموز خاصة (@ : % & / ...)
        user = quote_plus(self.DB_USER)
        pw   = quote_plus(self.DB_PASSWORD)
        return (f"postgresql+psycopg2://{user}:{pw}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?sslmode=require")

settings = Settings()
