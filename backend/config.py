import os
from datetime import timedelta
from urllib.parse import quote_plus
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, ".env")
if os.path.isfile(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()


def build_database_uri():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if db_url.startswith("mysql://"):
            db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)
        return db_url

    # Fallback to discrete parameters if DATABASE_URL is not set
    user = os.getenv("DB_USER", "root")
    raw_password = os.getenv("DB_PASSWORD", "")
    password = quote_plus(raw_password)
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "sis_db")

    if raw_password:
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"

    return f"sqlite:///{os.path.join(BASE_DIR, 'dev.db')}"


def build_engine_options():
    options = {}
    ssl_ca = os.getenv("DB_SSL_CA")
    if ssl_ca:
        if not os.path.isabs(ssl_ca):
            ca_candidate = os.path.join(BASE_DIR, ssl_ca)
            if os.path.exists(ca_candidate):
                ssl_ca = ca_candidate
        if os.path.exists(ssl_ca):
            options["connect_args"] = {"ssl": {"ca": ssl_ca}}
    return options


class Config:
    SQLALCHEMY_DATABASE_URI = build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = build_engine_options()

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
