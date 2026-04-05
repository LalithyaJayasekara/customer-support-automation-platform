import pytest
from app.models.schemas import TicketInput
from app.services.pipeline import run_ticket_pipeline


class TestTicketPipeline:
    """Test the complete ticket analysis pipeline."""
    
    @pytest.mark.unit
    def test_pipeline_returns_result(self) -> None:
        """Test that pipeline returns a result for valid input."""
        ticket = TicketInput(ticket_id="T100", text="I cannot login and this is urgent")
        result = run_ticket_pipeline(ticket)

        assert result.ticket_id == "T100"
        assert result.category in {"login", "general", "billing", "bug", "refund"}
        assert result.assigned_team in {"billing_team", "tech_team", "account_team", "support_team"}
        assert result.draft_reply
        assert result.qa_status in {"approved", "needs_review"}
    
    @pytest.mark.unit
    def test_pipeline_billing_issue(self) -> None:
        """Test pipeline with billing issue."""
        ticket = TicketInput(
            ticket_id="T101",
            text="I was charged twice for my subscription. Please refund me immediately."
        )
        result = run_ticket_pipeline(ticket)

        assert result.ticket_id == "T101"
        assert result.category in {"billing", "refund"}
        assert result.assigned_team == "billing_team"
        assert result.draft_reply
    
    @pytest.mark.unit
    def test_pipeline_generic_issue(self) -> None:
        """Test pipeline with generic inquiry."""
        ticket = TicketInput(
            ticket_id="T102",
            text="What are your business hours?"
        )
        result = run_ticket_pipeline(ticket)

        assert result.ticket_id == "T102"
        assert result.category in {"general", "login", "billing", "bug", "refund"}
        assert result.assigned_team
        assert result.draft_reply
    
    @pytest.mark.unit
    def test_pipeline_high_urgency(self) -> None:
        """Test pipeline correctly identifies high urgency."""
        urgent_tickets = [
            "URGENT: My account is locked and I cannot access my data!",
            "CRITICAL: Payment processing is failing!",
            "EMERGENCY: App is crashing for all users!"
        ]
        
        for text in urgent_tickets:
            ticket = TicketInput(ticket_id="T_URGENT", text=text)
            result = run_ticket_pipeline(ticket)
            
            assert result.urgency in {"high", "medium", "low"}
            assert result.draft_reply
    
    @pytest.mark.unit
    def test_pipeline_qa_validation(self) -> None:
        """Test that QA agent validates responses."""
        ticket = TicketInput(
            ticket_id="T103",
            text="I cannot login to my account"
        )
        result = run_ticket_pipeline(ticket)

        assert result.qa_status in {"approved", "needs_review"}
        # All responses should be human-readable
        assert len(result.draft_reply) > 10
    
    @pytest.mark.unit
    def test_pipeline_trace_information(self) -> None:
        """Test that pipeline includes trace information."""
        ticket = TicketInput(ticket_id="T104", text="Help!")
        result = run_ticket_pipeline(ticket)

        assert result.trace is not None
        assert len(result.trace) > 0
        # Trace should include information from agents
        agent_names = [step.agent for step in result.trace]
        assert len(agent_names) > 0
