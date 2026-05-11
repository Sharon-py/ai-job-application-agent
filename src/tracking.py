import pandas as pd

from config import SCORED_OFFERS_PATH, APPLICATION_TRACKER_PATH, RESULTS_DIR, SHORTLIST_PATH
from schema import VALID_STATUSES


def load_scored_jobs() -> pd.DataFrame:
    """
    Loads scored job offers.
    """

    if not SCORED_OFFERS_PATH.exists():
        raise FileNotFoundError(
            f"Scored job offers file not found: {SCORED_OFFERS_PATH}\n"
            "Run python src/data.py first."
        )

    return pd.read_csv(SCORED_OFFERS_PATH)


def create_application_tracker(jobs: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a tracking table from scored job offers.
    """

    tracker_columns = [
        "title",
        "company",
        "location",
        "contract_type",
        "source",
        "source_url",
        "date_found",
        "status",
        "score",
        "recommendation",
        "fit_type",
        "next_action",
        "explanation",
        "notes",
    ]

    existing_columns = [
        column for column in tracker_columns
        if column in jobs.columns
    ]

    tracker = jobs[existing_columns].copy()

    if "status" not in tracker.columns:
        tracker["status"] = "to_review"

    if "notes" not in tracker.columns:
        tracker["notes"] = ""

    tracker = tracker.sort_values(
        by="score",
        ascending=False
    )

    return tracker


def export_shortlist(tracker: pd.DataFrame, min_score: int = 12) -> None:
    """
    Exports a readable Markdown shortlist.
    """

    shortlist = tracker[
        (tracker["score"] >= min_score)
        & (tracker["status"].isin(["to_review", "interested"]))
    ].copy()

    lines = []
    lines.append("# Job application shortlist")
    lines.append("")
    lines.append(
        "This file contains the most relevant job offers to review first."
    )
    lines.append("")

    if shortlist.empty:
        lines.append("No job offer matched the shortlist criteria.")
    else:
        for _, row in shortlist.iterrows():
            lines.append(f"## {row['title']} — {row['company']}")
            lines.append("")
            lines.append(f"- Location: {row.get('location', '')}")
            lines.append(f"- Contract: {row.get('contract_type', '')}")
            lines.append(f"- Source: {row.get('source', '')}")
            lines.append(f"- Status: {row.get('status', '')}")
            lines.append(f"- Score: {row.get('score', '')}")
            lines.append(f"- Recommendation: {row.get('recommendation', '')}")
            lines.append(f"- Fit type: {row.get('fit_type', '')}")
            lines.append(f"- Next action: {row.get('next_action', '')}")
            lines.append(f"- URL: {row.get('source_url', '')}")
            lines.append("")
            lines.append("### Why this offer is relevant")
            lines.append("")
            lines.append(str(row.get("explanation", "")))
            lines.append("")
            lines.append("---")
            lines.append("")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    SHORTLIST_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    jobs = load_scored_jobs()
    tracker = create_application_tracker(jobs)

    APPLICATION_TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    tracker.to_csv(APPLICATION_TRACKER_PATH, index=False)

    export_shortlist(tracker)

    print("Application tracker created.")
    print(f"Saved tracker to: {APPLICATION_TRACKER_PATH}")
    print(f"Saved shortlist to: {SHORTLIST_PATH}")

    columns_to_display = [
        "title",
        "company",
        "status",
        "score",
        "recommendation",
        "next_action",
    ]

    existing_columns = [
        column for column in columns_to_display
        if column in tracker.columns
    ]

    print(tracker[existing_columns].head(10))


if __name__ == "__main__":
    main()