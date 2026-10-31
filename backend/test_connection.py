import os
import sys
from dotenv import load_dotenv

# Ensure backend directory is in path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(os.path.join(BACKEND_DIR, ".env"))

from utils.db import get_db_connection
from config import Config
from sqlalchemy import create_engine, text


def main():
    print("=" * 60)
    print("Testing connection to local MySQL database: sis_db")
    print("=" * 60)

    # 1. Test direct connection via PyMySQL
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            one_res = cur.fetchone()

            cur.execute("SELECT DATABASE(), CURRENT_USER(), VERSION();")
            db_info = cur.fetchone()

            cur.execute("SHOW TABLES;")
            tables = [row[0] for row in cur.fetchall()]

        conn.close()

        print("\nDatabase connection successful!")
        print(f"Executed query     : SELECT 1; -> Result: {one_res[0]}")
        print(f"Connected Database : {db_info[0]}")
        print(f"Current User       : {db_info[1]}")
        print(f"MySQL Version      : {db_info[2]}")
        print(f"Total Tables Found : {len(tables)}")
        print(f"Tables             : {', '.join(tables)}")

    except Exception as e:
        print(f"\nDirect connection error: {e}")
        sys.exit(1)

    # 2. Test SQLAlchemy connection via Config.SQLALCHEMY_DATABASE_URI
    try:
        print("\nVerifying SQLAlchemy engine with Config.SQLALCHEMY_DATABASE_URI...")
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        with engine.connect() as sqla_conn:
            sqla_res = sqla_conn.execute(text("SELECT 1;")).scalar()
            print(f"SQLAlchemy query test : SELECT 1; -> Result: {sqla_res}")
        print("SQLAlchemy connection successful!")
    except Exception as e:
        print(f"\nSQLAlchemy connection error: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("ALL DATABASE CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()