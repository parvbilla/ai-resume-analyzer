from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger("resumeai.database")


# ============================================================
# PATHS & CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_FILE = Path(
    os.getenv(
        "DATABASE_FILE",
        str(BASE_DIR / "resume_analyzer.db"),
    )
).resolve()

DATABASE_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATABASE_FILE.as_posix()}",
)


# ============================================================
# SQLALCHEMY ENGINE
# ============================================================

engine: Engine = create_engine(
    DATABASE_URL,

    # SQLite needs this for FastAPI's multi-threaded environment.
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
    },

    # Validate connections before using them.
    pool_pre_ping=True,

    # Recycle connections periodically.
    pool_recycle=1800,

    # Echo SQL only when explicitly enabled.
    echo=os.getenv("SQL_ECHO", "false").lower()
    in {"1", "true", "yes", "on"},
)


# ============================================================
# DATABASE SESSION
# ============================================================

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ============================================================
# DECLARATIVE BASE
# ============================================================

Base = declarative_base()


# ============================================================
# SQLITE OPTIMIZATION
# ============================================================

def _configure_sqlite(connection, _connection_record) -> None:
    """
    Configure every SQLite connection with safe performance
    and integrity settings.
    """

    try:
        cursor = connection.cursor()

        # Foreign key enforcement.
        cursor.execute("PRAGMA foreign_keys=ON")

        # Write-Ahead Logging improves concurrent reads/writes.
        cursor.execute("PRAGMA journal_mode=WAL")

        # Wait for locked database instead of failing immediately.
        cursor.execute("PRAGMA busy_timeout=30000")

        # Balanced durability/performance.
        cursor.execute("PRAGMA synchronous=NORMAL")

        # Keep temporary tables in memory where possible.
        cursor.execute("PRAGMA temp_store=MEMORY")

        cursor.close()

    except Exception:
        logger.exception(
            "Failed to configure SQLite connection."
        )
        raise


# Register SQLite connection configuration.

from sqlalchemy import event

event.listen(
    engine,
    "connect",
    _configure_sqlite,
)


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI database dependency.

    Creates a database session for the request and guarantees
    that the session is closed afterward.

    If an unexpected exception happens while using the session,
    rollback is attempted before closing.
    """

    db = SessionLocal()

    try:
        yield db

    except Exception:
        db.rollback()

        logger.exception(
            "Database transaction rolled back because of an error."
        )

        raise

    finally:
        db.close()


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database() -> None:
    """
    Initialize database tables and perform lightweight schema
    upgrades required by newer versions of ResumeAI.

    Importing models here guarantees SQLAlchemy knows about all
    model classes before create_all() executes.
    """

    try:
        from . import models  # noqa: F401

        Base.metadata.create_all(
            bind=engine,
            checkfirst=True,
        )

        ensure_schema()

        logger.info(
            "Database initialized successfully: %s",
            DATABASE_FILE,
        )

    except Exception:
        logger.exception(
            "Database initialization failed."
        )
        raise


# ============================================================
# LIGHTWEIGHT SCHEMA MIGRATION
# ============================================================

def ensure_schema() -> None:
    """
    Safely add newer columns to an existing SQLite database.

    This is intentionally lightweight and is NOT intended to
    replace Alembic for a large production system.
    """

    inspector = inspect(engine)

    table_names = inspector.get_table_names()

    if "resume_analyses" not in table_names:
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns(
            "resume_analyses"
        )
    }

    additions = {
        "overall_score": "FLOAT DEFAULT 0",
        "skills_score": "FLOAT DEFAULT 0",
        "keyword_score": "FLOAT DEFAULT 0",
        "semantic_score": "FLOAT DEFAULT 0",
        "section_score": "FLOAT DEFAULT 0",
        "achievement_score": "FLOAT DEFAULT 0",
        "contact_score": "FLOAT DEFAULT 0",
        "content_score": "FLOAT DEFAULT 0",

        "role_title": (
            "VARCHAR(255) DEFAULT 'Target Role'"
        ),

        "detected_keywords": (
            "TEXT DEFAULT ''"
        ),

        "missing_keywords": (
            "TEXT DEFAULT ''"
        ),

        "sections": (
            "TEXT DEFAULT ''"
        ),

        "strengths": (
            "TEXT DEFAULT ''"
        ),

        "weaknesses": (
            "TEXT DEFAULT ''"
        ),

        "insights": (
            "TEXT DEFAULT ''"
        ),
    }

    missing_columns = {
        name: definition
        for name, definition in additions.items()
        if name not in existing_columns
    }

    if not missing_columns:
        return

    logger.info(
        "Applying %d database schema upgrades.",
        len(missing_columns),
    )

    with engine.begin() as connection:

        for column_name, definition in missing_columns.items():

            statement = text(
                f'ALTER TABLE resume_analyses '
                f'ADD COLUMN "{column_name}" {definition}'
            )

            connection.execute(statement)

            logger.info(
                "Added database column: %s",
                column_name,
            )


# ============================================================
# DATABASE HEALTH CHECK
# ============================================================

def check_database_connection() -> bool:
    """
    Verify that the database is reachable.

    Returns:
        True  -> database is healthy
        False -> database connection failed
    """

    try:
        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

        return True

    except Exception:
        logger.exception(
            "Database health check failed."
        )
        return False


# ============================================================
# DATABASE METADATA
# ============================================================

def get_database_info() -> dict:
    """
    Return safe database information for internal diagnostics
    and the application's health endpoint.

    No sensitive database contents are exposed.
    """

    try:
        inspector = inspect(engine)

        tables = inspector.get_table_names()

        return {
            "engine": engine.dialect.name,
            "database": DATABASE_FILE.name,
            "database_exists": DATABASE_FILE.exists(),
            "tables": tables,
            "healthy": check_database_connection(),
        }

    except Exception:
        logger.exception(
            "Unable to collect database information."
        )

        return {
            "engine": engine.dialect.name,
            "database": DATABASE_FILE.name,
            "database_exists": DATABASE_FILE.exists(),
            "tables": [],
            "healthy": False,
        }


# ============================================================
# DATABASE SHUTDOWN
# ============================================================

def close_database() -> None:
    """
    Dispose SQLAlchemy's connection pool.

    Useful when FastAPI shuts down.
    """

    try:
        engine.dispose()

        logger.info(
            "Database connection pool disposed."
        )

    except Exception:
        logger.exception(
            "Failed to dispose database connection pool."
        )