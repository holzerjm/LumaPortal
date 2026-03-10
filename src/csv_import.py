import csv
import io
from datetime import datetime

from src.models import Guest


# Known column name patterns for mapping custom Luma CSV fields
COMPANY_PATTERNS = [
    "what company do you work for",
    "which university",
    "company",
    "organization",
]
TITLE_PATTERNS = [
    "what is your job title",
    "job title",
    "title",
    "role",
]


def _find_column(headers: list[str], patterns: list[str]) -> str | None:
    """Find a CSV column matching any of the given patterns (case-insensitive)."""
    lower_headers = {h.lower().strip(): h for h in headers}
    for pattern in patterns:
        for lower_h, original_h in lower_headers.items():
            if pattern in lower_h:
                return original_h
    return None


def parse_csv(content: str) -> list[Guest]:
    """Parse a Luma CSV export into Guest objects."""
    reader = csv.DictReader(io.StringIO(content))
    headers = reader.fieldnames or []

    company_col = _find_column(headers, COMPANY_PATTERNS)
    title_col = _find_column(headers, TITLE_PATTERNS)

    guests = []
    for row in reader:
        api_id = row.get("api_id", "").strip()
        if not api_id:
            continue

        name = row.get("name", "").strip()
        first_name = row.get("first_name", "").strip()
        last_name = row.get("last_name", "").strip()

        # If name is empty but first/last exist, construct it
        if not name and (first_name or last_name):
            name = f"{first_name} {last_name}".strip()

        company = row.get(company_col, "").strip() if company_col else ""
        job_title = row.get(title_col, "").strip() if title_col else ""

        checked_in_at = None
        raw_checkin = row.get("checked_in_at", "").strip()
        if raw_checkin:
            try:
                checked_in_at = datetime.fromisoformat(raw_checkin)
            except ValueError:
                pass

        guests.append(
            Guest(
                api_id=api_id,
                name=name,
                first_name=first_name,
                last_name=last_name,
                email=row.get("email", "").strip(),
                phone=row.get("phone_number", "").strip(),
                company=company,
                job_title=job_title,
                ticket_type=row.get("ticket_name", "").strip(),
                approval_status=row.get("approval_status", "approved").strip(),
                checked_in_at=checked_in_at,
                data_source="csv",
            )
        )

    return guests


def parse_csv_file(path: str) -> list[Guest]:
    """Parse a CSV file from disk."""
    with open(path, "r", encoding="utf-8-sig") as f:
        return parse_csv(f.read())
