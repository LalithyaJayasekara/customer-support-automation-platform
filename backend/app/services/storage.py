import json
import sqlite3
from pathlib import Path

from app.models.schemas import (
    HistoryRunDetail,
    HistoryRunSummary,
    HistoryTicketRecord,
    TicketInput,
    TicketResult,
)

DB_PATH = Path(__file__).resolve().parents[2] / "support_assistant.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                total_tickets INTEGER NOT NULL,
                high_priority INTEGER NOT NULL,
                approved INTEGER NOT NULL,
                needs_review INTEGER NOT NULL,
                new_count INTEGER NOT NULL,
                in_review_count INTEGER NOT NULL,
                resolved_count INTEGER NOT NULL,
                metrics_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                ticket_id TEXT NOT NULL,
                original_text TEXT NOT NULL,
                category TEXT NOT NULL,
                urgency TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                status TEXT NOT NULL,
                assigned_team TEXT NOT NULL,
                draft_reply TEXT NOT NULL,
                qa_status TEXT NOT NULL,
                trace_json TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs (run_id)
            )
            """
        )
        conn.commit()


def save_analysis_run(tickets: list[TicketInput], results: list[TicketResult], metrics: dict) -> int:
    ticket_text_map = {ticket.ticket_id: ticket.text for ticket in tickets}

    with _get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO analysis_runs (
                total_tickets,
                high_priority,
                approved,
                needs_review,
                new_count,
                in_review_count,
                resolved_count,
                metrics_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metrics.get("total_tickets", 0),
                metrics.get("high_priority", 0),
                metrics.get("approved", 0),
                metrics.get("needs_review", 0),
                metrics.get("new", 0),
                metrics.get("in_review", 0),
                metrics.get("resolved", 0),
                json.dumps(metrics),
            ),
        )
        run_id = int(cursor.lastrowid)

        for result in results:
            conn.execute(
                """
                INSERT INTO ticket_results (
                    run_id,
                    ticket_id,
                    original_text,
                    category,
                    urgency,
                    sentiment,
                    status,
                    assigned_team,
                    draft_reply,
                    qa_status,
                    trace_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    result.ticket_id,
                    ticket_text_map.get(result.ticket_id, ""),
                    result.category,
                    result.urgency,
                    result.sentiment,
                    result.status,
                    result.assigned_team,
                    result.draft_reply,
                    result.qa_status,
                    json.dumps([step.model_dump() for step in result.trace]),
                ),
            )

        conn.commit()
        return run_id


def list_history_runs(limit: int = 20) -> list[HistoryRunSummary]:
    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                run_id,
                created_at,
                total_tickets,
                high_priority,
                approved,
                needs_review
            FROM analysis_runs
            ORDER BY run_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        HistoryRunSummary(
            run_id=row["run_id"],
            created_at=row["created_at"],
            total_tickets=row["total_tickets"],
            high_priority=row["high_priority"],
            approved=row["approved"],
            needs_review=row["needs_review"],
        )
        for row in rows
    ]


def get_history_run_detail(run_id: int) -> HistoryRunDetail | None:
    with _get_connection() as conn:
        run_row = conn.execute(
            """
            SELECT run_id, created_at, metrics_json
            FROM analysis_runs
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

        if not run_row:
            return None

        ticket_rows = conn.execute(
            """
            SELECT
                ticket_id,
                original_text,
                category,
                urgency,
                sentiment,
                status,
                assigned_team,
                draft_reply,
                qa_status
            FROM ticket_results
            WHERE run_id = ?
            ORDER BY id ASC
            """,
            (run_id,),
        ).fetchall()

    tickets = [
        HistoryTicketRecord(
            ticket_id=row["ticket_id"],
            original_text=row["original_text"],
            category=row["category"],
            urgency=row["urgency"],
            sentiment=row["sentiment"],
            status=row["status"],
            assigned_team=row["assigned_team"],
            draft_reply=row["draft_reply"],
            qa_status=row["qa_status"],
        )
        for row in ticket_rows
    ]

    return HistoryRunDetail(
        run_id=run_row["run_id"],
        created_at=run_row["created_at"],
        metrics=json.loads(run_row["metrics_json"]),
        tickets=tickets,
    )


def delete_history_run(run_id: int) -> bool:
    with _get_connection() as conn:
        run_exists = conn.execute(
            "SELECT 1 FROM analysis_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        if not run_exists:
            return False

        conn.execute("DELETE FROM ticket_results WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM analysis_runs WHERE run_id = ?", (run_id,))
        conn.commit()
        return True
