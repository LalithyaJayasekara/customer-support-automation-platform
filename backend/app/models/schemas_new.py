from pydantic import BaseModel, EmailStr
from typing import Optional, List, Literal
from datetime import datetime
from pydantic import Field


# User Authentication Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    username: Optional[str] = None


# Ticket Analysis Schemas
Category = Literal["billing", "login", "bug", "refund", "general"]
Urgency = Literal["high", "medium", "low"]
Team = Literal["billing_team", "tech_team", "account_team", "support_team"]
QAStatus = Literal["approved", "needs_review"]
TicketStatus = Literal["new", "in_review", "resolved"]


class TicketInput(BaseModel):
    ticket_id: str = Field(..., description="Unique ticket ID")
    text: str = Field(..., min_length=5, description="Raw support ticket text")


class TraceStep(BaseModel):
    agent: str
    output: dict


class TicketResult(BaseModel):
    ticket_id: str
    category: Category
    urgency: Urgency
    sentiment: Literal["angry", "neutral", "positive"]
    status: TicketStatus
    assigned_team: Team
    draft_reply: str
    qa_status: QAStatus
    trace: list[TraceStep]


class AnalyzeRequest(BaseModel):
    tickets: list[TicketInput]


class AnalyzeResponse(BaseModel):
    run_id: int
    results: list[TicketResult]
    metrics: dict


class HistoryRunSummary(BaseModel):
    run_id: int
    created_at: str
    total_tickets: int
    high_priority: int
    approved: int
    needs_review: int


class HistoryRunDetail(BaseModel):
    run_id: int
    created_at: str
    metrics: dict
    tickets: list


class HistoryTicketRecord(BaseModel):
    ticket_id: str
    original_text: str
    category: str
    urgency: str
    sentiment: str
    status: str
    assigned_team: str
    draft_reply: str
    qa_status: str


class AnalyticsOverview(BaseModel):
    total_runs: int
    total_tickets: int
    high_priority: int
    approved: int
    needs_review: int
    new_count: int
    in_review_count: int
    resolved_count: int


class AnalyticsRunRecord(BaseModel):
    run_id: int
    created_at: str
    total_tickets: int
    high_priority: int
    approved: int
    needs_review: int
    metrics: dict


class AnalyticsTicketRecord(BaseModel):
    id: int
    run_id: int
    ticket_id: str
    category: str
    urgency: str
    sentiment: str
    status: str
    assigned_team: str
    qa_status: str