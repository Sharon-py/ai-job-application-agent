import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.append(str(SRC_DIR))

from database import (
    get_jobs,
    initialize_database,
    prepare_jobs_for_database,
    update_job_status,
    upsert_jobs,
)


def test_initialize_database_creates_db_file(tmp_path):
    database_path = tmp_path / "test_job_agent.db"

    initialize_database(database_path)

    assert database_path.exists()


def test_prepare_jobs_for_database_adds_required_columns():
    jobs = pd.DataFrame(
        [
            {
                "title": "Data Scientist",
                "company": "Test Company",
                "source_url": "https://example.com/job",
            }
        ]
    )

    prepared = prepare_jobs_for_database(jobs)

    assert "job_id" in prepared.columns
    assert "status" in prepared.columns
    assert "personal_notes" in prepared.columns
    assert "created_at" in prepared.columns
    assert "updated_at" in prepared.columns

    assert prepared.loc[0, "title"] == "Data Scientist"
    assert prepared.loc[0, "company"] == "Test Company"


def test_upsert_jobs_inserts_jobs(tmp_path):
    database_path = tmp_path / "test_job_agent.db"

    jobs = pd.DataFrame(
        [
            {
                "title": "Data Scientist",
                "company": "Test Company",
                "location": "Paris",
                "source_url": "https://example.com/job-1",
                "description": "Python, SQL, ML",
                "adjusted_score": 42,
            }
        ]
    )

    inserted_count = upsert_jobs(jobs, database_path=database_path)
    stored_jobs = get_jobs(database_path=database_path)

    assert inserted_count == 1
    assert len(stored_jobs) == 1
    assert stored_jobs.loc[0, "title"] == "Data Scientist"
    assert stored_jobs.loc[0, "adjusted_score"] == 42


def test_upsert_jobs_updates_existing_job_without_duplicating(tmp_path):
    database_path = tmp_path / "test_job_agent.db"

    first_jobs = pd.DataFrame(
        [
            {
                "title": "Data Scientist",
                "company": "Test Company",
                "location": "Paris",
                "source_url": "https://example.com/job-1",
                "description": "Old description",
                "adjusted_score": 20,
            }
        ]
    )

    second_jobs = pd.DataFrame(
        [
            {
                "title": "Data Scientist",
                "company": "Test Company",
                "location": "Paris",
                "source_url": "https://example.com/job-1",
                "description": "New description",
                "adjusted_score": 50,
            }
        ]
    )

    upsert_jobs(first_jobs, database_path=database_path)
    upsert_jobs(second_jobs, database_path=database_path)

    stored_jobs = get_jobs(database_path=database_path)

    assert len(stored_jobs) == 1
    assert stored_jobs.loc[0, "description"] == "New description"
    assert stored_jobs.loc[0, "adjusted_score"] == 50


def test_update_job_status_updates_status_and_notes(tmp_path):
    database_path = tmp_path / "test_job_agent.db"

    jobs = pd.DataFrame(
        [
            {
                "title": "AI Engineer",
                "company": "AI Company",
                "location": "Paris",
                "source_url": "https://example.com/job-2",
                "description": "LLM, RAG, Docker",
                "adjusted_score": 60,
            }
        ]
    )

    upsert_jobs(jobs, database_path=database_path)
    stored_jobs = get_jobs(database_path=database_path)

    job_id = stored_jobs.loc[0, "job_id"]

    update_job_status(
        job_id=job_id,
        status="interested",
        personal_notes="Very interesting role",
        database_path=database_path,
    )

    updated_jobs = get_jobs(database_path=database_path)

    assert updated_jobs.loc[0, "status"] == "interested"
    assert updated_jobs.loc[0, "personal_notes"] == "Very interesting role"


def test_upsert_preserves_existing_status_and_notes(tmp_path):
    database_path = tmp_path / "test_job_agent.db"

    jobs = pd.DataFrame(
        [
            {
                "title": "ML Engineer",
                "company": "Company A",
                "location": "Paris",
                "source_url": "https://example.com/job-3",
                "description": "Initial description",
                "adjusted_score": 40,
            }
        ]
    )

    upsert_jobs(jobs, database_path=database_path)
    stored_jobs = get_jobs(database_path=database_path)
    job_id = stored_jobs.loc[0, "job_id"]

    update_job_status(
        job_id=job_id,
        status="applied",
        personal_notes="Applied on company website",
        database_path=database_path,
    )

    refreshed_jobs = pd.DataFrame(
        [
            {
                "title": "ML Engineer",
                "company": "Company A",
                "location": "Paris",
                "source_url": "https://example.com/job-3",
                "description": "Updated description from new collection",
                "adjusted_score": 70,
            }
        ]
    )

    upsert_jobs(refreshed_jobs, database_path=database_path)
    final_jobs = get_jobs(database_path=database_path)

    assert len(final_jobs) == 1
    assert final_jobs.loc[0, "description"] == "Updated description from new collection"
    assert final_jobs.loc[0, "adjusted_score"] == 70

    # Very important: user tracking is preserved.
    assert final_jobs.loc[0, "status"] == "applied"
    assert final_jobs.loc[0, "personal_notes"] == "Applied on company website"