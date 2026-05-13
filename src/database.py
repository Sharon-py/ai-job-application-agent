from pathlib import Path
import sqlite3
from datetime import datetime

import pandas as pd

from config import DATA_DIR


DATABASE_PATH = DATA_DIR / "job_agent.db"


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


def get_connection(database_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    """
    Opens a connection to the SQLite database.

    SQLite stores the whole database in one .db file.
    """

    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    return connection


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


def initialize_database(database_path: Path = DATABASE_PATH) -> None:
    """
    Creates the database and the jobs table if they do not exist yet.
    """

    with get_connection(database_path) as connection:
        connection.execute(
            """
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
        )

        connection.commit()

    add_missing_columns(database_path)


def prepare_jobs_for_database(jobs: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares a jobs DataFrame before inserting it into SQLite.

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

def add_missing_columns(database_path=DATABASE_PATH) -> None:
    """
    Adds missing columns to an existing SQLite database.

    This keeps the local database compatible when the schema evolves.
    """

    with get_connection(database_path) as connection:
        existing_columns = pd.read_sql_query(
            "PRAGMA table_info(jobs)",
            connection,
        )["name"].tolist()

        if "date_posted" not in existing_columns:
            connection.execute("ALTER TABLE jobs ADD COLUMN date_posted TEXT")
            connection.commit()


def upsert_jobs(
    jobs: pd.DataFrame,
    database_path: Path = DATABASE_PATH,
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

    with get_connection(database_path) as connection:
        for _, row in prepared_jobs.iterrows():
            connection.execute(
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
                """,
                row.to_dict(),
            )

        connection.commit()

    return len(prepared_jobs)


def get_jobs(database_path: Path = DATABASE_PATH) -> pd.DataFrame:
    """
    Reads all jobs from the database.
    """

    initialize_database(database_path)

    with get_connection(database_path) as connection:
        jobs = pd.read_sql_query(
            """
            SELECT *
            FROM jobs
            ORDER BY adjusted_score DESC, created_at DESC
            """,
            connection,
        )

    return jobs


def update_job_status(
    job_id: str,
    status: str,
    personal_notes: str = "",
    database_path: Path = DATABASE_PATH,
) -> None:
    """
    Updates the status and personal notes of one job.
    """

    initialize_database(database_path)

    now = datetime.now().isoformat(timespec="seconds")

    with get_connection(database_path) as connection:
        connection.execute(
            """
            UPDATE jobs
            SET status = ?,
                personal_notes = ?,
                updated_at = ?
            WHERE job_id = ?
            """,
            (status, personal_notes, now, job_id),
        )

        connection.commit()


def import_csv_to_database(
    csv_path: Path,
    database_path: Path = DATABASE_PATH,
) -> int:
    """
    Imports jobs from a CSV file into the SQLite database.
    """

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    jobs = pd.read_csv(csv_path)

    return upsert_jobs(jobs, database_path=database_path)


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized at: {DATABASE_PATH}")