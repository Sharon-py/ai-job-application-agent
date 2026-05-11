# Data Science Project Template

## Overview

This repository is a reusable template for data science projects.

It provides a clean structure for organizing data, notebooks, source code, models, results, and reports.

## Project Structure

```text
.
├── data/
│   ├── raw/          # Original data, not modified
│   ├── interim/      # Intermediate data
│   ├── processed/    # Clean data used for modeling
│   └── external/     # External data or metadata
│
├── notebooks/        # Jupyter notebooks
├── src/              # Reusable Python code
├── models/           # Saved models
├── results/          # Metrics, predictions, outputs
├── reports/
│   ├── figures/      # Generated figures
│   └── tables/       # Generated tables
│
├── tests/            # Unit tests
├── requirements.txt
├── config.yaml
└── README.md
```

## How to use this template for a new project

This repository is meant to be reused as a starting point for new data science projects.

### 1. Create a new repository from the template on GitHub

On GitHub:

1. Open this template repository.
2. Click on **Use this template**.
3. Select **Create a new repository**.
4. Choose a new repository name, for example:

```text
my-new-data-science-project
```

5. Create the repository.

This will create a new GitHub repository with the same structure as this template.

### 2. Clone the new repository locally

Open VS Code, then open a terminal and go to the folder where you store your projects.

Example:

```bash
cd /c/code
```

Then clone the new repository:

```bash
git clone https://github.com/Sharon-py/my-new-data-science-project.git
```

Move into the project folder:

```bash
cd my-new-data-science-project
```

Open the project in VS Code:

```bash
code .
```

### 3. Create a virtual environment

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows with Git Bash:

```bash
source .venv/Scripts/activate
```

Or with PowerShell:

```powershell
.venv\Scripts\activate
```

### 4. Install dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

If new packages are installed during the project, update `requirements.txt`:

```bash
pip freeze > requirements.txt
```

### 5. Save changes with Git

Check modified files:

```bash
git status
```

Add changes:

```bash
git add .
```

Commit changes:

```bash
git commit -m "Initial project setup"
```

Push to GitHub:

```bash
git push
```

## Typical Workflow

The usual workflow is:

1. Load the raw data
2. Explore and understand the dataset
3. Clean and preprocess the data
4. Build features
5. Train models
6. Evaluate the results
7. Interpret the model and document the conclusions

## Notes

The folders `data/`, `models/`, `results/`, and generated report outputs are ignored by Git by default.

This avoids pushing large files, sensitive datasets, trained models, or temporary outputs to GitHub.

Only the empty folder structure is kept using `.gitkeep` files.

## Author

Sharon