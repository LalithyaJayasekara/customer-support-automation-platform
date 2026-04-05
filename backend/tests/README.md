# Test Suite Documentation

## Overview
Comprehensive test suite with **60+ tests** covering unit tests, integration tests, and validation tests.

## Test Structure

### Test Files (8 total)

1. **test_auth.py** (4 tests)
   - Tests JWT token generation and validation
   - Tests token expiration handling
   - Tests invalid token rejection

2. **test_user_service.py** (7 tests)
   - User creation and validation
   - User retrieval by username/email
   - Authentication with password verification
   - Duplicate username detection

3. **test_agents.py** (8 tests)
   - Ticket classification accuracy
   - Team routing logic
   - Reply generation
   - QA validation

4. **test_pipeline.py** (7 tests)
   - Complete pipeline execution
   - Category detection
   - Urgency assessment
   - Response quality validation

5. **test_api_endpoints.py** (15 tests)
   - User registration/login endpoints
   - Ticket analysis endpoints
   - History retrieval and deletion
   - Protected endpoint authentication

6. **test_middleware.py** (9 tests)
   - Rate limiting enforcement
   - CORS headers validation
   - Error handling (404, 405, 422)
   - Retry-After header presence

7. **test_schemas.py** (12 tests)
   - Pydantic schema validation
   - Email validation
   - Password strength requirements
   - Request/response structure validation

8. **conftest.py** (Fixtures)
   - `test_db`: Temporary SQLite database
   - `db_session`: Database session with automatic rollback
   - `client`: FastAPI TestClient with dependency overrides
   - `test_user_data`: Standard test user credentials
   - `auth_headers`: Pre-authenticated headers

## Running Tests

### All Tests
```bash
pytest
```

### Tests by Category
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Slow tests (excluded by default)
pytest -m slow

# Exclude slow tests
pytest -m "not slow"
```

### Tests by File
```bash
pytest backend/tests/test_auth.py
pytest backend/tests/test_user_service.py
pytest backend/tests/test_agents.py
pytest backend/tests/test_pipeline.py
pytest backend/tests/test_api_endpoints.py
pytest backend/tests/test_middleware.py
pytest backend/tests/test_schemas.py
```

### Verbose Output
```bash
pytest -v
```

### With Coverage Report
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

## Coverage Report

After running tests with coverage, generate reports:

```bash
# HTML report
pytest --cov=app --cov-report=html
# Open: htmlcov/index.html

# Terminal summary
pytest --cov=app --cov-report=term-missing
```

## Test Markers

- `@pytest.mark.unit` - Fast unit tests (no I/O)
- `@pytest.mark.integration` - Integration tests (includes API calls, DB)
- `@pytest.mark.slow` - Long-running tests (skipped by default)

## Environment Setup

Required packages (already in requirements.txt):
- `pytest==8.3.3` - Test framework
- `pytest-cov==5.0.0` - Coverage plugin
- `httpx==0.27.0` - Test client for FastAPI

## Database Testing

Tests use an isolated temporary SQLite database:

1. **Setup**: Each test session gets a fresh database
2. **Isolation**: Database transactions are rolled back after each test
3. **Cleanup**: Temporary databases are removed after test completion

This ensures tests don't interfere with each other or actual data.

## What's Tested

### Authentication (11 tests)
- Token generation and validation
- Login/registration flow
- Protected endpoint access
- Invalid credentials rejection

### Data Validation (12 tests)
- User creation validation
- Email format validation
- Password requirements
- Request/response schemas

### Business Logic (15 tests)
- User service operations
- Ticket classification
- Team routing
- Reply generation
- QA validation

### API Integration (24+ tests)
- All CRUD operations
- Error responses
- Rate limiting
- CORS policy

## Common Issues & Solutions

### Import Errors
Ensure you're in the correct directory:
```bash
cd backend
pytest
```

### Database Lock
Close any other connections to test DB, then:
```bash
pytest --cache-clear
```

### Slow Tests
Run without slow tests:
```bash
pytest -m "not slow"
```

## Adding New Tests

1. Create test file: `backend/tests/test_<feature>.py`
2. Import fixtures from conftest.py
3. Add `@pytest.mark.unit` or `@pytest.mark.integration`
4. Follow naming: `test_<action>_<scenario>`

Example:
```python
import pytest

class TestFeature:
    @pytest.mark.unit
    def test_something(self, db_session):
        # Your test here
        assert True
```

## CI/CD Integration

For GitHub Actions, add to `.github/workflows/tests.yml`:
```yaml
- name: Run tests
  run: |
    cd backend
    pip install -r requirements.txt
    pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```
