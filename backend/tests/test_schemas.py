import pytest
from pydantic import ValidationError
from app.models.schemas import (
    TicketInput,
    AnalysisRequest,
    AnalysisResponse,
    AnalysisResult,
    UserCreate,
    LoginRequest,
)


class TestSchemaValidation:
    """Test Pydantic schema validation."""
    
    @pytest.mark.unit
    def test_ticket_input_valid(self):
        """Test valid ticket input."""
        ticket = TicketInput(
            ticket_id="T123",
            text="Customer message here"
        )
        
        assert ticket.ticket_id == "T123"
        assert ticket.text == "Customer message here"
    
    @pytest.mark.unit
    def test_ticket_input_missing_required_field(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError):
            TicketInput(ticket_id="T123")  # Missing text
    
    @pytest.mark.unit
    def test_ticket_input_empty_text(self):
        """Test that empty text raises validation error."""
        with pytest.raises(ValidationError):
            TicketInput(ticket_id="T123", text="")
    
    @pytest.mark.unit
    def test_analysis_request_valid(self):
        """Test valid analysis request."""
        request = AnalysisRequest(
            tickets=[
                TicketInput(ticket_id="T1", text="Issue 1"),
                TicketInput(ticket_id="T2", text="Issue 2")
            ]
        )
        
        assert len(request.tickets) == 2
        assert request.tickets[0].ticket_id == "T1"
    
    @pytest.mark.unit
    def test_analysis_request_empty_tickets(self):
        """Test that empty tickets list raises validation error."""
        with pytest.raises(ValidationError):
            AnalysisRequest(tickets=[])
    
    @pytest.mark.unit
    def test_user_create_valid(self):
        """Test valid user creation data."""
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            password="securepassword123"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
    
    @pytest.mark.unit
    def test_user_create_invalid_email(self):
        """Test that invalid email raises validation error."""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="not-an-email",
                password="securepassword123"
            )
    
    @pytest.mark.unit
    def test_user_create_short_password(self):
        """Test that short password raises validation error."""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="short"
            )
    
    @pytest.mark.unit
    def test_login_request_valid(self):
        """Test valid login request."""
        login = LoginRequest(
            username="testuser",
            password="securepassword123"
        )
        
        assert login.username == "testuser"
        assert login.password == "securepassword123"
    
    @pytest.mark.unit
    def test_analysis_result_valid(self):
        """Test that analysis result accepts valid data."""
        from app.models.schemas import TraceStep
        
        result = AnalysisResult(
            ticket_id="T1",
            text="Customer issue",
            category="general",
            urgency="medium",
            assigned_team="support_team",
            draft_reply="Thank you for contacting us",
            qa_status="approved",
            trace=[
                TraceStep(agent="classifier", message="Classified as general inquiry")
            ]
        )
        
        assert result.ticket_id == "T1"
        assert result.qa_status == "approved"
        assert len(result.trace) == 1
    
    @pytest.mark.unit
    def test_analysis_response_structure(self):
        """Test analysis response structure."""
        response = AnalysisResponse(
            run_id="run_123",
            timestamp="2024-01-01T00:00:00",
            user_id=1,
            results=[],
            metrics={
                "total_tickets": 0,
                "categorized": 0,
                "routed": 0,
                "generated_replies": 0,
                "approved": 0,
                "needs_review": 0,
                "processing_time_ms": 100.5
            }
        )
        
        assert response.run_id == "run_123"
        assert response.metrics["total_tickets"] == 0
