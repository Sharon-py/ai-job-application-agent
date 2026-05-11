from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Data folders
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
INTERIM_DIR = DATA_DIR / "interim"
EXTERNAL_DIR = DATA_DIR / "external"

# Results folder
RESULTS_DIR = PROJECT_ROOT / "results"

# Main files
JOB_OFFERS_PATH = RAW_DIR / "job_offers.csv"
SCORED_OFFERS_PATH = PROCESSED_DIR / "scored_job_offers.csv"

# Application tracking
APPLICATION_TRACKER_PATH = PROCESSED_DIR / "application_tracker.csv"
SHORTLIST_PATH = RESULTS_DIR / "job_shortlist.md"