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


def get_analytics_overview(limit_runs: int = 200) -> dict:
    with _get_connection() as conn:
        row = conn.execute(
            """
            WITH latest_runs AS (
                SELECT *
                FROM analysis_runs
                ORDER BY run_id DESC
                LIMIT ?
            )
            SELECT
                COUNT(*) AS total_runs,
                COALESCE(SUM(total_tickets), 0) AS total_tickets,
                COALESCE(SUM(high_priority), 0) AS high_priority,
                COALESCE(SUM(approved), 0) AS approved,
                COALESCE(SUM(needs_review), 0) AS needs_review,
                COALESCE(SUM(new_count), 0) AS new_count,
                COALESCE(SUM(in_review_count), 0) AS in_review_count,
                COALESCE(SUM(resolved_count), 0) AS resolved_count
            FROM latest_runs
            """,
            (limit_runs,),
        ).fetchone()

    total_tickets = int(row["total_tickets"])
    high_priority = int(row["high_priority"])
    approved = int(row["approved"])
    needs_review = int(row["needs_review"])

    return {
        "total_runs": int(row["total_runs"]),
        "total_tickets": total_tickets,
        "high_priority": high_priority,
        "approved": approved,
        "needs_review": needs_review,
        "new_count": int(row["new_count"]),
        "in_review_count": int(row["in_review_count"]),
        "resolved_count": int(row["resolved_count"]),
        "high_priority_rate": (high_priority / total_tickets) if total_tickets else 0.0,
        "approval_rate": (approved / total_tickets) if total_tickets else 0.0,
        "needs_review_rate": (needs_review / total_tickets) if total_tickets else 0.0,
    }


def list_analytics_runs(limit: int = 200) -> list[dict]:
    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                run_id,
                created_at,
                total_tickets,
                high_priority,
                approved,
                needs_review,
                new_count,
                in_review_count,
                resolved_count
            FROM analysis_runs
            ORDER BY run_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    output: list[dict] = []
    for row in rows:
        total_tickets = int(row["total_tickets"])
        high_priority = int(row["high_priority"])
        approved = int(row["approved"])
        needs_review = int(row["needs_review"])

        output.append(
            {
                "run_id": int(row["run_id"]),
                "created_at": row["created_at"],
                "total_tickets": total_tickets,
                "high_priority": high_priority,
                "approved": approved,
                "needs_review": needs_review,
                "new_count": int(row["new_count"]),
                "in_review_count": int(row["in_review_count"]),
                "resolved_count": int(row["resolved_count"]),
                "high_priority_rate": (high_priority / total_tickets) if total_tickets else 0.0,
                "approval_rate": (approved / total_tickets) if total_tickets else 0.0,
                "needs_review_rate": (needs_review / total_tickets) if total_tickets else 0.0,
            }
        )

    return output


def list_analytics_tickets(limit: int = 5000, run_id: int | None = None) -> list[dict]:
    where_clause = ""
    params: tuple[int, ...]

    if run_id is None:
        params = (limit,)
    else:
        where_clause = "WHERE tr.run_id = ?"
        params = (run_id, limit)

    with _get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT
                tr.run_id,
                ar.created_at AS run_created_at,
                tr.ticket_id,
                tr.original_text,
                tr.category,
                tr.urgency,
                tr.sentiment,
                tr.status,
                tr.assigned_team,
                tr.qa_status
            FROM ticket_results tr
            JOIN analysis_runs ar ON ar.run_id = tr.run_id
            {where_clause}
            ORDER BY tr.id DESC
            LIMIT ?
            """,
            params,
        ).fetchall()

    output: list[dict] = []
    for row in rows:
        urgency = row["urgency"]
        qa_status = row["qa_status"]
        output.append(
            {
                "run_id": int(row["run_id"]),
                "run_created_at": row["run_created_at"],
                "ticket_id": row["ticket_id"],
                "original_text": row["original_text"],
                "category": row["category"],
                "urgency": urgency,
                "sentiment": row["sentiment"],
                "status": row["status"],
                "assigned_team": row["assigned_team"],
                "qa_status": qa_status,
                "is_high_priority": 1 if urgency == "high" else 0,
                "is_approved": 1 if qa_status == "approved" else 0,
                "is_needs_review": 1 if qa_status == "needs_review" else 0,
            }
        )

    return output
