from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"

NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
MODELS_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"

REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"


def create_project_dirs() -> None:
    """
    Create all standard project directories if they do not already exist.
    """
    directories = [
        RAW_DIR,
        INTERIM_DIR,
        PROCESSED_DIR,
        EXTERNAL_DIR,
        NOTEBOOKS_DIR,
        MODELS_DIR,
        RESULTS_DIR,
        FIGURES_DIR,
        TABLES_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)