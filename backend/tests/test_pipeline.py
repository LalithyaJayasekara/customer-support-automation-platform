from app.models.schemas import TicketInput
from app.services.pipeline import run_ticket_pipeline


def test_pipeline_returns_result() -> None:
    ticket = TicketInput(ticket_id="T100", text="I cannot login and this is urgent")
    result = run_ticket_pipeline(ticket)

    assert result.ticket_id == "T100"
    assert result.category in {"login", "general", "billing", "bug", "refund"}
    assert result.assigned_team in {"billing_team", "tech_team", "account_team", "support_team"}
    assert result.draft_reply
    assert result.qa_status in {"approved", "needs_review"}
