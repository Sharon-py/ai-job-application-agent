REQUIRED_JOB_COLUMNS = [
    "title",
    "company",
    "location",
    "contract_type",
    "source_url",
    "description",
    "date_found",
    "source",
    "status",
]

OPTIONAL_JOB_COLUMNS = [
    "notes",
]

VALID_STATUSES = [
    "to_review",
    "interested",
    "applied",
    "rejected",
    "archived",
]


def validate_job_offers_schema(df):
    """
    Checks that the job offers file has the expected columns.
    """

    missing_columns = [
        column for column in REQUIRED_JOB_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns in job offers file: "
            + ", ".join(missing_columns)
        )

    invalid_statuses = sorted(
        set(df["status"].dropna()) - set(VALID_STATUSES)
    )

    if invalid_statuses:
        raise ValueError(
            "Invalid status values found: "
            + ", ".join(invalid_statuses)
            + f". Valid statuses are: {', '.join(VALID_STATUSES)}"
        )

    return True