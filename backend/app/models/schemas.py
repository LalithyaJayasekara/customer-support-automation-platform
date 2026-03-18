from typing import Literal
from pydantic import BaseModel, Field


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
    results: list[TicketResult]
    metrics: dict


class HistoryRunSummary(BaseModel):
    run_id: int
    created_at: str
    total_tickets: int
    high_priority: int
    approved: int
    needs_review: int


class HistoryTicketRecord(BaseModel):
    ticket_id: str
    original_text: str
    category: Category
    urgency: Urgency
    sentiment: Literal["angry", "neutral", "positive"]
    status: TicketStatus
    assigned_team: Team
    draft_reply: str
    qa_status: QAStatus


class HistoryRunDetail(BaseModel):
    run_id: int
    created_at: str
    metrics: dict
    tickets: list[HistoryTicketRecord]
