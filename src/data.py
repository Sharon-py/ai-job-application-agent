from matplotlib.pyplot import title
import pandas as pd

from config import JOB_OFFERS_PATH, SCORED_OFFERS_PATH, PROCESSED_DIR
from scoring import score_offer
from schema import validate_job_offers_schema


def load_job_offers(path=JOB_OFFERS_PATH) -> pd.DataFrame:
    """
    Loads raw job offers from CSV.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Job offers file not found: {path}\n"
            "Create data/raw/job_offers.csv first."
        )

    jobs = pd.read_csv(path)
    validate_job_offers_schema(jobs)

    return jobs


def score_job_offers(jobs: pd.DataFrame) -> pd.DataFrame:
    """
    Applies the rule-based scoring function to all job offers.
    """

    scored_rows = []

    for _, row in jobs.iterrows():
        title = row.get("title", "")
        description = row.get("description", "")

        text_to_score = f"{title}\n\n{description}"

        scoring_result = score_offer(text_to_score)

        combined_row = {
            **row.to_dict(),
            **scoring_result,
        }

        scored_rows.append(combined_row)

    scored_jobs = pd.DataFrame(scored_rows)

    if "adjusted_score" in scored_jobs.columns:
        scored_jobs = scored_jobs.sort_values(
            by="adjusted_score",
            ascending=False
        )
    elif "score" in scored_jobs.columns:
        scored_jobs = scored_jobs.sort_values(
            by="score",
            ascending=False
        )

    return scored_jobs


def main():
    jobs = load_job_offers()
    scored_jobs = score_job_offers(jobs)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    scored_jobs.to_csv(SCORED_OFFERS_PATH, index=False)

    print("Scoring completed.")
    print(f"Saved scored job offers to: {SCORED_OFFERS_PATH}")

    columns_to_display = [
        "title",
        "company",
        "location",
        "status",
        "score",
        "recommendation",
        "fit_type",
        "next_action",
    ]

    existing_columns = [
        column for column in columns_to_display
        if column in scored_jobs.columns
    ]

    print(scored_jobs[existing_columns].head(10))


if __name__ == "__main__":
    main()