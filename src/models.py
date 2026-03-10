from pydantic import BaseModel
from datetime import datetime


class Guest(BaseModel):
    id: int | None = None
    api_id: str
    name: str
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""
    job_title: str = ""
    ticket_type: str = ""
    approval_status: str = "approved"
    checked_in_at: datetime | None = None
    checked_in_by: str | None = None
    badge_printed_at: datetime | None = None
    data_source: str = "csv"
    created_at: datetime | None = None


class SearchResult(BaseModel):
    api_id: str
    name: str
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    job_title: str = ""
    match_score: float = 0.0
    already_checked_in: bool = False
    checked_in_at: datetime | None = None


class CheckInRequest(BaseModel):
    api_id: str


class CheckInResponse(BaseModel):
    status: str  # "success", "duplicate", "not_found", "error"
    name: str = ""
    message: str = ""
    checked_in_at: datetime | None = None


class StatsResponse(BaseModel):
    total_guests: int = 0
    checked_in: int = 0
    remaining: int = 0
    event_name: str = ""
