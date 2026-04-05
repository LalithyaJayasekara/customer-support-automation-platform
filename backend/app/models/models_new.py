from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    run_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    total_tickets = Column(Integer, nullable=False)
    high_priority = Column(Integer, nullable=False)
    approved = Column(Integer, nullable=False)
    needs_review = Column(Integer, nullable=False)
    new_count = Column(Integer, nullable=False)
    in_review_count = Column(Integer, nullable=False)
    resolved_count = Column(Integer, nullable=False)
    metrics_json = Column(JSON, nullable=False)


class TicketResult(Base):
    __tablename__ = "ticket_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("analysis_runs.run_id"), nullable=False)
    ticket_id = Column(String, nullable=False)
    original_text = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    urgency = Column(String, nullable=False)
    sentiment = Column(String, nullable=False)
    status = Column(String, nullable=False)
    assigned_team = Column(String, nullable=False)
    draft_reply = Column(Text, nullable=False)
    qa_status = Column(String, nullable=False)
    trace_json = Column(JSON, nullable=False)