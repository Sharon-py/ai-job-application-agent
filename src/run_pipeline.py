from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


PIPELINE_STEPS = [
    {
        "name": "Collecte des offres",
        "command": ["src/job_collector.py"],
    },
    {
        "name": "Scoring des offres",
        "command": ["src/data.py"],
    },
    {
        "name": "Génération des messages",
        "command": ["src/application_message.py"],
    },
    {
        "name": "Synchronisation avec la base",
        "command": ["src/import_existing_data.py"],
    },
]


def log(message: str) -> None:
    """
    Prints a timestamped message.
    """

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}", flush=True)


def run_step(step_name: str, command: list[str]) -> None:
    """
    Runs one pipeline step.
    """

    full_command = [sys.executable, *command]

    log("")
    log("=" * 80)
    log(f"Starting step: {step_name}")
    log(f"Command: {' '.join(full_command)}")
    log("=" * 80)

    subprocess.run(
        full_command,
        cwd=PROJECT_ROOT,
        check=True,
    )

    log(f"Step completed: {step_name}")


def run_pipeline() -> None:
    """
    Runs the full job search pipeline once.
    """

    start_time = datetime.now()

    log("=" * 80)
    log("Starting full AI job application pipeline")
    log("=" * 80)

    try:
        for step in PIPELINE_STEPS:
            run_step(
                step_name=step["name"],
                command=step["command"],
            )

    except subprocess.CalledProcessError as error:
        log("")
        log("Pipeline failed.")
        log(f"Failed command: {error.cmd}")
        log(f"Return code: {error.returncode}")
        sys.exit(error.returncode)

    duration = datetime.now() - start_time

    log("")
    log("=" * 80)
    log("Pipeline completed successfully")
    log(f"Total duration: {duration}")
    log("=" * 80)


if __name__ == "__main__":
    run_pipeline()