import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["LETTA_SWITCHBOARD_DEV_MODE"] = "true"


@pytest.fixture
def temp_volume_path():
    """Create a temporary directory to simulate Modal volume."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_api_key():
    """A mock API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def mock_api_key_2():
    """A second mock API key for multi-user testing."""
    return "test-api-key-67890"


@pytest.fixture
def mock_agent_id():
    """A mock agent ID for testing."""
    return "agent-test-123"


@pytest.fixture
def encryption_key():
    """Generate a test encryption key."""
    return Fernet.generate_key()


@pytest.fixture
def test_recurring_schedule_data(mock_api_key, mock_agent_id):
    """Sample recurring schedule data."""
    return {
        "agent_id": mock_agent_id,
        "api_key": mock_api_key,
        "cron": "*/5 * * * *",
        "message": "Test recurring message",
        "role": "user"
    }


@pytest.fixture
def test_onetime_schedule_data(mock_api_key, mock_agent_id):
    """Sample one-time schedule data."""
    future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    return {
        "agent_id": mock_agent_id,
        "api_key": mock_api_key,
        "execute_at": future_time.isoformat(),
        "message": "Test one-time message",
        "role": "user"
    }


@pytest.fixture
def past_onetime_schedule_data(mock_api_key, mock_agent_id):
    """One-time schedule scheduled in the past (should execute immediately)."""
    past_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    return {
        "agent_id": mock_agent_id,
        "api_key": mock_api_key,
        "execute_at": past_time.isoformat(),
        "message": "Test past message",
        "role": "user"
    }


@pytest.fixture
def api_base_url():
    """Base URL for API testing. Override with LETTA_SWITCHBOARD_URL env var."""
    return os.getenv("LETTA_SWITCHBOARD_URL", "https://letta--letta-switchboard-api-dev.modal.run")


@pytest.fixture
def valid_letta_api_key():
    """Real Letta API key for E2E tests. Must be set via env var."""
    api_key = os.getenv("LETTA_API_KEY")
    if not api_key:
        pytest.skip("LETTA_API_KEY not set - skipping E2E test")
    return api_key


@pytest.fixture
def valid_letta_agent_id():
    """Real Letta agent ID for E2E tests."""
    agent_id = os.getenv("LETTA_AGENT_ID")
    if not agent_id:
        pytest.skip("LETTA_AGENT_ID not set - skipping E2E test")
    return agent_id
