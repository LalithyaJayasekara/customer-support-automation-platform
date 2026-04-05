import os
import json
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import AnalysisRun, TicketResult
from app.models.schemas import (
    HistoryRunDetail,
    HistoryRunSummary,
    HistoryTicketRecord,
    TicketInput,
    TicketResult as TicketResultSchema,
)
from app.logging_config import logger


def init_db() -> None:
    """Initialize database tables"""
    from app.database import engine, Base
    # Import all models to ensure they're registered with SQLAlchemy
    from app.models import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")


def get_db() -> Session:
    """Get database session"""
    return SessionLocal()


def save_analysis_run(tickets: List[TicketInput], results: List[TicketResultSchema], metrics: dict) -> int:
    """Save analysis run and ticket results to database"""
    ticket_text_map = {ticket.ticket_id: ticket.text for ticket in tickets}

    db = get_db()
    try:
        # Create analysis run
        db_run = AnalysisRun(
            total_tickets=metrics.get("total_tickets", 0),
            high_priority=metrics.get("high_priority", 0),
            approved=metrics.get("approved", 0),
            needs_review=metrics.get("needs_review", 0),
            new_count=metrics.get("new", 0),
            in_review_count=metrics.get("in_review", 0),
            resolved_count=metrics.get("resolved", 0),
            metrics_json=metrics,
        )
        db.add(db_run)
        db.flush()  # Get run_id
        run_id = db_run.run_id

        # Create ticket results
        for result in results:
            db_ticket = TicketResult(
                run_id=run_id,
                ticket_id=result.ticket_id,
                original_text=ticket_text_map.get(result.ticket_id, ""),
                category=result.category,
                urgency=result.urgency,
                sentiment=result.sentiment,
                status=result.status,
                assigned_team=result.assigned_team,
                draft_reply=result.draft_reply,
                qa_status=result.qa_status,
                trace_json=[step.model_dump() for step in result.trace],
            )
            db.add(db_ticket)

        db.commit()
        logger.info("Analysis run saved", run_id=run_id, ticket_count=len(results))
        return run_id

    except Exception as e:
        db.rollback()
        logger.error("Failed to save analysis run", error=str(e))
        raise
    finally:
        db.close()


def list_history_runs(limit: int = 20) -> List[HistoryRunSummary]:
    """List recent analysis runs"""
    db = get_db()
    try:
        runs = db.query(AnalysisRun).order_by(AnalysisRun.run_id.desc()).limit(limit).all()

        return [
            HistoryRunSummary(
                run_id=run.run_id,
                created_at=run.created_at.isoformat(),
                total_tickets=run.total_tickets,
                high_priority=run.high_priority,
                approved=run.approved,
                needs_review=run.needs_review,
            )
            for run in runs
        ]
    finally:
        db.close()


def get_history_run_detail(run_id: int) -> Optional[HistoryRunDetail]:
    """Get detailed analysis run data"""
    db = get_db()
    try:
        run = db.query(AnalysisRun).filter(AnalysisRun.run_id == run_id).first()
        if not run:
            return None

        tickets = db.query(TicketResult).filter(TicketResult.run_id == run_id).order_by(TicketResult.id).all()

        ticket_records = [
            HistoryTicketRecord(
                ticket_id=ticket.ticket_id,
                original_text=ticket.original_text,
                category=ticket.category,
                urgency=ticket.urgency,
                sentiment=ticket.sentiment,
                status=ticket.status,
                assigned_team=ticket.assigned_team,
                draft_reply=ticket.draft_reply,
                qa_status=ticket.qa_status,
            )
            for ticket in tickets
        ]

        return HistoryRunDetail(
            run_id=run.run_id,
            created_at=run.created_at.isoformat(),
            metrics=run.metrics_json,
            tickets=ticket_records,
        )
    finally:
        db.close()


def delete_history_run(run_id: int) -> bool:
    """Delete analysis run and associated tickets"""
    db = get_db()
    try:
        run = db.query(AnalysisRun).filter(AnalysisRun.run_id == run_id).first()
        if not run:
            return False

        # Delete associated tickets first (due to foreign key)
        db.query(TicketResult).filter(TicketResult.run_id == run_id).delete()

        # Delete the run
        db.delete(run)
        db.commit()

        logger.info("Analysis run deleted", run_id=run_id)
        return True

    except Exception as e:
        db.rollback()
        logger.error("Failed to delete analysis run", run_id=run_id, error=str(e))
        return False
    finally:
        db.close()


def get_analytics_overview(limit_runs: int = 200) -> dict:
    """Get analytics overview from recent runs"""
    db = get_db()
    try:
        # Get recent runs for aggregation
        recent_runs = db.query(AnalysisRun).order_by(AnalysisRun.run_id.desc()).limit(limit_runs).all()

        if not recent_runs:
            return {
                "total_runs": 0,
                "total_tickets": 0,
                "high_priority": 0,
                "approved": 0,
                "needs_review": 0,
                "new_count": 0,
                "in_review_count": 0,
                "resolved_count": 0,
            }

        # Aggregate metrics
        total_runs = len(recent_runs)
        total_tickets = sum(run.total_tickets for run in recent_runs)
        high_priority = sum(run.high_priority for run in recent_runs)
        approved = sum(run.approved for run in recent_runs)
        needs_review = sum(run.needs_review for run in recent_runs)
        new_count = sum(run.new_count for run in recent_runs)
        in_review_count = sum(run.in_review_count for run in recent_runs)
        resolved_count = sum(run.resolved_count for run in recent_runs)

        return {
            "total_runs": total_runs,
            "total_tickets": total_tickets,
            "high_priority": high_priority,
            "approved": approved,
            "needs_review": needs_review,
            "new_count": new_count,
            "in_review_count": in_review_count,
            "resolved_count": resolved_count,
        }

    finally:
        db.close()


def list_analytics_runs(limit: int = 100) -> List[dict]:
    """List runs for analytics"""
    db = get_db()
    try:
        runs = db.query(AnalysisRun).order_by(AnalysisRun.run_id.desc()).limit(limit).all()

        return [
            {
                "run_id": run.run_id,
                "created_at": run.created_at.isoformat(),
                "total_tickets": run.total_tickets,
                "high_priority": run.high_priority,
                "approved": run.approved,
                "needs_review": run.needs_review,
                "metrics": run.metrics_json,
            }
            for run in runs
        ]
    finally:
        db.close()


def list_analytics_tickets(limit: int = 1000) -> List[dict]:
    """List tickets for analytics"""
    db = get_db()
    try:
        tickets = db.query(TicketResult).order_by(TicketResult.id.desc()).limit(limit).all()

        return [
            {
                "id": ticket.id,
                "run_id": ticket.run_id,
                "ticket_id": ticket.ticket_id,
                "category": ticket.category,
                "urgency": ticket.urgency,
                "sentiment": ticket.sentiment,
                "status": ticket.status,
                "assigned_team": ticket.assigned_team,
                "qa_status": ticket.qa_status,
            }
            for ticket in tickets
        ]
    finally:
        db.close()