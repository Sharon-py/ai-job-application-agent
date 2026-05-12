# Ce fichier contient toute la logique de scoring.
# Son rôle : prendre une description d'offre d'emploi
# et calculer à quel point elle correspond à ton profil.

# On définit plusieurs catégories importantes pour ton profil.
# Chaque catégorie a :
# - un poids : plus il est élevé, plus cette catégorie compte dans le score final
# - des mots-clés : si ces mots apparaissent dans l'offre, on ajoute des points

import re
import unicodedata

CATEGORIES = {
    "core_data_science": {
        "weight": 4,
        "keywords": [
            "python",
            "machine learning",
            "apprentissage automatique",
            "deep learning",
            "apprentissage profond",
            "data science",
            "science des données",
            "scikit-learn",
            "statistics",
            "statistical",
            "statistiques",
            "statistique",
            "modeling",
            "modélisation",
            "classification",
            "regression",
            "régression",
            "predictive",
            "prédictif",
            "modèle prédictif",
        ],
    },

    "ai_llm_nlp": {
        "weight": 4,
        "keywords": [
            "llm",
            "rag",
            "nlp",
            "generative ai",
            "ia générative",
            "intelligence artificielle générative",
            "ai agents",
            "agents ia",
            "agent ia",
            "natural language processing",
            "traitement du langage naturel",
            "taln",
            "prompt engineering",
            "ingénierie de prompt",
            "information extraction",
            "extraction d'information",
            "extraction d’informations",
            "document analysis",
            "analyse documentaire",
            "analyse de documents",
        ],
    },

    "engineering": {
        "weight": 3,
        "keywords": [
            "docker",
            "airflow",
            "api",
            "pipeline",
            "pipelines",
            "production",
            "mise en production",
            "industrialisation",
            "deployment",
            "déploiement",
            "sql",
            "spark",
            "mlflow",
            "ci/cd",
            "intégration continue",
            "déploiement continu",
            "scalable",
            "scalabilité",
            "monitoring",
            "observabilité",
            "observability",
        ],
    },

    "health_research": {
        "weight": 2,
        "keywords": [
            "health",
            "santé",
            "biomedical",
            "biomédical",
            "medical",
            "médical",
            "clinical",
            "clinique",
            "research",
            "recherche",
            "hospital",
            "hôpital",
            "hospitalier",
            "genomics",
            "génomique",
            "imaging",
            "imagerie",
            "brain",
            "cerveau",
            "diagnosis",
            "diagnostic",
        ],
    },

    "business_reporting": {
        "weight": 1,
        "keywords": [
            "dashboard",
            "dashboarding",
            "tableau de bord",
            "reporting",
            "power bi",
            "tableau",
            "kpi",
            "indicateurs",
            "excel",
            "analyse métier",
            "business analysis",
        ],
    },

    "finance_risk": {
        "weight": 2,
        "keywords": [
            "risk",
            "risque",
            "finance",
            "financial",
            "financier",
            "banking",
            "banque",
            "bancaire",
            "esg",
            "stress test",
            "test de résistance",
            "solvency",
            "solvabilité",
            "credit risk",
            "risque de crédit",
        ],
    },
}

SENIORITY_SIGNALS = {
    "too_senior": [
        "principal",
        "staff",
        "lead engineer",
        "tech lead",
        "engineering leadership",
        "8+ years",
        "8 years",
        "10+ years",
        "10 years",
        "senior leadership",
        "mentor engineers",
        "system design interview",

        "principal engineer",
        "ingénieur principal",
        "staff engineer",
        "lead technique",
        "responsable technique",
        "leadership technique",
        "8 ans d'expérience",
        "8 ans d’expérience",
        "10 ans d'expérience",
        "10 ans d’expérience",
        "mentorer",
        "encadrer des ingénieurs",
        "entretien system design",
        "entretien de conception système",
    ],
    "senior": [
        "senior",
        "confirmé",
        "expérimenté",
        "lead",
        "5+ years",
        "5 years",
        "6+ years",
        "6 years",
        "7+ years",
        "7 years",
        "5 ans d'expérience",
        "5 ans d’expérience",
        "6 ans d'expérience",
        "6 ans d’expérience",
        "7 ans d'expérience",
        "7 ans d’expérience",
    ],
    "junior_friendly": [
        "junior",
        "graduate",
        "entry level",
        "early career",
        "débutant",
        "jeune diplômé",
        "jeune diplome",
        "première expérience",
        "premiere experience",
        "0-2 years",
        "1-2 years",
        "0 à 2 ans",
        "1 à 2 ans",
        "first experience",
    ],
}

CONTRACT_SIGNALS = {
    "target_contract": [
        "cdi",
        "permanent",
        "full-time",
        "full time",
        "temps plein",
    ],
    "possible_contract": [
        "cdd",
        "fixed-term",
        "fixed term",
    ],
    "non_priority_contract": [
        "freelance",
        "contractor",
        "stage",
        "internship",
        "alternance",
        "apprentissage",
        "apprenticeship",
        "student",
        "student job",
        "trainee",
        "stagiaire",
    ],
}  


def normalize_text(text: str) -> str:
    """
    Nettoie un texte pour faciliter la recherche de mots-clés.
    Met en minuscules et enlève les accents.
    """

    if not isinstance(text, str):
        return ""

    text = text.lower()

    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )

    return text

def contains_signal(text: str, signal: str) -> bool:
    """
    Checks whether a signal appears as a real expression in the text.

    This avoids false positives like:
    - intern found inside internal
    - stage found inside multi-stage
    """

    text = normalize_text(text)
    signal = normalize_text(signal)

    pattern = r"(?<![a-zA-Z])" + re.escape(signal) + r"(?![a-zA-Z])"

    return re.search(pattern, text) is not None

def detect_contract_type(text: str) -> dict:
    """
    Detects whether the contract type seems aligned with the current job search.

    Important:
    We remove ML expressions like "apprentissage automatique" before detecting
    apprenticeship contracts, otherwise they create false positives.
    """

    text = normalize_text(text)

    # Avoid confusing "apprentissage automatique" with apprenticeship contracts.
    ml_expressions = [
        "apprentissage automatique",
        "apprentissage profond",
        "apprentissage supervise",
        "apprentissage non supervise",
        "apprentissage par renforcement",
    ]

    for expression in ml_expressions:
        text = text.replace(expression, "")

    matched_signals = {
        "target_contract": [],
        "possible_contract": [],
        "non_priority_contract": [],
    }

    for level, signals in CONTRACT_SIGNALS.items():
        for signal in signals:
            if contains_signal(text, signal):
                matched_signals[level].append(signal)

    if matched_signals["non_priority_contract"]:
        return {
            "contract_fit": "non_priority_contract",
            "contract_penalty": 25,
            "contract_warning": (
                "Le type de contrat ne correspond pas à la recherche actuelle "
                f"(signaux détectés : {', '.join(matched_signals['non_priority_contract'])})."
            ),
            "contract_signals": matched_signals,
        }

    if matched_signals["target_contract"]:
        return {
            "contract_fit": "target_contract",
            "contract_penalty": 0,
            "contract_warning": "Le type de contrat semble aligné avec la recherche actuelle.",
            "contract_signals": matched_signals,
        }

    if matched_signals["possible_contract"]:
        return {
            "contract_fit": "possible_contract",
            "contract_penalty": 2,
            "contract_warning": "Le type de contrat est possible mais à vérifier.",
            "contract_signals": matched_signals,
        }

    return {
        "contract_fit": "not_specified",
        "contract_penalty": 0,
        "contract_warning": "Aucun signal clair sur le type de contrat.",
        "contract_signals": matched_signals,
    }

def detect_seniority(description: str) -> dict:
    """
    Detects whether a job offer seems junior-friendly, senior, or ambiguous.

    Important rule:
    If junior-friendly signals are present, they override senior signals.
    This avoids losing potentially relevant offers that mention several levels.
    """

    description = normalize_text(description)

    matched_signals = {
        "too_senior": [],
        "senior": [],
        "junior_friendly": [],
    }

    for level, signals in SENIORITY_SIGNALS.items():
        for signal in signals:
            if contains_signal(description, signal):
                matched_signals[level].append(signal)

    has_junior = bool(matched_signals["junior_friendly"])
    has_senior = bool(matched_signals["senior"])
    has_too_senior = bool(matched_signals["too_senior"])

    if has_junior and (has_senior or has_too_senior):
        return {
            "seniority_level": "mixed_seniority",
            "seniority_penalty": 0,
            "seniority_warning": (
                "L'offre contient à la fois des signaux junior/accessibles "
                "et des signaux senior. À relire manuellement avant décision."
            ),
            "seniority_signals": matched_signals,
        }

    if has_junior:
        return {
            "seniority_level": "junior_friendly",
            "seniority_penalty": 0,
            "seniority_warning": (
                "L'offre contient des signaux compatibles avec un profil junior ou early-career."
            ),
            "seniority_signals": matched_signals,
        }

    if has_too_senior:
        return {
            "seniority_level": "too_senior",
            "seniority_penalty": 12,
            "seniority_warning": (
                "L'offre semble trop senior pour le profil actuel "
                f"(signaux détectés : {', '.join(matched_signals['too_senior'])})."
            ),
            "seniority_signals": matched_signals,
        }

    if has_senior:
        return {
            "seniority_level": "senior",
            "seniority_penalty": 6,
            "seniority_warning": (
                "L'offre semble senior et doit être analysée avec prudence "
                f"(signaux détectés : {', '.join(matched_signals['senior'])})."
            ),
            "seniority_signals": matched_signals,
        }

    return {
        "seniority_level": "not_specified",
        "seniority_penalty": 0,
        "seniority_warning": "Aucun signal fort de seniorité détecté.",
        "seniority_signals": matched_signals,
    }

def score_offer(description: str) -> dict:
    """
    Cette fonction prend la description d'une offre
    et renvoie un dictionnaire avec :
    - le score total
    - le score ajusté avec pénalité seniorité et contrat
    - les scores par catégorie
    - les mots-clés trouvés
    - une explication lisible
    - un niveau de recommandation
    """

    description = normalize_text(description)

    total_score = 0
    category_scores = {}
    matched_keywords = {}

    for category, params in CATEGORIES.items():
        weight = params["weight"]
        keywords = params["keywords"]

        matches = []
        category_score = 0

        for keyword in keywords:
            if normalize_text(keyword) in description:
                matches.append(keyword)
                category_score += weight

        category_scores[category] = category_score
        matched_keywords[category] = matches
        total_score += category_score

    explanation = generate_explanation(category_scores, matched_keywords)

    seniority_result = detect_seniority(description)
    contract_result = detect_contract_type(description)

    seniority_penalty = seniority_result["seniority_penalty"]
    contract_penalty = contract_result["contract_penalty"]

    adjusted_score = max(
        total_score - seniority_penalty - contract_penalty,
        0,
    )

    recommendation = get_recommendation_level(adjusted_score)
    fit_type = get_fit_type(category_scores)
    next_action = get_next_action(adjusted_score, category_scores)

    if seniority_result["seniority_level"] == "too_senior":
        recommendation = "Très aligné techniquement mais probablement trop senior"
        next_action = "Archiver ou garder comme inspiration, mais ne pas prioriser"

    elif seniority_result["seniority_level"] == "mixed_seniority":
        recommendation = "Intéressant mais seniorité à vérifier"
        next_action = "Lire l'offre en détail avant de décider"

    elif seniority_result["seniority_level"] == "senior":
        recommendation = "Intéressant mais possiblement senior"
        next_action = "Lire en détail avant de candidater"

    if contract_result["contract_fit"] == "non_priority_contract":
        recommendation = "Non prioritaire car contrat non adapté"
        next_action = "Ne pas prioriser pour la recherche actuelle"

    return {
        "score": total_score,
        "adjusted_score": adjusted_score,
        "recommendation": recommendation,
        "fit_type": fit_type,
        "next_action": next_action,
        "explanation": explanation,

        "seniority_level": seniority_result["seniority_level"],
        "seniority_warning": seniority_result["seniority_warning"],
        "seniority_penalty": seniority_penalty,
        "seniority_signals": seniority_result["seniority_signals"],

        "contract_fit": contract_result["contract_fit"],
        "contract_warning": contract_result["contract_warning"],
        "contract_penalty": contract_penalty,
        "contract_signals": contract_result["contract_signals"],

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
    Résume le type de correspondance entre l'offre et ton profil.
    Version robuste : évite les erreurs si une catégorie est absente.
    """

    ai_llm_nlp = category_scores.get("ai_llm_nlp", 0)
    core_data_science = category_scores.get("core_data_science", 0)
    engineering = category_scores.get("engineering", 0)
    health_research = category_scores.get("health_research", 0)
    finance_risk = category_scores.get("finance_risk", 0)
    business_reporting = category_scores.get("business_reporting", 0)

    if ai_llm_nlp >= 8 and core_data_science >= 4:
        return "Très aligné IA / LLM / Data Science"

    if core_data_science >= 8 and engineering >= 3:
        return "Très aligné Data Science / Engineering"

    if health_research >= 4 and core_data_science >= 4:
        return "Bon match avec bonus santé / recherche"

    if finance_risk >= 4 and core_data_science >= 4:
        return "Bon match data avec orientation finance / risque"

    if business_reporting >= 2 and core_data_science == 0:
        return "Plutôt orienté reporting / dashboard"

    return "Match général à analyser"

def get_next_action(score: int, category_scores: dict) -> str:
    """
    Propose une action concrète après le scoring.
    Version robuste : évite les erreurs si une catégorie est absente.
    """

    core_data_science = category_scores.get("core_data_science", 0)
    health_research = category_scores.get("health_research", 0)
    business_reporting = category_scores.get("business_reporting", 0)

    if score >= 20:
        return "Candidater rapidement"

    if score >= 14:
        return "Lire l'offre en détail et préparer une candidature"

    if health_research >= 4:
        return "Regarder en détail grâce au bonus santé / recherche"

    if business_reporting >= 2 and core_data_science == 0:
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