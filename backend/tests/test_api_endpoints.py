import pytest
from app.models.schemas import TicketInput


class TestAuthEndpoints:
    """Integration tests for authentication endpoints."""
    
    @pytest.mark.integration
    def test_register_user(self, client, test_user_data):
        """Test user registration."""
        response = client.post(
            "/auth/register",
            json={
                "username": test_user_data["username"],
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["is_active"] is True
    
    @pytest.mark.integration
    def test_register_duplicate_username(self, client, test_user_data, auth_headers):
        """Test registration with duplicate username."""
        response = client.post(
            "/auth/register",
            json={
                "username": test_user_data["username"],
                "email": "different@example.com",
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == 400
        assert "already taken" in response.json()["detail"]
    
    @pytest.mark.integration
    def test_login_user(self, client, test_user_data, auth_headers):
        """Test user login."""
        response = client.post(
            "/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == test_user_data["username"]
    
    @pytest.mark.integration
    def test_login_wrong_password(self, client, test_user_data, auth_headers):
        """Test login with wrong password."""
        response = client.post(
            "/auth/login",
            json={
                "username": test_user_data["username"],
                "password": "wrong_password"
            }
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"]
    
    @pytest.mark.integration
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info."""
        response = client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert data["is_active"] is True
    
    @pytest.mark.integration
    def test_protected_endpoint_without_auth(self, client):
        """Test that protected endpoints reject unauthenticated requests."""
        response = client.get("/auth/me")
        
        assert response.status_code == 403


class TestAnalysisEndpoints:
    """Integration tests for ticket analysis endpoints."""
    
    @pytest.mark.integration
    def test_analyze_tickets(self, client, auth_headers):
        """Test analyzing customer messages."""
        response = client.post(
            "/analyze",
            json={
                "tickets": [
                    {
                        "ticket_id": "T1",
                        "text": "I was charged twice for my subscription"
                    }
                ]
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert "results" in data
        assert len(data["results"]) == 1
        assert "metrics" in data
    
    @pytest.mark.integration
    def test_analyze_multiple_tickets(self, client, auth_headers):
        """Test analyzing multiple tickets."""
        response = client.post(
            "/analyze",
            json={
                "tickets": [
                    {"ticket_id": "T1", "text": "I cannot login"},
                    {"ticket_id": "T2", "text": "I was charged twice"},
                    {"ticket_id": "T3", "text": "App keeps crashing"}
                ]
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3
        assert data["metrics"]["total_tickets"] == 3
    
    @pytest.mark.integration
    def test_analyze_without_auth(self, client):
        """Test that analysis requires authentication."""
        response = client.post(
            "/analyze",
            json={"tickets": [{"ticket_id": "T1", "text": "test message"}]}
        )
        
        assert response.status_code == 403


class TestHistoryEndpoints:
    """Integration tests for history endpoints."""
    
    @pytest.mark.integration
    def test_get_history(self, client, auth_headers):
        """Test retrieving analysis history."""
        # First, analyze some tickets
        client.post(
            "/analyze",
            json={"tickets": [{"ticket_id": "T1", "text": "test"}]},
            headers=auth_headers
        )
        
        # Get history
        response = client.get("/history", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "run_id" in data[0]
    
    @pytest.mark.integration
    def test_get_history_detail(self, client, auth_headers):
        """Test retrieving detailed run information."""
        # Analyze tickets
        analyze_response = client.post(
            "/analyze",
            json={"tickets": [{"ticket_id": "T1", "text": "test"}]},
            headers=auth_headers
        )
        run_id = analyze_response.json()["run_id"]
        
        # Get run detail
        response = client.get(f"/history/{run_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == run_id
        assert "metrics" in data
        assert "tickets" in data
    
    @pytest.mark.integration
    def test_delete_history(self, client, auth_headers):
        """Test deleting a run from history."""
        # Analyze tickets
        analyze_response = client.post(
            "/analyze",
            json={"tickets": [{"ticket_id": "T1", "text": "test"}]},
            headers=auth_headers
        )
        run_id = analyze_response.json()["run_id"]
        
        # Delete run
        response = client.delete(f"/history/{run_id}", headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify deletion
        get_response = client.get(f"/history/{run_id}", headers=auth_headers)
        assert get_response.status_code == 404


class TestHealthAndSystemEndpoints:
    """Integration tests for health and system endpoints."""
    
    @pytest.mark.integration
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    @pytest.mark.integration
    def test_system_mode(self, client):
        """Test system mode endpoint."""
        response = client.get("/system-mode")
        
        assert response.status_code == 200
        data = response.json()
        assert "mode" in data
        assert data["mode"] in {"ai", "rule-based"}
        assert "database_type" in data
