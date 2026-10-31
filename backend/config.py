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


class BaseConfig:
    FLASK_ENV = os.getenv("FLASK_ENV", "development").strip().lower()
    SQLALCHEMY_DATABASE_URI = build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = build_engine_options()
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or "sis-development-local-only-key-2026"

    _cors_env = os.getenv("CORS_ORIGINS", "")
    if _cors_env and _cors_env.strip() != "*":
        CORS_ORIGINS = [o.strip() for o in _cors_env.split(",") if o.strip()]
    else:
        CORS_ORIGINS = [
            "http://localhost:5000",
            "http://127.0.0.1:5000",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]


class ProductionConfig(BaseConfig):
    DEBUG = False

    # Enforce strong, non-fallback JWT secret in production
    _jwt_secret = os.getenv("JWT_SECRET_KEY")
    _insecure_defaults = {
        "", "dev-secret-change-me", "change-this-to-something-long-and-random",
        "sis-development-local-only-key-2026"
    }
    if not _jwt_secret or _jwt_secret.strip() in _insecure_defaults:
        raise RuntimeError(
            "CRITICAL CONFIGURATION ERROR: JWT_SECRET_KEY must be set in production "
            "to a strong, random secret key. Insecure fallback values are strictly forbidden."
        )
    JWT_SECRET_KEY = _jwt_secret.strip()

    # Enforce restricted CORS origins in production (wildcards strictly rejected)
    _cors_env = os.getenv("CORS_ORIGINS", "").strip()
    if not _cors_env or _cors_env == "*":
        # Default to the configured production frontend domain if wildcard or unset
        CORS_ORIGINS = ["https://sis-portal-gold.vercel.app"]
    else:
        CORS_ORIGINS = [o.strip() for o in _cors_env.split(",") if o.strip()]
        if "*" in CORS_ORIGINS:
            raise RuntimeError(
                "CRITICAL CONFIGURATION ERROR: Wildcard CORS_ORIGINS ('*') is not allowed in production. "
                "Specify explicit allowed origin URLs separated by commas."
            )


def get_config():
    env = os.getenv("FLASK_ENV", "development").strip().lower()
    return ProductionConfig if env == "production" else DevelopmentConfig


# Config dynamically resolves to the active environment configuration
class ConfigMeta(type):
    def __getattr__(cls, name):
        active_cls = get_config()
        return getattr(active_cls, name)


class Config(metaclass=ConfigMeta):
    pass

