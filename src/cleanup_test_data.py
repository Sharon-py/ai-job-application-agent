from pathlib import Path
import sqlite3

import pandas as pd

from config import JOB_OFFERS_PATH, SCORED_OFFERS_PATH, PROCESSED_DIR, RESULTS_DIR, DATA_DIR


APPLICATION_STATUS_PATH = PROCESSED_DIR / "application_status.csv"
APPLICATION_MESSAGES_PATH = RESULTS_DIR / "application_messages.csv"
DATABASE_PATH = DATA_DIR / "job_agent.db"


TEST_PATTERNS = [
    "Test Entreprise",
    "Test Mixed",
    "Test Entreprise FR",
    "Test Entreprise Senior",
    "Data Scientist Junior Test",
    "mixed_seniority_test",
    "lead_ai_fr_test",
    "data_scientist_fr_test",
]


CSV_PATHS = [
    JOB_OFFERS_PATH,
    SCORED_OFFERS_PATH,
    APPLICATION_STATUS_PATH,
    APPLICATION_MESSAGES_PATH,
]


def row_contains_test_data(row: pd.Series) -> bool:
    """
    Returns True if a row seems to come from fake/test data.
    """

    row_text = " ".join(row.fillna("").astype(str).tolist()).lower()

    return any(pattern.lower() in row_text for pattern in TEST_PATTERNS)


def clean_csv(path: Path) -> None:
    """
    Removes fake/test rows from one CSV file.
    """

    if not path.exists():
        print(f"Skipping missing file: {path}")
        return

    try:
        df = pd.read_csv(path)
        separator = ","
    except Exception:
        df = pd.read_csv(path, sep=";")
        separator = ";"

    if df.empty:
        print(f"Skipping empty file: {path}")
        return

    mask_test = df.apply(row_contains_test_data, axis=1)

    removed_count = int(mask_test.sum())

    if removed_count == 0:
        print(f"No test rows found in: {path}")
        return

    cleaned = df[~mask_test].copy()

    df.to_csv(path.with_suffix(path.suffix + ".backup"), index=False, sep=separator)
    cleaned.to_csv(path, index=False, sep=separator, encoding="utf-8-sig")

    print(f"Cleaned {path}")
    print(f"Removed rows: {removed_count}")
    print(f"Backup saved to: {path.with_suffix(path.suffix + '.backup')}")


def clean_sqlite_database() -> None:
    """
    Removes fake/test rows from the SQLite jobs table.
    """

    if not DATABASE_PATH.exists():
        print(f"Skipping missing database: {DATABASE_PATH}")
        return

    conditions = []
    params = []

    columns_to_check = [
        "title",
        "company",
        "location",
        "source_url",
        "description",
        "notes",
        "application_message",
    ]

    for pattern in TEST_PATTERNS:
        for column in columns_to_check:
            conditions.append(f"LOWER({column}) LIKE ?")
            params.append(f"%{pattern.lower()}%")

    where_clause = " OR ".join(conditions)

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM jobs
            WHERE {where_clause}
            """,
            params,
        )

        removed_count = cursor.fetchone()[0]

        if removed_count == 0:
            print("No test rows found in SQLite database.")
            return

        cursor.execute(
            f"""
            DELETE FROM jobs
            WHERE {where_clause}
            """,
            params,
        )

        connection.commit()

    print(f"Cleaned SQLite database: {DATABASE_PATH}")
    print(f"Removed rows: {removed_count}")


def main() -> None:
    print("=" * 80)
    print("Cleaning fake/test job data")
    print("=" * 80)

    for path in CSV_PATHS:
        clean_csv(path)

    clean_sqlite_database()

    print("")
    print("Cleanup completed.")


if __name__ == "__main__":
    main()