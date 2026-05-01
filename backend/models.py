from pydantic import BaseModel
from typing import Optional

class ApplicationCreate(BaseModel):
    company: str
    role: str
    status: str = "applied"
    date_applied: Optional[str] = None
    source: str = "manual"
    fit_score: Optional[int] = None
    notes: Optional[str] = None
    next_action: Optional[str] = None

class ApplicationUpdate(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    next_action: Optional[str] = None
    fit_score: Optional[int] = None

class ApplicationResponse(BaseModel):
    id: int
    company: str
    role: str
    status: str
    date_applied: Optional[str]
    source: Optional[str]
    fit_score: Optional[int]
    notes: Optional[str]
    next_action: Optional[str]
    last_activity: Optional[str]
    created_at: str

class QueueItemResponse(BaseModel):
    id: int
    email_id: int
    suggested_type: Optional[str]
    suggested_company: Optional[str]
    suggested_role: Optional[str]
    confidence_score: Optional[float]
    reasoning: Optional[str]
    status: str
    created_at: str
    sender_name: Optional[str]
    sender_email: Optional[str]
    subject: Optional[str]
    body_snippet: Optional[str]

class QueueResolve(BaseModel):
    action: str  # "confirm", "correct", "reject"
    corrected_type: Optional[str] = None
    corrected_company: Optional[str] = None
    corrected_role: Optional[str] = None

class DashboardStats(BaseModel):
    total_active: int
    total_applied: int
    total_screening: int
    total_interview: int
    total_offer: int
    total_rejected: int
    total_archived: int
    response_rate: float  # percentage of applications that got any response
    avg_days_to_response: Optional[float]
    pending_review: int
    weekly_trend: list  # list of { week: "2025-W01", applied: N, responses: N }

class CoverLetterRequest(BaseModel):
    job_description: str
    company: str
    role: str
    application_id: Optional[int] = None

class CoverLetterResponse(BaseModel):
    cover_letter: str
    key_matches: list[str]  # bullet points of strongest resume-to-JD matches
    gaps: list[str]         # skills in JD not strongly represented in resume
