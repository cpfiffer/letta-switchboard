# Letta Schedules Test Suite

Comprehensive test suite with unit tests and end-to-end integration tests.

## Test Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── test_crypto_utils.py     # Unit tests for encryption/hashing
├── test_scheduler.py        # Unit tests for schedule logic
├── test_api_e2e.py          # E2E API tests (requires running service)
└── README.md                # This file
```

## Setup

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

## Running Tests

### Unit Tests Only (Fast)

Unit tests run without requiring a running Modal service:

```bash
# Run all unit tests
pytest -m "not e2e"

# Run specific unit test file
pytest tests/test_crypto_utils.py
pytest tests/test_scheduler.py

# Run with verbose output
pytest -v -m "not e2e"
```

### E2E Tests (Requires Running Service)

E2E tests require a running Modal service and valid Letta credentials:

**1. Start the service:**
```bash
export LETTA_SCHEDULES_DEV_MODE=true
modal serve app.py
```

**2. In another terminal, set environment variables:**
```bash
export LETTA_API_KEY="sk-..."                              # Required: Valid Letta API key
export LETTA_AGENT_ID="agent-xxx"                          # Required: Valid agent ID
export LETTA_SCHEDULES_URL="https://your-modal-url"        # Optional: defaults to dev URL
export LETTA_API_KEY_2="sk-different-key"                  # Optional: for multi-user tests
```

**3. Run E2E tests:**
```bash
# Run all E2E tests (excluding slow tests)
pytest -m "e2e and not slow"

# Run all E2E tests including slow ones
pytest -m "e2e"

# Run specific E2E test class
pytest tests/test_api_e2e.py::TestAuthentication
pytest tests/test_api_e2e.py::TestRecurringScheduleCRUD

# Run execution tests (these take 60-90 seconds each)
pytest -m "slow" -v
```

### Run All Tests

```bash
# Run everything (unit + e2e, excluding slow tests)
pytest -m "not slow"

# Run absolutely everything
pytest
```

## Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.unit` - Fast unit tests (no external dependencies)
- `@pytest.mark.e2e` - End-to-end tests (requires running service)
- `@pytest.mark.slow` - Tests that wait for cron execution (60-90s each)

## Test Categories

### 1. Unit Tests

**test_crypto_utils.py:**
- API key hashing (deterministic, correct length)
- Dev mode detection
- Encryption/decryption roundtrip
- Dev mode plaintext storage
- Production mode encryption

**test_scheduler.py:**
- Cron schedule due checking
- One-time schedule due checking
- Timezone handling
- Edge cases (just ran, long ago, exact time)

### 2. E2E API Tests

**test_api_e2e.py:**

**Authentication:**
- Invalid API key → 401
- Missing auth header → 403
- API keys never in responses

**Recurring Schedules CRUD:**
- Create, list, get, delete operations
- Authorization checks
- 404 on non-existent schedules

**One-Time Schedules CRUD:**
- Create, list, get, delete operations
- Timezone support
- Authorization checks

**Results:**
- List execution results
- Get specific result
- Results persist after schedule deletion

**Execution (Slow Tests):**
- Past schedules execute immediately (<90s)
- One-time schedules deleted after execution
- No duplicate executions
- Results created with run_id

## Environment Variables

**Required for E2E tests:**
- `LETTA_API_KEY` - Valid Letta API key
- `LETTA_AGENT_ID` - Valid Letta agent ID

**Optional:**
- `LETTA_SCHEDULES_URL` - Override API base URL (default: dev URL)
- `LETTA_API_KEY_2` - Second API key for multi-user isolation tests
- `LETTA_SCHEDULES_DEV_MODE` - Enable dev mode (default: true for tests)

## CI/CD Integration

For continuous integration, run only fast tests:

```bash
# Run unit tests + fast E2E tests
pytest -m "not slow" --timeout=30

# Generate coverage report
pytest --cov=. --cov-report=html -m "not slow"
```

For full integration testing (slower):

```bash
# Run everything including execution tests
pytest -v --timeout=120
```

## Troubleshooting

**Tests fail with "LETTA_API_KEY not set":**
- E2E tests require valid Letta credentials
- Set environment variables or run only unit tests: `pytest -m "not e2e"`

**Tests timeout:**
- Execution tests wait up to 90 seconds for cron to run
- Ensure Modal service is running: `modal serve app.py`
- Check service logs: `modal app logs letta-schedules --follow`

**"Service not reachable":**
- Verify Modal service is running
- Check `LETTA_SCHEDULES_URL` points to correct endpoint
- Ensure service accepts connections: `curl <service-url>/schedules/recurring`

**Dev mode warnings:**
- Tests automatically enable dev mode via `LETTA_SCHEDULES_DEV_MODE=true`
- No encryption key needed for local tests
- Files stored in plaintext for easy inspection

## Example Test Run

```bash
# Terminal 1: Start service
export LETTA_SCHEDULES_DEV_MODE=true
modal serve app.py

# Terminal 2: Run tests
export LETTA_API_KEY="sk-..."
export LETTA_AGENT_ID="agent-..."
pytest -v -m "e2e and not slow"
```

Expected output:
```
tests/test_api_e2e.py::TestAuthentication::test_invalid_api_key_returns_401 PASSED
tests/test_api_e2e.py::TestRecurringScheduleCRUD::test_create_recurring_schedule PASSED
tests/test_api_e2e.py::TestOneTimeScheduleCRUD::test_create_onetime_schedule PASSED
...
========== 15 passed in 12.34s ==========
```
