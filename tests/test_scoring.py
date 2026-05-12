import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.append(str(SRC_DIR))

from scoring import score_offer, detect_contract_type, detect_seniority


def test_apprentissage_automatique_is_not_apprenticeship_contract():
    text = """
    Nous recherchons un Data Scientist Junior pour travailler sur des modèles
    de machine learning, d'apprentissage automatique et de classification.
    CDI à Paris.
    """

    result = detect_contract_type(text)

    assert result["contract_fit"] != "non_priority_contract"
    assert "apprentissage" not in result["contract_signals"]


def test_internship_is_non_priority_contract():
    text = """
    Data Scientist Internship.
    We are looking for a student for a 6-month internship in machine learning.
    """

    result = detect_contract_type(text)

    assert result["contract_fit"] == "non_priority_contract"
    assert result["contract_penalty"] > 0


def test_alternance_is_non_priority_contract():
    text = """
    Offre en alternance pour un poste de Data Analyst.
    Apprentissage possible sur 12 mois.
    """

    result = detect_contract_type(text)

    assert result["contract_fit"] == "non_priority_contract"
    assert result["contract_penalty"] > 0


def test_junior_offer_is_junior_friendly():
    text = """
    Data Scientist Junior.
    Poste ouvert aux jeunes diplômés avec une première expérience.
    Python, SQL, machine learning.
    """

    result = detect_seniority(text)

    assert result["seniority_level"] == "junior_friendly"
    assert result["seniority_penalty"] == 0


def test_principal_offer_is_too_senior():
    text = """
    Principal AI Engineer.
    We are looking for a staff-level engineer with 10+ years of experience,
    strong leadership, system design and mentoring experience.
    """

    result = detect_seniority(text)

    assert result["seniority_level"] == "too_senior"
    assert result["seniority_penalty"] > 0


def test_mixed_seniority_is_detected():
    text = """
    Data Scientist Junior.
    Poste ouvert aux jeunes diplômés, première expérience acceptée.
    Une expérience de 7+ years and team leadership would be a plus.
    """

    result = detect_seniority(text)

    assert result["seniority_level"] == "mixed_seniority"
    assert result["seniority_penalty"] == 0


def test_good_ai_offer_gets_positive_score():
    text = """
    AI Engineer CDI.
    You will work on LLM, RAG, NLP, information extraction, Python,
    SQL, Docker, Airflow and production machine learning pipelines.
    """

    result = score_offer(text)

    assert result["score"] > 0
    assert result["adjusted_score"] > 0
    assert result["contract_fit"] != "non_priority_contract"
    assert result["seniority_level"] != "too_senior"


def test_non_priority_contract_reduces_recommendation():
    text = """
    Data Scientist Internship.
    Python, machine learning, NLP, LLM, RAG, SQL, Docker.
    Student internship position.
    """

    result = score_offer(text)

    assert result["contract_fit"] == "non_priority_contract"
    assert result["recommendation"] == "Non prioritaire car contrat non adapté"
    assert result["next_action"] == "Ne pas prioriser pour la recherche actuelle"