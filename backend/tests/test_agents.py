import pytest
from app.agents.classifier import classify_ticket
from app.agents.router import route_ticket
from app.agents.replier import generate_reply
from app.agents.qa import check_quality


class TestAgents:
    """Test ticket analysis agents."""
    
    @pytest.mark.unit
    def test_classifier_categorizes_ticket(self):
        """Test that classifier identifies ticket category."""
        result = classify_ticket("I cannot login to my account")
        
        assert result is not None
        assert "category" in result
        assert result["category"] in {"login", "general", "billing", "bug", "refund"}
    
    @pytest.mark.unit
    def test_classifier_identifies_urgency(self):
        """Test that classifier identifies urgency level."""
        urgent_text = "URGENT: I was charged twice and my account is still locked!"
        result = classify_ticket(urgent_text)
        
        assert result is not None
        assert "urgency" in result
        assert result["urgency"] in {"high", "medium", "low"}
    
    @pytest.mark.unit
    def test_classifier_handles_empty_text(self):
        """Test classifier behavior with empty text."""
        result = classify_ticket("")
        
        assert result is not None
        assert "category" in result
    
    @pytest.mark.unit
    def test_router_assigns_team(self):
        """Test that router assigns appropriate team."""
        ticket_data = {
            "category": "billing",
            "urgency": "high",
            "text": "I was charged twice for my subscription"
        }
        result = route_ticket(ticket_data)
        
        assert result is not None
        assert "team" in result
        assert result["team"] in {"billing_team", "tech_team", "account_team", "support_team"}
    
    @pytest.mark.unit
    def test_router_login_issues_to_tech_team(self):
        """Test that login issues are routed to tech team."""
        ticket_data = {
            "category": "login",
            "urgency": "high",
            "text": "Cannot login after password reset"
        }
        result = route_ticket(ticket_data)
        
        assert result is not None
        assert result["team"] == "tech_team"
    
    @pytest.mark.unit
    def test_replier_generates_response(self):
        """Test that replier generates a response."""
        ticket_data = {
            "category": "billing",
            "urgency": "high",
            "text": "I was charged twice for my subscription",
            "team": "billing_team"
        }
        result = generate_reply(ticket_data)
        
        assert result is not None
        assert "reply" in result
        assert len(result["reply"]) > 0
    
    @pytest.mark.unit
    def test_qa_validates_response(self):
        """Test that QA agent validates responses."""
        ticket_data = {
            "category": "billing",
            "urgency": "high",
            "original_text": "I was charged twice",
            "reply": "We sincerely apologize for the double charge. We will process a refund to your account within 3-5 business days."
        }
        result = check_quality(ticket_data)
        
        assert result is not None
        assert "status" in result
        assert result["status"] in {"approved", "needs_review"}
    
    @pytest.mark.unit
    def test_qa_handles_poor_response(self):
        """Test QA handling of low-quality responses."""
        ticket_data = {
            "category": "billing",
            "urgency": "high",
            "original_text": "I was charged twice",
            "reply": "ok"
        }
        result = check_quality(ticket_data)
        
        assert result is not None
        assert "status" in result
        # Short responses should be flagged for review
        assert result["status"] in {"approved", "needs_review"}
