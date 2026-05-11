# Ce fichier sert à centraliser les chemins importants du projet.
# L'idée est simple : au lieu d'écrire les chemins partout,
# on les définit une seule fois ici.

from pathlib import Path

# ROOT_DIR correspond à la racine du projet.
# Exemple :
# C:/code/ai-job-application-agent
ROOT_DIR = Path(__file__).resolve().parents[1]

# Dossier principal des données.
DATA_DIR = ROOT_DIR / "data"

# Dossier contenant les données brutes.
RAW_DIR = DATA_DIR / "raw"

# Dossier contenant les données nettoyées ou transformées.
PROCESSED_DIR = DATA_DIR / "processed"

# Dossier contenant les résultats éventuels.
RESULTS_DIR = ROOT_DIR / "results"

# Chemin vers le fichier CSV des offres brutes.
JOB_OFFERS_PATH = RAW_DIR / "job_offers.csv"

# Chemin vers le fichier CSV des offres scorées.
SCORED_OFFERS_PATH = PROCESSED_DIR / "scored_job_offers.csv"