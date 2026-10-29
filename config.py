import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
    DATABASE_URL = os.environ.get("DATABASE_URL")
    DB_SSLMODE = os.environ.get("DB_SSLMODE", "require")
