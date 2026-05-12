from urllib.parse import quote_plus
import webbrowser

import pandas as pd

from config import SEARCH_QUERIES_PATH, JOB_SEARCH_RESULTS_PATH, RESULTS_DIR


SEARCH_SOURCES = {
    "LinkedIn": "https://www.google.com/search?q=site%3Alinkedin.com%2Fjobs%2Fview+{query}",
    "Welcome to the Jungle": "https://www.google.com/search?q=site%3Awelcometothejungle.com%2Ffr%2Fcompanies+{query}",
    "Indeed": "https://www.google.com/search?q=site%3Afr.indeed.com+{query}",
    "APEC": "https://www.google.com/search?q=site%3Aapec.fr+{query}",
    "Company career pages": "https://www.google.com/search?q=site%3Aboards.greenhouse.io+OR+site%3Ajobs.lever.co+{query}",
}


def load_search_queries() -> pd.DataFrame:
    """
    Loads job search queries from CSV.
    """

    if not SEARCH_QUERIES_PATH.exists():
        raise FileNotFoundError(
            f"Search queries file not found: {SEARCH_QUERIES_PATH}\n"
            "Create data/raw/search_queries.csv first."
        )

    return pd.read_csv(SEARCH_QUERIES_PATH)


def build_search_url(source_name: str, query: str, location: str) -> str:
    """
    Builds a search URL for a given source.
    """

    full_query = f"{query} {location} CDI OR stage OR alternance OR full-time"
    encoded_query = quote_plus(full_query)

    template = SEARCH_SOURCES[source_name]

    return template.format(query=encoded_query)


def generate_search_results(queries: pd.DataFrame) -> list[dict]:
    """
    Generates search links for all queries and all sources.
    """

    results = []

    for _, row in queries.iterrows():
        query = row["query"]
        location = row["location"]
        priority = row.get("priority", "")
        notes = row.get("notes", "")

        for source_name in SEARCH_SOURCES:
            url = build_search_url(source_name, query, location)

            results.append(
                {
                    "query": query,
                    "location": location,
                    "priority": priority,
                    "notes": notes,
                    "source": source_name,
                    "url": url,
                }
            )

    return results


def save_results_to_markdown(results: list[dict]) -> None:
    """
    Saves generated search links to a readable Markdown file.
    """

    lines = []

    lines.append("# Job search links")
    lines.append("")
    lines.append("Generated search links based on the target job search profile.")
    lines.append("")

    current_query = None

    for item in results:
        query_label = f"{item['query']} — {item['location']}"

        if query_label != current_query:
            current_query = query_label
            lines.append(f"## {query_label}")
            lines.append("")
            lines.append(f"Priority: **{item['priority']}**")
            lines.append("")
            if item["notes"]:
                lines.append(f"Notes: {item['notes']}")
                lines.append("")

        lines.append(f"- [{item['source']}]({item['url']})")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    JOB_SEARCH_RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def open_high_priority_searches(results: list[dict]) -> None:
    """
    Opens only high-priority searches in the browser.
    """

    high_priority_results = [
        item for item in results
        if item["priority"] == "high"
    ]

    for item in high_priority_results:
        webbrowser.open_new_tab(item["url"])


def main(open_browser: bool = False):
    queries = load_search_queries()
    results = generate_search_results(queries)

    save_results_to_markdown(results)

    print("Job search links generated successfully.")
    print(f"Saved results to: {JOB_SEARCH_RESULTS_PATH}")
    print(f"Generated links: {len(results)}")

    if open_browser:
        open_high_priority_searches(results)
        print("High-priority searches opened in browser.")


if __name__ == "__main__":
    main(open_browser=False)