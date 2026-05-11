# AI Job Application Agent

This project is a first version of an AI-assisted job application agent.

The goal is to help a candidate organize a job search by analyzing job offers, ranking them according to a personalized profile, and generating tailored application messages.

## Project idea

Searching for a job often involves reading many job descriptions, comparing them manually, and deciding which ones are worth applying to first.

This project proposes a simple decision-support pipeline that:

1. loads job offers from a CSV file,
2. scores each offer according to a target profile,
3. explains why an offer is relevant,
4. recommends the next action,
5. generates a first personalized application message,
6. exports the results in CSV and Markdown format.

## Current version

The current version is a rule-based prototype.

It does not yet search job offers automatically online and does not yet use a Large Language Model for generation.

Instead, it focuses on building a clean and understandable first pipeline.

The scoring is based on several categories:

- core data science and machine learning,
- generative AI, LLM and NLP,
- data engineering and production,
- health, biomedical and research bonus,
- finance and risk,
- reporting and dashboarding.

The goal is not to target only medical or research jobs.

The priority is to identify realistic Data Scientist / ML / AI opportunities, while giving a bonus to health, biomedical or research-related positions.

## Project structure

```text
ai-job-application-agent/
│
├── data/
│   ├── raw/
│   │   └── job_offers.csv
│   ├── processed/
│   │   └── scored_job_offers.csv
│   ├── interim/
│   └── external/
│
├── results/
│   ├── application_messages.csv
│   └── application_messages.md
│
├── src/
│   ├── config.py
│   ├── data.py
│   ├── scoring.py
│   └── application_message.py
│
├── README.md
├── requirements.txt
└── .gitignore
```

## How it works

### 1. Input job offers

Job offers are stored in:

```text
data/raw/job_offers.csv
```

Example format:

```csv
title,company,location,contract_type,source_url,description
LLM Data Scientist,Gorgias,Paris,CDI,https://example.com,"LLM, NLP, Python, AI agents, ecommerce, machine learning"
```

### 2. Score job offers

Run:

```bash
python src/data.py
```

This creates:

```text
data/processed/scored_job_offers.csv
```

Each offer receives:

- a global score,
- a recommendation level,
- a fit type,
- a suggested next action,
- an explanation of the match.

### 3. Generate application messages

Run:

```bash
python src/application_message.py
```

This creates:

```text
results/application_messages.csv
results/application_messages.md
```

The Markdown file is easier to read and contains one section per selected job offer.

## Example output

For a job offer such as:

```text
LLM Data Scientist — Gorgias
```

The system can identify a strong match with:

- Python,
- machine learning,
- NLP,
- LLM,
- AI agents.

It then recommends applying quickly and generates a first personalized application message.

## Current limitations

This version is intentionally simple.

Current limitations:

- job offers are entered manually in a CSV file,
- scoring is based on keywords and weights,
- the application message is generated with templates,
- no automatic job scraping is implemented yet,
- no LLM API is used yet.

## Next improvements

Planned improvements:

- load real job offers from APIs or job boards,
- improve the scoring with semantic similarity,
- add a real LLM to generate more natural application messages,
- include the candidate CV as structured input,
- add a Streamlit interface,
- export a full job search dashboard.

## Tech stack

- Python
- pandas
- Markdown export
- CSV processing
- rule-based scoring

## How to run the project

Clone the repository:

```bash
git clone https://github.com/Sharon-py/ai-job-application-agent.git
cd ai-job-application-agent
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows with Git Bash:

```bash
source .venv/Scripts/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the scoring pipeline:

```bash
python src/data.py
```

Generate application messages:

```bash
python src/application_message.py
```

## Notes

This project is a learning-oriented prototype.

The first goal is to build a clean and understandable pipeline before adding more advanced agentic features.

Future versions may include automatic job search, semantic matching, LLM-based message generation, and a user interface.