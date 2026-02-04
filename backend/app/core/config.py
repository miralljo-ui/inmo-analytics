from pydantic import BaseModel
from pydantic import Field
import os


class Settings(BaseModel):
    app_name: str = "Inmo Analytics"
    allowed_origins: str = Field(default="*")
    database_url: str = Field(default="postgresql+psycopg2://postgres:postgres@localhost:5432/inmo")


    @staticmethod
    def load() -> "Settings":
        return Settings(
            app_name=os.getenv("APP_NAME", "Inmo Analytics"),
            allowed_origins=os.getenv("ALLOWED_ORIGINS", "*"),
            database_url=os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg2://postgres:postgres@localhost:5432/inmo",
            ),
        )


settings = Settings.load()
