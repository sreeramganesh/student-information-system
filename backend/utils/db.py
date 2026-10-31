import os
from dotenv import load_dotenv
import pymysql

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(BACKEND_DIR, ".env")
if os.path.isfile(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()


def get_db_connection():
    """
    Establishes and returns a direct connection to the MySQL database.
    Configuration parameters are read from environment variables with fallback defaults.
    """
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", 3306))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "sis_db")

    ssl_ca = os.getenv("DB_SSL_CA")
    ssl_dict = None
    if ssl_ca:
        if not os.path.isabs(ssl_ca):
            ca_candidate = os.path.join(BACKEND_DIR, ssl_ca)
            if os.path.exists(ca_candidate):
                ssl_ca = ca_candidate
        if os.path.exists(ssl_ca):
            ssl_dict = {"ca": ssl_ca}

    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        ssl=ssl_dict,
        autocommit=True
    )
    return conn
