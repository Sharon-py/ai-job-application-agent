from pathlib import Path
from datetime import datetime
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config import DATA_DIR


load_dotenv()


DATABASE_PATH = DATA_DIR / "job_agent.db"
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


JOBS_COLUMNS = [
    "job_id",
    "title",
    "company",
    "location",
    "contract_type",
    "source_url",
    "description",
    "date_found",
    "date_posted",
    "source",
    "status",
    "personal_notes",
    "notes",
    "score",
    "adjusted_score",
    "recommendation",
    "fit_type",
    "next_action",
    "explanation",
    "seniority_level",
    "seniority_warning",
    "seniority_penalty",
    "contract_fit",
    "contract_warning",
    "contract_penalty",
    "application_message",
    "created_at",
    "updated_at",
]


def normalize_database_url(database_url: str) -> str:
    """
    Normalizes database URLs for SQLAlchemy.

    Some cloud providers expose URLs starting with postgres://,
    while SQLAlchemy expects postgresql://.
    """

    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)

    return database_url


def get_database_url(database_path: Path | None = None) -> str:
    """
    Returns the database URL.

    Priority:
    1. Explicit database_path, useful for tests.
    2. DATABASE_URL environment variable, useful for PostgreSQL/cloud.
    3. Local SQLite database.
    """

    if database_path is not None:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{database_path.as_posix()}"

    if DATABASE_URL:
        return normalize_database_url(DATABASE_URL)

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{DATABASE_PATH.as_posix()}"


def get_engine(database_path: Path | None = None) -> Engine:
    """
    Creates a SQLAlchemy engine for SQLite or PostgreSQL.
    """

    database_url = get_database_url(database_path)

    connect_args = {}

    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    return create_engine(
        database_url,
        future=True,
        connect_args=connect_args,
    )


def get_database_backend(database_path: Path | None = None) -> str:
    """
    Returns the current database backend.
    """

    engine = get_engine(database_path)
    return engine.url.get_backend_name()


def create_job_id(row: pd.Series) -> str:
    """
    Creates a stable ID for one job offer.

    The ID is based on title + company + source_url.
    It allows us to recognize the same job later.
    """

    title = str(row.get("title", "")).strip().lower()
    company = str(row.get("company", "")).strip().lower()
    source_url = str(row.get("source_url", "")).strip().lower()

    return f"{title}__{company}__{source_url}"


def initialize_database(database_path: Path | None = None) -> None:
    """
    Creates the jobs table if it does not exist yet.
    Works with SQLite and PostgreSQL.
    """

    engine = get_engine(database_path)

    create_table_query = """
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            contract_type TEXT,
            source_url TEXT,
            description TEXT,
            date_found TEXT,
            date_posted TEXT,
            source TEXT,
            status TEXT DEFAULT 'to_review',
            personal_notes TEXT DEFAULT '',
            notes TEXT,
            score REAL,
            adjusted_score REAL,
            recommendation TEXT,
            fit_type TEXT,
            next_action TEXT,
            explanation TEXT,
            seniority_level TEXT,
            seniority_warning TEXT,
            seniority_penalty REAL,
            contract_fit TEXT,
            contract_warning TEXT,
            contract_penalty REAL,
            application_message TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """

    with engine.begin() as connection:
        connection.execute(text(create_table_query))

    add_missing_columns(database_path)


def get_existing_columns(
    table_name: str,
    database_path: Path | None = None,
) -> list[str]:
    """
    Returns existing columns for a table.
    Supports SQLite and PostgreSQL.
    """

    engine = get_engine(database_path)
    backend = engine.url.get_backend_name()

    with engine.begin() as connection:
        if backend == "sqlite":
            rows = connection.execute(
                text(f"PRAGMA table_info({table_name})")
            ).fetchall()

            return [row[1] for row in rows]

        rows = connection.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = :table_name
                  AND table_schema = 'public'
                ORDER BY ordinal_position
                """
            ),
            {"table_name": table_name},
        ).fetchall()

        return [row[0] for row in rows]


def add_missing_columns(database_path: Path | None = None) -> None:
    """
    Adds missing columns when the schema evolves.

    This protects existing local SQLite databases and future PostgreSQL tables
    if new fields are added progressively.
    """

    engine = get_engine(database_path)

    existing_columns = get_existing_columns(
        table_name="jobs",
        database_path=database_path,
    )

    columns_to_add = {
        "date_posted": "TEXT",
    }

    with engine.begin() as connection:
        for column_name, column_type in columns_to_add.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(
                        f"ALTER TABLE jobs "
                        f"ADD COLUMN {column_name} {column_type}"
                    )
                )


def prepare_jobs_for_database(jobs: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares a jobs DataFrame before inserting it into the database.

    It adds missing columns, creates job_id, and fills empty values.
    """

    jobs = jobs.copy()

    if "job_id" not in jobs.columns:
        jobs["job_id"] = jobs.apply(create_job_id, axis=1)

    now = datetime.now().isoformat(timespec="seconds")

    if "created_at" not in jobs.columns:
        jobs["created_at"] = now

    jobs["updated_at"] = now

    for column in JOBS_COLUMNS:
        if column not in jobs.columns:
            jobs[column] = ""

    jobs = jobs[JOBS_COLUMNS]

    for column in jobs.columns:
        jobs[column] = jobs[column].fillna("")

    return jobs


def upsert_jobs(
    jobs: pd.DataFrame,
    database_path: Path | None = None,
) -> int:
    """
    Inserts or updates jobs in the database.

    Upsert means:
    - if the job is new, insert it
    - if the job already exists, update its information

    We preserve status and personal_notes when the job already exists.
    """

    if jobs.empty:
        return 0

    initialize_database(database_path)

    prepared_jobs = prepare_jobs_for_database(jobs)

    engine = get_engine(database_path)

    upsert_query = text(
        """
        INSERT INTO jobs (
            job_id,
            title,
            company,
            location,
            contract_type,
            source_url,
            description,
            date_found,
            date_posted,
            source,
            status,
            personal_notes,
            notes,
            score,
            adjusted_score,
            recommendation,
            fit_type,
            next_action,
            explanation,
            seniority_level,
            seniority_warning,
            seniority_penalty,
            contract_fit,
            contract_warning,
            contract_penalty,
            application_message,
            created_at,
            updated_at
        )
        VALUES (
            :job_id,
            :title,
            :company,
            :location,
            :contract_type,
            :source_url,
            :description,
            :date_found,
            :date_posted,
            :source,
            :status,
            :personal_notes,
            :notes,
            :score,
            :adjusted_score,
            :recommendation,
            :fit_type,
            :next_action,
            :explanation,
            :seniority_level,
            :seniority_warning,
            :seniority_penalty,
            :contract_fit,
            :contract_warning,
            :contract_penalty,
            :application_message,
            :created_at,
            :updated_at
        )
        ON CONFLICT(job_id) DO UPDATE SET
            title = excluded.title,
            company = excluded.company,
            location = excluded.location,
            contract_type = excluded.contract_type,
            source_url = excluded.source_url,
            description = excluded.description,
            date_found = excluded.date_found,
            date_posted = excluded.date_posted,
            source = excluded.source,
            notes = excluded.notes,
            score = excluded.score,
            adjusted_score = excluded.adjusted_score,
            recommendation = excluded.recommendation,
            fit_type = excluded.fit_type,
            next_action = excluded.next_action,
            explanation = excluded.explanation,
            seniority_level = excluded.seniority_level,
            seniority_warning = excluded.seniority_warning,
            seniority_penalty = excluded.seniority_penalty,
            contract_fit = excluded.contract_fit,
            contract_warning = excluded.contract_warning,
            contract_penalty = excluded.contract_penalty,
            application_message = excluded.application_message,
            updated_at = excluded.updated_at
        """
    )

    records = prepared_jobs.to_dict(orient="records")

    with engine.begin() as connection:
        connection.execute(upsert_query, records)

    return len(prepared_jobs)


def get_jobs(database_path: Path | None = None) -> pd.DataFrame:
    """
    Reads all jobs from the database.
    """

    initialize_database(database_path)

    engine = get_engine(database_path)

    query = text(
        """
        SELECT *
        FROM jobs
        ORDER BY adjusted_score DESC, created_at DESC
        """
    )

    with engine.begin() as connection:
        jobs = pd.read_sql_query(query, connection)

    return jobs


def update_job_status(
    job_id: str,
    status: str,
    personal_notes: str = "",
    database_path: Path | None = None,
) -> None:
    """
    Updates the status and personal notes of one job.
    """

    initialize_database(database_path)

    now = datetime.now().isoformat(timespec="seconds")

    engine = get_engine(database_path)

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE jobs
                SET status = :status,
                    personal_notes = :personal_notes,
                    updated_at = :updated_at
                WHERE job_id = :job_id
                """
            ),
            {
                "status": status,
                "personal_notes": personal_notes,
                "updated_at": now,
                "job_id": job_id,
            },
        )


def import_csv_to_database(
    csv_path: Path,
    database_path: Path | None = None,
) -> int:
    """
    Imports jobs from a CSV file into the database.
    """

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    jobs = pd.read_csv(csv_path)

    return upsert_jobs(jobs, database_path=database_path)


if __name__ == "__main__":
    initialize_database()

    backend = get_database_backend()
    print(f"Database initialized using backend: {backend}")

    if not DATABASE_URL:
        print(f"Local SQLite database path: {DATABASE_PATH}")