# Ce fichier sert à charger les offres d'emploi,
# appliquer le scoring,
# puis sauvegarder les résultats dans un fichier CSV.

import pandas as pd

# On importe les chemins définis dans config.py.
# Comme ça, on évite d'écrire les chemins à la main partout dans le projet.
from config import JOB_OFFERS_PATH, SCORED_OFFERS_PATH

# On importe la fonction qui calcule le score d'une offre.
from scoring import score_offer


def main():
    """
    Fonction principale du script.

    Elle fait 4 choses :
    1. Charger les offres depuis data/raw/job_offers.csv
    2. Calculer un score pour chaque offre
    3. Trier les offres de la plus intéressante à la moins intéressante
    4. Sauvegarder le résultat dans data/processed/scored_job_offers.csv
    """

    # On lit le fichier CSV qui contient les offres.
    jobs = pd.read_csv(JOB_OFFERS_PATH)

    # Pour chaque description d'offre, on applique la fonction score_offer.
    #
    # Résultat :
    # scoring_results contient une série de dictionnaires.
    #
    # Exemple :
    # {
    #   "score": 18,
    #   "recommendation": "Opportunité intéressante",
    #   "explanation": "...",
    #   ...
    # }
    scoring_results = jobs["description"].apply(score_offer)

    # On transforme les dictionnaires de scoring en DataFrame.
    #
    # Avant :
    # une colonne avec des dictionnaires
    #
    # Après :
    # plusieurs colonnes :
    # score, recommendation, explanation, core_data_science, etc.
    scoring_df = pd.DataFrame(scoring_results.tolist())

    # On colle les colonnes originales des offres
    # avec les nouvelles colonnes de scoring.
    jobs_scored = pd.concat([jobs, scoring_df], axis=1)

    # On trie les offres par score décroissant.
    # La meilleure offre apparaît donc en premier.
    jobs_scored = jobs_scored.sort_values("score", ascending=False)

    # On sauvegarde le résultat dans data/processed/scored_job_offers.csv.
    jobs_scored.to_csv(SCORED_OFFERS_PATH, index=False)

    # On affiche un résumé dans le terminal.
    print("Offres classées :")

    print(
        jobs_scored[
            [
                "title",
                "company",
                "location",
                "score",
                "recommendation",
                "fit_type",
                "next_action",
                "explanation",
            ]
        ]
    )


# Cette condition permet de lancer main()
# seulement quand on exécute directement ce fichier.
#
# Exemple :
# python src/data.py
#
# Si ce fichier est importé ailleurs,
# main() ne se lancera pas automatiquement.
if __name__ == "__main__":
    main()