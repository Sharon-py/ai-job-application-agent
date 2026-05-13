from pathlib import Path
import sys
import html
import re
import hashlib

import pandas as pd
import streamlit as st
from st_click_detector import click_detector


# Allows the app to import files from src/
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.append(str(SRC_DIR))

from database import get_jobs, update_job_status


STATUS_OPTIONS = [
    "to_review",
    "interested",
    "applied",
    "rejected",
    "archived",
]


ACTION_LABELS = {
    "to_review": "À revoir",
    "interested": "À garder",
    "applied": "Déjà postulé",
    "rejected": "Refuser",
    "archived": "Archiver",
}


def safe_html(value) -> str:
    """
    Escapes text before injecting it in custom HTML.
    """

    if pd.isna(value):
        return ""

    return html.escape(str(value))


def make_click_id(job_id: str) -> str:
    """
    Creates a safe short HTML id for click detection.
    """

    digest = hashlib.md5(job_id.encode("utf-8")).hexdigest()
    return f"job_{digest}"


def load_jobs_from_database() -> pd.DataFrame:
    """
    Loads jobs directly from the SQLite database.
    """

    jobs = get_jobs()

    if jobs.empty:
        st.error(
            "Aucune offre trouvée dans SQLite. "
            "Lance d'abord : py src/import_existing_data.py"
        )
        st.stop()

    required_columns = [
        "job_id",
        "title",
        "company",
        "description",
        "source_url",
        "date_found",
        "date_posted",
        "adjusted_score",
        "recommendation",
        "next_action",
        "seniority_level",
        "contract_fit",
        "status",
        "personal_notes",
        "application_message",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in jobs.columns
    ]

    if missing_columns:
        st.error(
            "Colonnes manquantes dans la table SQLite jobs : "
            + ", ".join(missing_columns)
        )
        st.stop()

    jobs["adjusted_score"] = pd.to_numeric(
        jobs["adjusted_score"],
        errors="coerce",
    ).fillna(0)

    jobs["score"] = pd.to_numeric(
        jobs.get("score", 0),
        errors="coerce",
    ).fillna(0)

    jobs["status"] = jobs["status"].fillna("to_review")
    jobs["personal_notes"] = jobs["personal_notes"].fillna("")
    jobs["application_message"] = jobs["application_message"].fillna("")
    jobs["date_posted"] = jobs["date_posted"].fillna("")
    jobs["date_found"] = jobs["date_found"].fillna("")

    return jobs


def inject_custom_css() -> None:
    """
    Adds custom CSS to make the Streamlit app look cleaner.
    """

    st.markdown(
        """
        <style>
        .stApp {
            background: #f6f7fb;
        }

        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e5e7eb;
        }

        .main-title {
            font-size: 2rem;
            font-weight: 800;
            color: #111827;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            color: #6b7280;
            font-size: 0.95rem;
            margin-bottom: 1.5rem;
        }

        .small-help {
            color: #6b7280;
            font-size: 0.85rem;
        }

        .detail-panel {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 22px;
            padding: 22px;
            margin-bottom: 16px;
            box-shadow: 0 8px 26px rgba(15, 23, 42, 0.05);
        }

        .detail-title {
            font-size: 1.55rem;
            font-weight: 850;
            color: #111827;
            margin-bottom: 0.25rem;
        }

        .detail-subtitle {
            color: #6b7280;
            font-size: 0.95rem;
            margin-bottom: 1rem;
        }

        .pill {
            display: inline-block;
            padding: 4px 9px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 650;
            margin-right: 5px;
            margin-bottom: 5px;
        }

        .pill-score {
            background: #ecfdf5;
            color: #047857;
        }

        .pill-status {
            background: #eef2ff;
            color: #4338ca;
        }

        .pill-warning {
            background: #fff7ed;
            color: #c2410c;
        }

        .pill-muted {
            background: #f3f4f6;
            color: #4b5563;
        }

        div[data-testid="stButton"] > button {
            border-radius: 14px;
            border: 1px solid #e5e7eb;
            font-weight: 650;
        }

        div[data-testid="stButton"] > button:hover {
            border-color: #6366f1;
            color: #4338ca;
            box-shadow: 0 8px 24px rgba(79, 70, 229, 0.08);
        }

        textarea {
            border-radius: 14px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """
    Renders app header.
    """

    st.markdown(
        """
        <div class="main-title">💼 AI Job Application Agent</div>
        <div class="subtitle">
        Lis, filtre et suis tes candidatures data / IA depuis SQLite.
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_cards_html(
    jobs: pd.DataFrame,
    selected_job_id: str,
) -> tuple[str, dict[str, str]]:
    """
    Builds the HTML for all clickable job cards and a map from click id to job id.
    """

    click_id_to_job_id = {}

    cards = [
        """
        <style>
            body {
                margin: 0;
                background: transparent;
                font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }

            .cards-wrapper {
                padding: 2px 4px 12px 2px;
            }

            a.job-card-link {
                text-decoration: none !important;
                color: inherit !important;
                display: block;
            }

            .job-card {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 18px;
                padding: 16px;
                margin-bottom: 12px;
                box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
                cursor: pointer;
                transition: all 0.15s ease-in-out;
            }

            .job-card:hover {
                border-color: #6366f1;
                box-shadow: 0 8px 24px rgba(79, 70, 229, 0.10);
                transform: translateY(-1px);
            }

            .job-card-selected {
                border: 2px solid #6366f1;
                box-shadow: 0 8px 24px rgba(79, 70, 229, 0.12);
            }

            .job-title {
                font-size: 0.98rem;
                font-weight: 750;
                color: #111827;
                margin-bottom: 4px;
                line-height: 1.25;
            }

            .job-company {
                color: #4b5563;
                font-size: 0.88rem;
                margin-bottom: 10px;
                line-height: 1.3;
            }

            .job-recommendation {
                margin-top: 8px;
                color: #6b7280;
                font-size: 0.82rem;
                line-height: 1.35;
            }

            .pill {
                display: inline-block;
                padding: 4px 9px;
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 650;
                margin-right: 5px;
                margin-bottom: 5px;
            }

            .pill-score {
                background: #ecfdf5;
                color: #047857;
            }

            .pill-status {
                background: #eef2ff;
                color: #4338ca;
            }

            .pill-warning {
                background: #fff7ed;
                color: #c2410c;
            }

            .pill-muted {
                background: #f3f4f6;
                color: #4b5563;
            }
        </style>

        <div class="cards-wrapper">
        """
    ]

    for _, row in jobs.iterrows():
        job_id = str(row["job_id"])
        click_id = make_click_id(job_id)
        click_id_to_job_id[click_id] = job_id

        selected_class = "job-card-selected" if job_id == selected_job_id else ""

        title = safe_html(row.get("title", ""))
        company = safe_html(row.get("company", ""))
        location = safe_html(row.get("location", ""))
        score = safe_html(row.get("adjusted_score", ""))

        saved_status = row.get("status", "")
        status_label = safe_html(ACTION_LABELS.get(saved_status, saved_status))

        seniority = safe_html(row.get("seniority_level", ""))
        contract_fit = safe_html(row.get("contract_fit", ""))
        recommendation = safe_html(row.get("recommendation", ""))

        cards.append(
            f"""
            <a class="job-card-link" id="{click_id}" href="javascript:void(0);">
                <div class="job-card {selected_class}">
                    <div class="job-title">{title}</div>
                    <div class="job-company">{company} · {location}</div>

                    <span class="pill pill-score">Score {score}</span>
                    <span class="pill pill-status">{status_label}</span>
                    <span class="pill pill-warning">{seniority}</span>
                    <span class="pill pill-muted">{contract_fit}</span>

                    <div class="job-recommendation">
                        {recommendation}
                    </div>
                </div>
            </a>
            """
        )

    cards.append("</div>")

    return "\n".join(cards), click_id_to_job_id


def save_status_change(
    job_id: str,
    status: str,
    personal_notes: str,
) -> None:
    """
    Saves a status change in SQLite.
    """

    update_job_status(
        job_id=job_id,
        status=status,
        personal_notes=personal_notes,
    )


def main() -> None:
    st.set_page_config(
        page_title="AI Job Application Agent",
        page_icon="💼",
        layout="wide",
    )

    inject_custom_css()
    render_header()

    jobs = load_jobs_from_database()

    if "selected_job_id" not in st.session_state and not jobs.empty:
        st.session_state["selected_job_id"] = jobs.iloc[0]["job_id"]

    st.sidebar.header("Filtres")

    min_score = st.sidebar.slider(
        "Score ajusté minimum",
        min_value=0,
        max_value=int(max(jobs["adjusted_score"].max(), 100)),
        value=20,
        step=1,
    )

    status_filter = st.sidebar.multiselect(
        "Statut",
        options=STATUS_OPTIONS,
        default=["to_review", "interested"],
        format_func=lambda x: ACTION_LABELS.get(x, x),
    )

    seniority_values = sorted(jobs["seniority_level"].dropna().unique())
    seniority_filter = st.sidebar.multiselect(
        "Seniorité",
        options=seniority_values,
        default=[
            level for level in seniority_values
            if level != "too_senior"
        ],
    )

    contract_values = sorted(jobs["contract_fit"].dropna().unique())
    contract_filter = st.sidebar.multiselect(
        "Type de contrat détecté",
        options=contract_values,
        default=[
            contract for contract in contract_values
            if contract != "non_priority_contract"
        ],
    )

    search_text = st.sidebar.text_input(
        "Recherche texte",
        placeholder="ex: LLM, santé, Python, Airflow...",
    )

    max_cards = st.sidebar.slider(
        "Nombre d'offres affichées",
        min_value=10,
        max_value=100,
        value=30,
        step=10,
    )

    filtered_jobs = jobs[
        (jobs["adjusted_score"] >= min_score)
        & (jobs["status"].isin(status_filter))
        & (jobs["seniority_level"].isin(seniority_filter))
        & (jobs["contract_fit"].isin(contract_filter))
    ].copy()

    if search_text:
        search_text_lower = re.escape(search_text.lower())

        filtered_jobs = filtered_jobs[
            filtered_jobs["title"]
            .fillna("")
            .str.lower()
            .str.contains(search_text_lower, regex=True)
            | filtered_jobs["company"]
            .fillna("")
            .str.lower()
            .str.contains(search_text_lower, regex=True)
            | filtered_jobs["description"]
            .fillna("")
            .str.lower()
            .str.contains(search_text_lower, regex=True)
        ]

    filtered_jobs = filtered_jobs.sort_values(
        by="adjusted_score",
        ascending=False,
    )

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Offres affichées", len(filtered_jobs))
    col_b.metric("Offres totales", len(jobs))
    col_c.metric("Déjà postulé", int((jobs["status"] == "applied").sum()))
    col_d.metric("À garder", int((jobs["status"] == "interested").sum()))

    if filtered_jobs.empty:
        st.warning("Aucune offre ne correspond aux filtres.")
        return

    if st.session_state.get("selected_job_id") not in set(filtered_jobs["job_id"]):
        st.session_state["selected_job_id"] = filtered_jobs.iloc[0]["job_id"]

    left_col, right_col = st.columns([1, 2], gap="large")

    with left_col:
        st.markdown("### Offres")
        st.markdown(
            "<div class='small-help'>Clique sur une carte pour voir le détail.</div>",
            unsafe_allow_html=True,
        )
        st.write("")

        visible_jobs = filtered_jobs.head(max_cards).copy()

        cards_html, click_id_to_job_id = build_cards_html(
            visible_jobs,
            st.session_state["selected_job_id"],
        )

        offers_container = st.container(height=720)

        with offers_container:
            clicked_click_id = click_detector(
                cards_html,
                key="job_cards_click_detector_sqlite",
            )

        if clicked_click_id:
            clicked_job_id = click_id_to_job_id.get(clicked_click_id)

            if (
                clicked_job_id
                and clicked_job_id != st.session_state.get("selected_job_id")
            ):
                st.session_state["selected_job_id"] = clicked_job_id

    selected_job_df = filtered_jobs[
        filtered_jobs["job_id"] == st.session_state["selected_job_id"]
    ]

    if selected_job_df.empty:
        selected_job = filtered_jobs.iloc[0]
        st.session_state["selected_job_id"] = selected_job["job_id"]
    else:
        selected_job = selected_job_df.iloc[0]

    with right_col:
        title = safe_html(selected_job.get("title", ""))
        company = safe_html(selected_job.get("company", ""))
        location = safe_html(selected_job.get("location", ""))

        st.markdown(
            f"""
            <div class="detail-panel">
                <div class="detail-title">{title}</div>
                <div class="detail-subtitle">{company} · {location}</div>
                <span class="pill pill-score">
                    Score ajusté {safe_html(selected_job.get("adjusted_score", ""))}
                </span>
                <span class="pill pill-muted">
                    Score brut {safe_html(selected_job.get("score", ""))}
                </span>
                <span class="pill pill-warning">
                    {safe_html(selected_job.get("seniority_level", ""))}
                </span>
                <span class="pill pill-muted">
                    {safe_html(selected_job.get("contract_fit", ""))}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        info_col, action_col = st.columns([2, 1], gap="large")

        with info_col:
            st.write(f"📍 **Localisation :** {selected_job.get('location', '')}")
            st.write(f"🔗 **Source :** {selected_job.get('source', '')}")
            st.write(f"📅 **Trouvée par l'agent :** {selected_job.get('date_found', '')}")
            st.write(f"🕒 **Date de publication source :** {selected_job.get('date_posted', '')}")
            st.write(f"🎯 **Recommandation :** {selected_job.get('recommendation', '')}")
            st.write(f"➡️ **Action suivante :** {selected_job.get('next_action', '')}")
            source_url = selected_job.get("source_url", "")
            if isinstance(source_url, str) and source_url.strip():
                st.link_button("Ouvrir l'offre", source_url)

        with action_col:
            st.markdown("### Suivi")

            current_status = selected_job.get("status", "to_review")
            current_notes = selected_job.get("personal_notes", "")

            new_status = st.selectbox(
                "Statut",
                options=STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(current_status)
                if current_status in STATUS_OPTIONS
                else 0,
                format_func=lambda x: ACTION_LABELS.get(x, x),
            )

            personal_notes = st.text_area(
                "Notes perso",
                value=current_notes,
                placeholder=(
                    "Ex: à candidater demain, contacter recruteur, "
                    "pas assez ML..."
                ),
                height=120,
            )

            if st.button("Sauvegarder", type="primary"):
                save_status_change(
                    job_id=selected_job["job_id"],
                    status=new_status,
                    personal_notes=personal_notes,
                )
                st.success("Statut sauvegardé dans SQLite.")
                st.rerun()

        st.write("")

        quick_a, quick_b, quick_c, quick_d = st.columns(4)

        with quick_a:
            if st.button("⭐ Garder"):
                save_status_change(
                    selected_job["job_id"],
                    "interested",
                    selected_job.get("personal_notes", ""),
                )
                st.rerun()

        with quick_b:
            if st.button("✅ Postulé"):
                save_status_change(
                    selected_job["job_id"],
                    "applied",
                    selected_job.get("personal_notes", ""),
                )
                st.rerun()

        with quick_c:
            if st.button("❌ Refuser"):
                save_status_change(
                    selected_job["job_id"],
                    "rejected",
                    selected_job.get("personal_notes", ""),
                )
                st.rerun()

        with quick_d:
            if st.button("🗄️ Archiver"):
                save_status_change(
                    selected_job["job_id"],
                    "archived",
                    selected_job.get("personal_notes", ""),
                )
                st.rerun()

        tab_description, tab_analysis, tab_message = st.tabs(
            ["Description", "Analyse", "Message"]
        )

        with tab_description:
            st.markdown("### Description complète")
            st.write(selected_job.get("description", ""))

        with tab_analysis:
            st.markdown("### Pourquoi cette offre ressort ?")
            st.write(selected_job.get("explanation", ""))

            st.markdown("### Seniorité")
            st.write(selected_job.get("seniority_warning", ""))

            st.markdown("### Contrat")
            st.write(selected_job.get("contract_warning", ""))

            with st.expander("Détails techniques du scoring"):
                st.json(
                    {
                        "matched_keywords": selected_job.get("matched_keywords", ""),
                        "seniority_signals": selected_job.get(
                            "seniority_signals",
                            "",
                        ),
                        "contract_signals": selected_job.get(
                            "contract_signals",
                            "",
                        ),
                    }
                )

        with tab_message:
            st.markdown("### Message de candidature généré")

            message = selected_job.get("application_message", "")

            if isinstance(message, str) and message.strip():
                st.text_area(
                    "Message",
                    value=message,
                    height=350,
                )
            else:
                st.info(
                    "Aucun message généré pour cette offre dans SQLite."
                )


if __name__ == "__main__":
    main()