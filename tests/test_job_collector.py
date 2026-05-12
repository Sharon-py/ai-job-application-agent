import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.append(str(SRC_DIR))

from job_collector import (
    EXPECTED_COLUMNS,
    clean_text_columns,
    normalize_collected_jobs,
    remove_duplicates,
)


def test_normalize_collected_jobs_creates_expected_schema():
    raw_jobs = pd.DataFrame(
        [
            {
                "title": "Data Scientist",
                "company": "Test Company",
                "location": "Paris",
                "job_type": "Full-time",
                "job_url": "https://example.com/job-1",
                "description": "Python, machine learning, SQL.",
                "site": "linkedin",
                "search_query": "Data Scientist junior",
            }
        ]
    )

    normalized = normalize_collected_jobs(raw_jobs)

    assert list(normalized.columns) == EXPECTED_COLUMNS
    assert normalized.loc[0, "title"] == "Data Scientist"
    assert normalized.loc[0, "company"] == "Test Company"
    assert normalized.loc[0, "contract_type"] == "Full-time"
    assert normalized.loc[0, "source_url"] == "https://example.com/job-1"
    assert normalized.loc[0, "source"] == "linkedin"
    assert normalized.loc[0, "status"] == "to_review"
    assert "Data Scientist junior" in normalized.loc[0, "notes"]


def test_normalize_collected_jobs_without_search_query_still_works():
    raw_jobs = pd.DataFrame(
        [
            {
                "title": "ML Engineer",
                "company": "AI Company",
                "location": "Paris",
                "job_type": "CDI",
                "job_url": "https://example.com/job-2",
                "description": "LLM, RAG, Docker.",
                "site": "indeed",
            }
        ]
    )

    normalized = normalize_collected_jobs(raw_jobs)

    assert list(normalized.columns) == EXPECTED_COLUMNS
    assert normalized.loc[0, "notes"] == "Collected automatically with JobSpy"


def test_clean_text_columns_adds_missing_columns_and_removes_nan():
    jobs = pd.DataFrame(
        [
            {
                "title": " Data Scientist ",
                "company": None,
                "location": " Paris ",
                "source_url": " https://example.com/job ",
            }
        ]
    )

    cleaned = clean_text_columns(jobs)

    assert list(cleaned.columns) == EXPECTED_COLUMNS
    assert cleaned.loc[0, "title"] == "Data Scientist"
    assert cleaned.loc[0, "company"] == ""
    assert cleaned.loc[0, "location"] == "Paris"
    assert cleaned.loc[0, "source_url"] == "https://example.com/job"

    for column in EXPECTED_COLUMNS:
        assert column in cleaned.columns
        assert pd.notna(cleaned.loc[0, column])


def test_remove_duplicates_by_source_url_keeps_last_occurrence():
    jobs = pd.DataFrame(
        [
            {
                "title": "Data Scientist",
                "company": "Company A",
                "location": "Paris",
                "contract_type": "CDI",
                "source_url": "https://example.com/job-1",
                "description": "Old description",
                "date_found": "2026-01-01",
                "source": "linkedin",
                "status": "to_review",
                "notes": "old",
            },
            {
                "title": "Data Scientist",
                "company": "Company A",
                "location": "Paris",
                "contract_type": "CDI",
                "source_url": "https://example.com/job-1",
                "description": "New description",
                "date_found": "2026-01-02",
                "source": "linkedin",
                "status": "to_review",
                "notes": "new",
            },
        ]
    )

    deduplicated = remove_duplicates(jobs)

    assert len(deduplicated) == 1
    assert deduplicated.iloc[0]["description"] == "New description"
    assert deduplicated.iloc[0]["notes"] == "new"


def test_remove_duplicates_by_title_company_location_keeps_last_occurrence():
    jobs = pd.DataFrame(
        [
            {
                "title": "Data Scientist",
                "company": "Company A",
                "location": "Paris",
                "contract_type": "CDI",
                "source_url": "https://example.com/job-old",
                "description": "Old description",
                "date_found": "2026-01-01",
                "source": "linkedin",
                "status": "to_review",
                "notes": "old",
            },
            {
                "title": "Data Scientist",
                "company": "Company A",
                "location": "Paris",
                "contract_type": "CDI",
                "source_url": "https://example.com/job-new",
                "description": "New description",
                "date_found": "2026-01-02",
                "source": "indeed",
                "status": "to_review",
                "notes": "new",
            },
        ]
    )

    deduplicated = remove_duplicates(jobs)

    assert len(deduplicated) == 1
    assert deduplicated.iloc[0]["source_url"] == "https://example.com/job-new"
    assert deduplicated.iloc[0]["description"] == "New description"


def test_remove_duplicates_keeps_different_jobs():
    jobs = pd.DataFrame(
        [
            {
                "title": "Data Scientist",
                "company": "Company A",
                "location": "Paris",
                "contract_type": "CDI",
                "source_url": "https://example.com/job-1",
                "description": "Python ML",
                "date_found": "2026-01-01",
                "source": "linkedin",
                "status": "to_review",
                "notes": "",
            },
            {
                "title": "ML Engineer",
                "company": "Company B",
                "location": "Paris",
                "contract_type": "CDI",
                "source_url": "https://example.com/job-2",
                "description": "LLM RAG",
                "date_found": "2026-01-01",
                "source": "indeed",
                "status": "to_review",
                "notes": "",
            },
        ]
    )

    deduplicated = remove_duplicates(jobs)

    assert len(deduplicated) == 2