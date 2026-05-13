from pathlib import Path
import sys

import pandas as pd

from config import PROCESSED_DIR, RESULTS_DIR, SCORED_OFFERS_PATH
from database import create_job_id, get_jobs, upsert_jobs


APPLICATION_STATUS_PATH = PROCESSED_DIR / "application_status.csv"
APPLICATION_MESSAGES_PATH = RESULTS_DIR / "application_messages.csv"


def load_csv_if_exists(path: Path, sep: str | None = None) -> pd.DataFrame:
    """
    Loads a CSV file if it exists.

    Some project CSV files use comma separator, others use semicolon
    for better Excel compatibility.
    """

    if not path.exists():
        print(f"File not found, skipping: {path}")
        return pd.DataFrame()

    if sep is not None:
        return pd.read_csv(path, sep=sep)

    try:
        return pd.read_csv(path)
    except Exception:
        return pd.read_csv(path, sep=";")


def add_job_id(jobs: pd.DataFrame) -> pd.DataFrame:
    """
    Adds job_id if it does not already exist.
    """

    jobs = jobs.copy()

    if "job_id" not in jobs.columns:
        jobs["job_id"] = jobs.apply(create_job_id, axis=1)

    return jobs


def merge_application_messages(jobs: pd.DataFrame) -> pd.DataFrame:
    """
    Adds generated application messages to the jobs DataFrame.
    """

    messages = load_csv_if_exists(APPLICATION_MESSAGES_PATH)

    if messages.empty:
        jobs["application_message"] = jobs.get("application_message", "")
        return jobs

    messages = add_job_id(messages)

    if "application_message" not in messages.columns:
        print("application_messages.csv found, but no application_message column.")
        jobs["application_message"] = jobs.get("application_message", "")
        return jobs

    messages = messages[["job_id", "application_message"]].drop_duplicates(
        subset=["job_id"],
        keep="last",
    )

    jobs = jobs.merge(
        messages,
        on="job_id",
        how="left",
        suffixes=("", "_from_messages"),
    )

    if "application_message_from_messages" in jobs.columns:
        jobs["application_message"] = jobs["application_message_from_messages"].fillna(
            jobs.get("application_message", "")
        )
        jobs = jobs.drop(columns=["application_message_from_messages"])
    else:
        jobs["application_message"] = jobs.get("application_message", "")

    jobs["application_message"] = jobs["application_message"].fillna("")

    return jobs


def merge_application_status(jobs: pd.DataFrame) -> pd.DataFrame:
    """
    Adds saved statuses and personal notes to the jobs DataFrame.
    """

    status_data = load_csv_if_exists(APPLICATION_STATUS_PATH, sep=";")

    if status_data.empty:
        jobs["status"] = jobs.get("status", "to_review")
        jobs["personal_notes"] = jobs.get("personal_notes", "")
        return jobs

    if "job_id" not in status_data.columns:
        print("application_status.csv found, but no job_id column.")
        jobs["status"] = jobs.get("status", "to_review")
        jobs["personal_notes"] = jobs.get("personal_notes", "")
        return jobs

    expected_columns = ["job_id", "status", "personal_notes"]
    existing_columns = [
        column for column in expected_columns
        if column in status_data.columns
    ]

    status_data = status_data[existing_columns].drop_duplicates(
        subset=["job_id"],
        keep="last",
    )

    jobs = jobs.merge(
        status_data,
        on="job_id",
        how="left",
        suffixes=("", "_from_status"),
    )

    if "status_from_status" in jobs.columns:
        jobs["status"] = jobs["status_from_status"].fillna(
            jobs.get("status", "to_review")
        )
        jobs = jobs.drop(columns=["status_from_status"])
    else:
        jobs["status"] = jobs.get("status", "to_review")

    if "personal_notes_from_status" in jobs.columns:
        jobs["personal_notes"] = jobs["personal_notes_from_status"].fillna(
            jobs.get("personal_notes", "")
        )
        jobs = jobs.drop(columns=["personal_notes_from_status"])
    else:
        jobs["personal_notes"] = jobs.get("personal_notes", "")

    jobs["status"] = jobs["status"].fillna("to_review")
    jobs["personal_notes"] = jobs["personal_notes"].fillna("")

    return jobs


def import_existing_data() -> int:
    """
    Imports current CSV-based project data into SQLite.
    """

    print("=" * 80)
    print("Importing existing CSV data into SQLite")
    print("=" * 80)

    scored_jobs = load_csv_if_exists(SCORED_OFFERS_PATH)

    if scored_jobs.empty:
        print("")
        print("No scored jobs found.")
        print("Run this first:")
        print("py src/data.py")
        return 0

    print(f"Loaded scored jobs: {len(scored_jobs)}")

    jobs = add_job_id(scored_jobs)
    if "date_posted" not in jobs.columns:
        jobs["date_posted"] = ""
    jobs = merge_application_messages(jobs)
    jobs = merge_application_status(jobs)

    imported_count = upsert_jobs(jobs)

    stored_jobs = get_jobs()

    print("")
    print("Import completed.")
    print(f"Rows sent to database: {imported_count}")
    print(f"Total jobs currently stored in SQLite: {len(stored_jobs)}")

    if not stored_jobs.empty:
        print("")
        print("Preview:")
        columns_to_show = [
            "title",
            "company",
            "adjusted_score",
            "status",
            "application_message",
        ]

        available_columns = [
            column for column in columns_to_show
            if column in stored_jobs.columns
        ]

        print(stored_jobs[available_columns].head(10).to_string(index=False))

    return imported_count


if __name__ == "__main__":
    import_existing_data()