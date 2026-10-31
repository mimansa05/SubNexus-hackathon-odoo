"""
Database initialization and connectivity verification module.
"""

import sys
from sqlalchemy import inspect, text
from app.database.db import engine, Base


def check_connection() -> bool:
    """Verifies active connectivity to the PostgreSQL database."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();")).scalar()
            current_db = conn.execute(text("SELECT current_database();")).scalar()
            print("Successfully connected to PostgreSQL database!")
            print(f"Database: {current_db}")
            print(f"Version: {result}")
            return True
    except Exception as exc:
        print(f"Database connection error: {exc}", file=sys.stderr)
        return False


def get_existing_tables() -> list[str]:
    """Returns a list of tables currently present in the database."""
    inspector = inspect(engine)
    return inspector.get_table_names()


def init_db(create_tables: bool = False) -> None:
    """
    Initializes database connectivity and optionally creates tables in development.
    Note: For production and version-controlled environments, use Alembic migrations.
    """
    if not check_connection():
        raise RuntimeError("Failed to establish database connection.")

    existing_tables = get_existing_tables()
    print(f"Existing tables in database ({len(existing_tables)}): {existing_tables}")

    if create_tables:
        from app.database.base import Base  # ensure all models are imported
        print("Creating all tables from shared metadata...")
        Base.metadata.create_all(bind=engine)
        new_tables = get_existing_tables()
        print(f"Tables after initialization ({len(new_tables)}): {new_tables}")


if __name__ == "__main__":
    check_only = "--check-only" in sys.argv or "-c" in sys.argv
    create = "--create" in sys.argv
    if check_only:
        check_connection()
    else:
        init_db(create_tables=create)
