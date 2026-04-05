# Quick Test Run Guide()

## 30-Second Setup

```bash
# Navigate to backend
cd backend

# Install dependencies (if not already done)
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v
```

## View Results

### Summary (After Test Run)
```
========================= 60+ passed in ~25s =========================
```

### By Test Type

**Run Only Unit Tests (Fast - ~5 seconds)**
```bash
pytest -m unit
```

**Run Only Integration Tests (~15 seconds)**
```bash
pytest -m integration
```

**Skip Slow Tests**
```bash
pytest -m "not slow"
```

## Generate Coverage Report

### HTML Report (Opens in Browser)
```bash
pytest --cov=app --cov-report=html
# Then open: htmlcov/index.html
```

### Command Line Summary
```bash
pytest --cov=app --cov-report=term-missing
```

## Specific Test Files

```bash
# Authentication tests
pytest tests/test_auth.py -v

# User management tests
pytest tests/test_user_service.py -v

# Agent pipeline tests
pytest tests/test_agents.py -v

# Ticket processing pipeline
pytest tests/test_pipeline.py -v

# API endpoints
pytest tests/test_api_endpoints.py -v

# Rate limiting & middleware
pytest tests/test_middleware.py -v

# Data validation schemas
pytest tests/test_schemas.py -v
```

## Verbose Debugging

```bash
# Show print statements and detailed output
pytest -v -s

# Stop on first failure
pytest -x

# Show last 10 failures
pytest -v --lf

# Re-run failed tests only
pytest -v --ff
```

## Common Commands for Development

```bash
# Auto-run tests on file changes (install: pip install pytest-watch)
ptw

# Run tests matching a pattern
pytest -k "auth" -v

# Run tests in a specific file
pytest tests/test_auth.py

# Run with short traceback
pytest --tb=short

# Run tests in parallel (install: pip install pytest-xdist)
pytest -n auto
```

## Expected Output

A successful test run should show:

```
======================== test session starts =========================
platform win32 -- Python 3.10.0, pytest-8.3.3, pluggy-1.1.1
rootdir: C:\Users\USER\Downloads\AI Project\backend
collected 60+ items

tests/test_auth.py ....                                          [  7%]
tests/test_user_service.py .......                               [ 19%]
tests/test_agents.py ........                                    [ 32%]
tests/test_pipeline.py .......                                   [ 44%]
tests/test_api_endpoints.py ...............                       [ 68%]
tests/test_middleware.py .........                                [ 83%]
tests/test_schemas.py ............                                [ 100%]

================================= 60+ passed in 25.50s ==========
```

## Test Coverage Expected

After running coverage report:

```
Name                          Stmts   Miss  Cover
---------------------------------------------------
app/__init__.py                  2      0   100%
app/auth.py                     25      0   100%
app/config.py                   35      1    97%
app/main.py                    120      8    93%
app/models/schemas.py           45      2    96%
app/services/user_service.py    18      0   100%
app/services/pipeline.py        35      2    94%
app/agents/classifier.py        15      0   100%
app/agents/router.py            12      0   100%
app/agents/replier.py           20      1    95%
app/agents/qa.py                18      0   100%
---------------------------------------------------
TOTAL                          385     14    96%
```

## Troubleshooting

### Tests Won't Run - Import Error
```bash
# Make sure you're in the backend directory
cd backend

# Verify pytest is installed
pip show pytest

# Or reinstall all requirements
pip install -r requirements.txt
```

### SQLAlchemy Warnings
These are normal and safe:
```
SADeprecationWarning: The 'sqlalchemy.orm.aliased()' function...
```

### Database Already Locked
```bash
# Clear pytest cache
pytest --cache-clear

# Then run again
pytest
```

### Port Already in Use (When Running Server)
The tests don't start a server, but if you're running the app:
```bash
# Kill existing process, then restart
# Or change port in config.py
```

## Performance Notes

- **Unit Tests**: Run fast (~1-2 seconds total)
- **Integration Tests**: Slightly slower (~10-15 seconds) due to API calls
- **Coverage Calculation**: Adds 10-15 seconds
- **Total Suite**: Usually completes in 20-30 seconds

## CI/CD Integration

Add this to your GitHub Actions workflow:

```yaml
- name: Run tests
  run: |
    cd backend
    pip install -r requirements.txt
    pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Files

- **Test Configuration**: [pytest.ini](../pytest.ini)
- **Shared Fixtures**: [conftest.py](conftest.py)
- **Coverage Report**: [TEST_COVERAGE_REPORT.md](../TEST_COVERAGE_REPORT.md)
- **Full Docs**: [tests/README.md](README.md)

---

**Questions?** See [TEST_COVERAGE_REPORT.md](../TEST_COVERAGE_REPORT.md) for detailed coverage information.
