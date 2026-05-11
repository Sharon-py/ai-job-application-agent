# Ce fichier contient toute la logique de scoring.
# Son rôle : prendre une description d'offre d'emploi
# et calculer à quel point elle correspond à ton profil.

# On définit plusieurs catégories importantes pour ton profil.
# Chaque catégorie a :
# - un poids : plus il est élevé, plus cette catégorie compte dans le score final
# - des mots-clés : si ces mots apparaissent dans l'offre, on ajoute des points

CATEGORIES = {
    "core_data_science": {
        "weight": 4,
        "keywords": [
            "python",
            "machine learning",
            "deep learning",
            "data science",
            "scikit-learn",
            "statistics",
            "statistical",
            "modeling",
            "classification",
            "regression",
            "predictive",
        ],
    },
    "ai_llm_nlp": {
        "weight": 4,
        "keywords": [
            "llm",
            "rag",
            "nlm",
            "nlp",
            "generative ai",
            "ai agents",
            "natural language processing",
            "prompt engineering",
            "information extraction",
            "document analysis",
        ],
    },
    "engineering": {
        "weight": 3,
        "keywords": [
            "docker",
            "airflow",
            "api",
            "pipeline",
            "production",
            "deployment",
            "sql",
            "spark",
            "mlflow",
            "ci/cd",
        ],
    },
    "health_research": {
        "weight": 2,
        "keywords": [
            "health",
            "biomedical",
            "medical",
            "clinical",
            "research",
            "hospital",
            "genomics",
            "imaging",
            "brain",
            "diagnosis",
        ],
    },
    "business_reporting": {
        "weight": 1,
        "keywords": [
            "dashboard",
            "reporting",
            "power bi",
            "tableau",
            "kpi",
            "excel",
        ],
    },
    "finance_risk": {
        "weight": 2,
        "keywords": [
            "risk",
            "finance",
            "banking",
            "esg",
            "stress test",
            "solvency",
            "credit risk",
        ],
    },
}


def normalize_text(text: str) -> str:
    """
    Cette fonction nettoie un texte pour faciliter la recherche de mots-clés.

    Exemple :
    "Python and Machine Learning" devient "python and machine learning"

    Comme ça, on évite les problèmes de majuscules/minuscules.
    """

    # Si le texte n'est pas une chaîne de caractères,
    # on renvoie une chaîne vide pour éviter une erreur.
    if not isinstance(text, str):
        return ""

    # On met tout en minuscules.
    return text.lower()


def score_offer(description: str) -> dict:
    """
    Cette fonction prend la description d'une offre
    et renvoie un dictionnaire avec :
    - le score total
    - les scores par catégorie
    - les mots-clés trouvés
    - une explication lisible
    - un niveau de recommandation
    """

    # On nettoie la description avant de chercher les mots-clés.
    description = normalize_text(description)

    # Score global de l'offre.
    total_score = 0

    # Ici, on stockera le score obtenu pour chaque catégorie.
    # Exemple :
    # {"core_data_science": 6, "ai_llm_nlp": 8, ...}
    category_scores = {}

    # Ici, on stockera les mots-clés trouvés dans chaque catégorie.
    # Exemple :
    # {"core_data_science": ["python", "machine learning"], ...}
    matched_keywords = {}

    # On parcourt chaque catégorie définie plus haut.
    for category, params in CATEGORIES.items():

        # On récupère le poids de la catégorie.
        weight = params["weight"]

        # On récupère la liste des mots-clés de la catégorie.
        keywords = params["keywords"]

        # Liste des mots-clés trouvés pour cette catégorie.
        matches = []

        # Score de cette catégorie uniquement.
        category_score = 0

        # On teste chaque mot-clé.
        for keyword in keywords:

            # Si le mot-clé est présent dans la description,
            # alors l'offre gagne des points.
            if keyword.lower() in description:
                matches.append(keyword)
                category_score += weight

        # On sauvegarde le score de la catégorie.
        category_scores[category] = category_score

        # On sauvegarde les mots-clés trouvés.
        matched_keywords[category] = matches

        # On ajoute le score de cette catégorie au score total.
        total_score += category_score

    # On génère une phrase d'explication à partir des scores.
    explanation = generate_explanation(category_scores, matched_keywords)

    # On transforme le score total en niveau lisible.
    recommendation = get_recommendation_level(total_score)
    fit_type = get_fit_type(category_scores)
    next_action = get_next_action(total_score, category_scores)

    # On renvoie tous les résultats sous forme de dictionnaire.
    return {
        "score": total_score,
        "recommendation": recommendation,
        "fit_type": fit_type,
        "next_action": next_action,
        "explanation": explanation,
        "matched_keywords": matched_keywords,
        **category_scores,
    }


def generate_explanation(category_scores: dict, matched_keywords: dict) -> str:
    """
    Cette fonction crée une explication lisible pour comprendre
    pourquoi une offre a obtenu son score.

    Au lieu d'afficher seulement :
    score = 18

    On veut afficher une phrase du type :
    L'offre matche avec ton profil sur : IA générative, data science, santé.
    """

    # On garde seulement les catégories qui ont marqué au moins 1 point.
    strong_categories = [
        category
        for category, score in category_scores.items()
        if score > 0
    ]

    # Si aucune catégorie ne matche,
    # on renvoie une explication simple.
    if not strong_categories:
        return "L'offre présente peu de correspondance directe avec le profil cible actuel."
    # Noms plus jolis à afficher dans l'explication.
    readable_names = {
        "core_data_science": "data science / machine learning",
        "ai_llm_nlp": "IA générative / LLM / NLP",
        "engineering": "mise en production et pipelines data",
        "health_research": "bonus santé, biomédical ou recherche",
        "business_reporting": "reporting et dashboards",
        "finance_risk": "finance, risque ou ESG",
    }

    # Cette liste va contenir les morceaux de phrase.
    parts = []

    # On parcourt les catégories qui ont matché.
    for category in strong_categories:

        # On récupère le nom lisible de la catégorie.
        name = readable_names.get(category, category)

        # On récupère les mots-clés trouvés pour cette catégorie.
        keywords = matched_keywords.get(category, [])

        # Si on a trouvé des mots-clés,
        # on les ajoute dans l'explication.
        if keywords:
            parts.append(f"{name} ({', '.join(keywords)})")

    # On rassemble tous les morceaux dans une phrase finale.
    return (
        "L'offre présente une correspondance avec le profil sur les dimensions suivantes : "
        + "; ".join(parts)
        + "."
    )

def get_fit_type(category_scores: dict) -> str:
    """
    Cette fonction résume le type de correspondance entre l'offre et ton profil.
    Elle ne regarde pas seulement le score total, mais aussi d'où viennent les points.
    """

    if category_scores["ai_llm_nlp"] >= 8 and category_scores["core_data_science"] >= 4:
        return "Très aligné IA / LLM / Data Science"

    if category_scores["core_data_science"] >= 8 and category_scores["engineering"] >= 3:
        return "Très aligné Data Science / Engineering"

    if category_scores["health_research"] >= 4 and category_scores["core_data_science"] >= 4:
        return "Bon match avec bonus santé / recherche"

    if category_scores["finance_risk"] >= 4 and category_scores["core_data_science"] >= 4:
        return "Bon match data avec orientation finance / risque"

    if category_scores["business_reporting"] >= 2 and category_scores["core_data_science"] == 0:
        return "Plutôt orienté reporting / dashboard"

    return "Match général à analyser"


def get_next_action(score: int, category_scores: dict) -> str:
    """
    Cette fonction propose une action concrète après le scoring.
    Le but est d'aider à décider quoi faire avec l'offre.
    """

    if score >= 20:
        return "Candidater rapidement"

    if score >= 14:
        return "Lire l'offre en détail et préparer une candidature"

    if category_scores["health_research"] >= 4:
        return "Regarder en détail grâce au bonus santé / recherche"

    if category_scores["business_reporting"] >= 2 and category_scores["core_data_science"] == 0:
        return "Garder en option si besoin"

    if score >= 8:
        return "À comparer avec d'autres offres"

    return "Peu prioritaire pour le moment"


def get_recommendation_level(score: int) -> str:
    """
    Cette fonction transforme un score numérique en recommandation lisible.

    Exemple :
    24 devient "Très bonne opportunité"
    14 devient "Opportunité intéressante"
    """

    if score >= 20:
        return "Très bonne opportunité"
    elif score >= 12:
        return "Opportunité intéressante"
    elif score >= 6:
        return "À regarder"
    else:
        return "Peu prioritaire"