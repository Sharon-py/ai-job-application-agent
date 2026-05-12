from datetime import date
from time import sleep

import pandas as pd
from jobspy import scrape_jobs

from config import JOB_OFFERS_PATH, COLLECTED_JOBS_PATH


LOCATION = "Paris, France"
RESULTS_PER_QUERY = 15
HOURS_OLD = 10  # 7 derniers jours environ


SEARCH_TERMS = [
    # Data Science général — FR / EN
    "Data Scientist junior",
    "Junior Data Scientist",
    "Data Scientist early career",
    "Data Scientist first experience",
    "Data Scientist young graduate",
    "Data Scientist jeune diplômé",
    "Data Scientist première expérience",
    "Data Scientist confirmé",
    "Data Scientist 2 years experience",
    "Data Scientist 3 years experience",
    "Data Scientist 5 years experience",

    # Machine Learning / AI
    "Machine Learning Engineer junior",
    "Junior Machine Learning Engineer",
    "ML Engineer junior",
    "AI Engineer junior",
    "Junior AI Engineer",
    "Ingénieur IA junior",
    "Ingénieur Machine Learning junior",
    "Machine Learning Engineer 2 years experience",
    "Machine Learning Engineer 3 years experience",
    "Machine Learning Engineer 5 years experience",

    # LLM / NLP / GenAI / Agents
    "Data Scientist LLM junior",
    "AI Engineer LLM junior",
    "NLP Data Scientist junior",
    "NLP Engineer junior",
    "Generative AI Engineer junior",
    "Ingénieur IA générative junior",
    "Data Scientist NLP",
    "Data Scientist RAG",
    "LLM Engineer junior",
    "AI Agent Engineer junior",
    "Prompt Engineer Data Scientist",
    "Data Scientist IA générative",

    # Data Engineering accessible
    "Data Engineer junior",
    "Junior Data Engineer",
    "Data Engineer Python SQL junior",
    "Data Engineer Airflow Docker junior",
    "Data Engineer Spark junior",
    "Ingénieur Data junior",
    "Data Engineer 2 years experience",
    "Data Engineer 3 years experience",
    "Data Engineer confirmé",

    # MLOps / production ML
    "MLOps Engineer junior",
    "Junior MLOps Engineer",
    "Machine Learning Ops junior",
    "Data Scientist production Python Docker",
    "ML Engineer Docker Airflow",
    "Data Scientist industrialisation modèle",
    "Machine Learning Engineer production",

    # Analytics proche data science
    "Data Analyst Python SQL machine learning",
    "Data Analyst junior Python SQL",
    "Analytics Engineer junior",
    "Junior Analytics Engineer",
    "Business Data Analyst Python SQL",
    "Data Analyst IA",
    "Data Analyst machine learning",

    # Secteurs intéressants, sans être bloquants
    "Data Scientist santé",
    "Data Scientist biomédical",
    "Data Scientist recherche clinique",
    "Data Scientist hospitalier",
    "Data Scientist finance risque",
    "Data Scientist assurance",
    "Data Scientist énergie",
    "Data Scientist industrie",
    "Data Scientist transport",
    "Data Scientist retail",
    "Data Scientist marketing science",
]


EXPECTED_COLUMNS = [
    "title",
    "company",
    "location",
    "contract_type",
    "source_url",
    "description",
    "date_found",
    "source",
    "status",
    "notes",
]

SITE_NAMES = ["google", "linkedin", "indeed"]


def collect_jobs_for_query(query: str) -> pd.DataFrame:
    """
    Collects job offers for one query using JobSpy.

    The collector does not decide if a job is relevant.
    It only collects. The scoring pipeline will rank and filter later.
    """

    jobs = scrape_jobs(
        site_name=SITE_NAMES,
        search_term=query,
        location=LOCATION,
        results_wanted=RESULTS_PER_QUERY,
        hours_old=HOURS_OLD,
        country_indeed="France",
    )

    if jobs is None or jobs.empty:
        return pd.DataFrame()

    jobs["search_query"] = query

    return jobs


def normalize_collected_jobs(jobs: pd.DataFrame) -> pd.DataFrame:
    """
    Converts JobSpy output to the project's job_offers.csv schema.
    """

    normalized = pd.DataFrame()

    normalized["title"] = jobs.get("title", "")
    normalized["company"] = jobs.get("company", "")
    normalized["location"] = jobs.get("location", "")
    normalized["contract_type"] = jobs.get("job_type", "")
    normalized["source_url"] = jobs.get("job_url", "")
    normalized["description"] = jobs.get("description", "")
    normalized["date_found"] = date.today().isoformat()
    normalized["source"] = jobs.get("site", "")
    normalized["status"] = "to_review"

    if "search_query" in jobs.columns:
        normalized["notes"] = (
            "Collected automatically with JobSpy | query: "
            + jobs["search_query"].fillna("").astype(str)
        )
    else:
        normalized["notes"] = "Collected automatically with JobSpy"

    return normalized


def load_existing_jobs() -> pd.DataFrame:
    """
    Loads existing job_offers.csv if it exists.
    """

    if JOB_OFFERS_PATH.exists():
        return pd.read_csv(JOB_OFFERS_PATH)

    return pd.DataFrame(columns=EXPECTED_COLUMNS)


def clean_text_columns(jobs: pd.DataFrame) -> pd.DataFrame:
    """
    Basic cleaning to avoid NaN and messy text fields.
    """

    jobs = jobs.copy()

    for column in EXPECTED_COLUMNS:
        if column not in jobs.columns:
            jobs[column] = ""

    for column in EXPECTED_COLUMNS:
        jobs[column] = jobs[column].fillna("").astype(str).str.strip()

    return jobs[EXPECTED_COLUMNS]


def remove_duplicates(jobs: pd.DataFrame) -> pd.DataFrame:
    """
    Removes duplicates without being too aggressive.

    Priority:
    1. Same non-empty source URL = duplicate.
    2. Same title + company + location = likely duplicate.

    The function keeps the last occurrence in the original order.
    This is useful because newly collected jobs are appended after existing jobs.
    """

    jobs = jobs.copy()

    # Keep original order so "keep=last" really means:
    # keep the most recently appended version.
    jobs["_original_order"] = range(len(jobs))

    # Deduplicate jobs with a real source URL.
    jobs_with_url = jobs[jobs["source_url"].fillna("").astype(str).str.strip() != ""]
    jobs_without_url = jobs[jobs["source_url"].fillna("").astype(str).str.strip() == ""]

    jobs_with_url = jobs_with_url.drop_duplicates(
        subset=["source_url"],
        keep="last",
    )

    jobs = pd.concat(
        [jobs_with_url, jobs_without_url],
        ignore_index=True,
    )

    # Deduplicate likely duplicates across different sources.
    jobs = jobs.sort_values("_original_order")
    jobs = jobs.drop_duplicates(
        subset=["title", "company", "location"],
        keep="last",
    )

    jobs = jobs.sort_values("_original_order")
    jobs = jobs.drop(columns=["_original_order"])

    return jobs


def main():
    all_raw_results = []
    all_normalized_jobs = []

    for index, query in enumerate(SEARCH_TERMS, start=1):
        print("=" * 80)
        print(f"[{index}/{len(SEARCH_TERMS)}] Searching jobs for: {query}")
        print("=" * 80)

        try:
            raw_jobs = collect_jobs_for_query(query)
        except Exception as error:
            print(f"Error while searching '{query}': {error}")
            continue

        if raw_jobs.empty:
            print("No jobs found.")
            continue

        print(f"Raw jobs collected: {len(raw_jobs)}")

        normalized_jobs = normalize_collected_jobs(raw_jobs)

        all_raw_results.append(raw_jobs)
        all_normalized_jobs.append(normalized_jobs)

        # Petite pause pour éviter d'enchaîner trop brutalement les requêtes.
        sleep(2)

    if not all_normalized_jobs:
        print("No jobs collected.")
        return

    collected_raw = pd.concat(all_raw_results, ignore_index=True)
    collected_normalized = pd.concat(all_normalized_jobs, ignore_index=True)

    collected_normalized = clean_text_columns(collected_normalized)

    existing_jobs = load_existing_jobs()
    existing_jobs = clean_text_columns(existing_jobs)

    final_jobs = pd.concat(
        [existing_jobs, collected_normalized],
        ignore_index=True,
    )

    final_jobs = remove_duplicates(final_jobs)

    JOB_OFFERS_PATH.parent.mkdir(parents=True, exist_ok=True)

    collected_raw.to_csv(COLLECTED_JOBS_PATH, index=False)
    final_jobs.to_csv(JOB_OFFERS_PATH, index=False)

    print("")
    print("Automatic job collection completed.")
    print(f"Raw collected jobs saved to: {COLLECTED_JOBS_PATH}")
    print(f"Project job offers saved to: {JOB_OFFERS_PATH}")
    print(f"New collected jobs before deduplication: {len(collected_normalized)}")
    print(f"Total jobs in job_offers.csv after deduplication: {len(final_jobs)}")

    print("")
    print("Latest jobs:")
    print(
        final_jobs[
            ["title", "company", "location", "source", "status"]
        ].tail(20)
    )


if __name__ == "__main__":
    main()