from pathlib import Path
from datetime import date

import pandas as pd

from config import RAW_DIR, JOB_OFFERS_PATH


JOB_DESCRIPTIONS_DIR = RAW_DIR / "job_descriptions"


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


def extract_field(text: str, field_name: str, default: str = "") -> str:
    """
    Extracts a metadata field from the beginning of a raw job description.

    Example:
    TITLE: Data Scientist
    """

    prefix = f"{field_name.upper()}:"

    for line in text.splitlines():
        line = line.strip()

        if line.upper().startswith(prefix):
            return line[len(prefix):].strip()

    return default


def extract_description(text: str) -> str:
    """
    Extracts the job description after the DESCRIPTION: marker.
    If the marker is missing, returns the full text.
    """

    marker = "DESCRIPTION:"

    if marker in text:
        return text.split(marker, 1)[1].strip()

    return text.strip()


def parse_job_file(path: Path) -> dict:
    """
    Parses one .txt job description file into a structured job offer row.
    """

    text = path.read_text(encoding="utf-8")

    title = extract_field(text, "TITLE", default=path.stem.replace("_", " ").title())
    company = extract_field(text, "COMPANY", default="")
    location = extract_field(text, "LOCATION", default="")
    contract_type = extract_field(text, "CONTRACT_TYPE", default="")
    source_url = extract_field(text, "SOURCE_URL", default="")
    source = extract_field(text, "SOURCE", default="Manual")
    status = extract_field(text, "STATUS", default="to_review")
    notes = extract_field(text, "NOTES", default="")

    description = extract_description(text)

    return {
        "title": title,
        "company": company,
        "location": location,
        "contract_type": contract_type,
        "source_url": source_url,
        "description": description,
        "date_found": date.today().isoformat(),
        "source": source,
        "status": status,
        "notes": notes,
    }


def load_existing_job_offers() -> pd.DataFrame:
    """
    Loads the existing job_offers.csv if it exists.
    Otherwise creates an empty dataframe with the expected columns.
    """

    if JOB_OFFERS_PATH.exists():
        return pd.read_csv(JOB_OFFERS_PATH)

    return pd.DataFrame(columns=EXPECTED_COLUMNS)


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes duplicated offers based on title, company and source_url.
    """

    return df.drop_duplicates(
        subset=["title", "company", "source_url"],
        keep="last"
    )


def main():
    if not JOB_DESCRIPTIONS_DIR.exists():
        raise FileNotFoundError(
            f"Folder not found: {JOB_DESCRIPTIONS_DIR}\n"
            "Create it with: mkdir -p data/raw/job_descriptions"
        )

    txt_files = sorted(JOB_DESCRIPTIONS_DIR.glob("*.txt"))

    if not txt_files:
        print(f"No .txt files found in {JOB_DESCRIPTIONS_DIR}")
        return

    parsed_jobs = []

    for path in txt_files:
        parsed_job = parse_job_file(path)
        parsed_jobs.append(parsed_job)

    new_jobs = pd.DataFrame(parsed_jobs)

    existing_jobs = load_existing_job_offers()
    all_jobs = pd.concat([existing_jobs, new_jobs], ignore_index=True)

    all_jobs = all_jobs[EXPECTED_COLUMNS]
    all_jobs = remove_duplicates(all_jobs)

    JOB_OFFERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_jobs.to_csv(JOB_OFFERS_PATH, index=False)

    print("Job descriptions parsed successfully.")
    print(f"Parsed files: {len(txt_files)}")
    print(f"Saved job offers to: {JOB_OFFERS_PATH}")

    print()
    print(all_jobs[["title", "company", "location", "status", "source"]].tail())


if __name__ == "__main__":
    main()