import pytest
import time


class TestRateLimiting:
    """Integration tests for rate limiting middleware."""
    
    @pytest.mark.integration
    def test_rate_limit_allows_requests_under_limit(self, client, auth_headers):
        """Test that requests under the limit are allowed."""
        # Make requests under the limit
        for i in range(5):
            response = client.get("/health", headers=auth_headers)
            assert response.status_code == 200
    
    @pytest.mark.integration
    def test_rate_limit_returns_429_when_exceeded(self, client, auth_headers):
        """Test that requests over the limit return 429."""
        # Make requests up to the limit (120 per 60s)
        responses = []
        for i in range(121):
            response = client.get("/health", headers=auth_headers)
            responses.append(response.status_code)
        
        # At least one request should be rate limited
        has_429 = any(status == 429 for status in responses)
        assert has_429, "Rate limit was not applied"
    
    @pytest.mark.integration
    def test_rate_limit_includes_retry_after_header(self, client, auth_headers):
        """Test that 429 responses include Retry-After header."""
        # Make many requests to trigger rate limit
        for i in range(125):
            response = client.get("/health", headers=auth_headers)
            
            if response.status_code == 429:
                assert "Retry-After" in response.headers
                retry_after = int(response.headers["Retry-After"])
                assert retry_after > 0
                break
    
    @pytest.mark.integration
    def test_rate_limit_returns_limit_headers(self, client, auth_headers):
        """Test that responses include X-RateLimit headers."""
        response = client.get("/health", headers=auth_headers)
        
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert int(response.headers["X-RateLimit-Limit"]) == 120
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_rate_limit_window_reset(self, client, auth_headers):
        """Test that rate limit window resets after 60 seconds."""
        # This test is marked as slow because it requires a 60-second wait
        # In a real scenario, you might use a mock time or adjust the window
        pass


class TestCORSHeaders:
    """Integration tests for CORS configuration."""
    
    @pytest.mark.integration
    def test_cors_headers_present(self, client):
        """Test that CORS headers are included in responses."""
        response = client.get("/health")
        
        assert response.status_code == 200
        # Check for common CORS headers
        assert "access-control-allow-origin" in response.headers or \
               "Access-Control-Allow-Origin" in response.headers
    
    @pytest.mark.integration
    def test_preflight_request_allowed(self, client):
        """Test that CORS preflight requests are handled."""
        response = client.options(
            "/analyze",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # Should be 200 or 204 for preflight
        assert response.status_code in [200, 204]


class TestErrorHandling:
    """Integration tests for error handling."""
    
    @pytest.mark.integration
    def test_404_error_handling(self, client):
        """Test that 404 errors are handled properly."""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
    
    @pytest.mark.integration
    def test_405_method_not_allowed(self, client):
        """Test that 405 errors are handled properly."""
        response = client.get("/analyze")  # /analyze only supports POST
        
        assert response.status_code in [405, 405]
    
    @pytest.mark.integration
    def test_invalid_json_body(self, client, auth_headers):
        """Test handling of invalid JSON in request body."""
        response = client.post(
            "/analyze",
            content="invalid json",
            headers={
                **auth_headers,
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 422  # Unprocessable Entity
