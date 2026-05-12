# Ce fichier sert à générer des messages de candidature simples
# à partir des offres déjà scorées.

from matplotlib import lines
import pandas as pd

from config import SCORED_OFFERS_PATH, RESULTS_DIR


def generate_application_message(row: pd.Series) -> str:
    """
    Génère un message court et personnalisé pour une offre.

    L'objectif n'est pas encore d'écrire une lettre parfaite,
    mais de produire une bonne base de message LinkedIn / mail recruteur.
    """

    title = row["title"]
    company = row["company"]
    fit_type = row["fit_type"]

    core_score = row.get("core_data_science", 0)
    ai_score = row.get("ai_llm_nlp", 0)
    engineering_score = row.get("engineering", 0)
    health_score = row.get("health_research", 0)
    finance_score = row.get("finance_risk", 0)

    # On construit une phrase personnalisée selon le type d'offre.
    if ai_score >= 8:
        interest_sentence = (
            "J’ai notamment été attirée par les sujets autour du NLP, des LLM "
            "et de l’IA appliquée, qui sont très proches de mon expérience récente "
            "sur des pipelines LLM/RAG."
        )
    elif health_score >= 6:
        interest_sentence = (
            "J’ai notamment été attirée par la dimension santé, recherche et IA appliquée, "
            "qui correspond bien à mon intérêt pour les projets data à impact concret."
        )
    elif finance_score >= 4:
        interest_sentence = (
            "J’ai notamment été intéressée par la dimension data appliquée aux problématiques "
            "de risque, d’analyse et de décision, un environnement que je connais déjà à travers "
            "mon expérience en banque."
        )
    elif engineering_score >= 3:
        interest_sentence = (
            "J’ai notamment été intéressée par la dimension technique du poste, autour des pipelines, "
            "de l’industrialisation et de la mise en production de traitements data."
        )
    elif core_score >= 8:
        interest_sentence = (
            "J’ai notamment été intéressée par la place donnée au machine learning, "
            "à Python et à l’analyse de données."
        )
    else:
        interest_sentence = (
            "J’ai été intéressée par le positionnement du poste, qui semble mobiliser "
            "des compétences proches de mon parcours en data science."
        )

    message = f"""
Bonjour,

Je me permets de vous contacter au sujet de l’offre de {title} chez {company}.

{interest_sentence}

De mon côté, j’ai une formation en statistiques, machine learning et data science, avec une expérience récente en extraction d’information, LLM/RAG, SQL, Airflow et Docker. Je cherche aujourd’hui un poste de Data Scientist / ML / IA dans lequel je peux contribuer à des projets concrets, avec une vraie utilité métier.

Le poste me semble donc intéressant à explorer, car il correspond bien au type de missions que je recherche aujourd’hui.

Je serais ravie d’échanger avec vous si mon profil peut correspondre à vos besoins.

Bien cordialement,

Sharon Chemmama
""".strip()

    return message

def save_messages_to_markdown(selected_jobs: pd.DataFrame, output_path) -> None:
    """
    Sauvegarde les messages générés dans un fichier Markdown.

    Le Markdown est plus lisible qu'un CSV pour relire les messages,
    car il garde une structure propre avec des titres, des scores
    et le texte du message.
    """

    lines = []

    lines.append("# Messages de candidature générés")
    lines.append("")
    lines.append("Ce fichier contient les messages générés automatiquement à partir des offres scorées.")
    lines.append("")

    for _, row in selected_jobs.iterrows():
        lines.append(f"## {row['title']} — {row['company']}")
        lines.append("")
        lines.append("| Information | Valeur |")
        lines.append("|---|---|")
        lines.append(f"| Localisation | {row.get('location', '')} |")
        lines.append(f"| Source | {row.get('source', '')} |")
        lines.append(f"| Lien offre | {row.get('source_url', '')} |")
        lines.append(f"| Score brut | {row.get('score', '')} |")
        lines.append(f"| Score ajusté | {row.get('adjusted_score', '')} |")
        lines.append(f"| Recommandation | {row.get('recommendation', '')} |")
        lines.append(f"| Type de match | {row.get('fit_type', '')} |")
        lines.append(f"| Action suivante | {row.get('next_action', '')} |")
        lines.append("")
        lines.append("### Pourquoi cette offre ressort ?")
        lines.append("")
        lines.append(row["explanation"])
        lines.append("")
        lines.append("### Message proposé")
        lines.append("")
        lines.append(row["application_message"])
        lines.append("")
        lines.append("---")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    """
    Fonction principale.

    Elle :
    1. charge les offres scorées
    2. garde uniquement les offres pertinentes pour une vraie candidature
    3. exclut les offres trop senior ou avec un contrat non adapté
    4. génère un message pour les meilleures offres
    5. sauvegarde les messages dans results/application_messages.csv et .md
    """

    jobs = pd.read_csv(SCORED_OFFERS_PATH)

    selected_jobs = jobs[
        (jobs["adjusted_score"] >= 20)
        & (jobs["status"].isin(["to_review", "interested"]))
        & (jobs["seniority_level"] != "too_senior")
        & (jobs["contract_fit"] != "non_priority_contract")
    ].copy()

    selected_jobs = selected_jobs.sort_values(
        by="adjusted_score",
        ascending=False,
    ).head(20)

    selected_jobs["application_message"] = selected_jobs.apply(
        generate_application_message,
        axis=1,
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_DIR / "application_messages.csv"
    selected_jobs.to_csv(
    output_path,
    index=False,
    sep=";",
    encoding="utf-8-sig",
)

    markdown_output_path = RESULTS_DIR / "application_messages.md"
    save_messages_to_markdown(selected_jobs, markdown_output_path)

    print("Messages générés avec succès.")
    print(f"Nombre de messages générés : {len(selected_jobs)}")
    print(f"CSV sauvegardé ici : {output_path}")
    print(f"Markdown sauvegardé ici : {markdown_output_path}")

    for _, row in selected_jobs.iterrows():
        print("\n" + "=" * 80)
        print(f"{row['title']} - {row['company']}")
        print("=" * 80)
        print(row["application_message"])


if __name__ == "__main__":
    main()