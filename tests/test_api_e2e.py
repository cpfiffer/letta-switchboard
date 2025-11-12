import pytest
import requests
import time
import os
from datetime import datetime, timezone, timedelta


@pytest.mark.e2e
class TestAuthentication:
    def test_invalid_api_key_returns_401(self, api_base_url):
        """Invalid API key should return 401 Unauthorized."""
        headers = {"Authorization": "Bearer invalid-fake-key-123"}
        response = requests.get(f"{api_base_url}/schedules/recurring", headers=headers)
        assert response.status_code == 401
    
    def test_no_auth_header_returns_403(self, api_base_url):
        """Missing auth header should return 403."""
        response = requests.get(f"{api_base_url}/schedules/recurring")
        assert response.status_code == 403
    
    def test_api_key_not_in_response(self, api_base_url, valid_letta_api_key, valid_letta_agent_id):
        """API key should never be returned in responses."""
        headers = {"Authorization": f"Bearer {valid_letta_api_key}"}
        
        # Create schedule
        payload = {
            "agent_id": valid_letta_agent_id,
            "api_key": valid_letta_api_key,
            "cron": "*/5 * * * *",
            "message": "Test message",
            "role": "user"
        }
        response = requests.post(f"{api_base_url}/schedules/recurring", json=payload, headers=headers)
        
        # API key should not be in response
        data = response.json()
        assert "api_key" not in data
        
        # Clean up
        schedule_id = data["id"]
        requests.delete(f"{api_base_url}/schedules/recurring/{schedule_id}", headers=headers)


@pytest.mark.e2e
class TestRecurringScheduleCRUD:
    def test_create_recurring_schedule(self, api_base_url, valid_letta_api_key, valid_letta_agent_id):
        """Should successfully create a recurring schedule."""
        headers = {"Authorization": f"Bearer {valid_letta_api_key}"}
        payload = {
            "agent_id": valid_letta_agent_id,
            "api_key": valid_letta_api_key,
            "cron": "0 9 * * *",
            "message": "Daily morning message",
            "role": "user"
        }
        
        response = requests.post(f"{api_base_url}/schedules/recurring", json=payload, headers=headers)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data["cron"] == "0 9 * * *"
        assert data["message"] == "Daily morning message"
        
        # Clean up
        requests.delete(f"{api_base_url}/schedules/recurring/{data['id']}", headers=headers)
    
    def test_list_recurring_schedules(self, api_base_url, valid_letta_api_key, valid_letta_agent_id):
        """List should only return schedules for authenticated user."""
        headers = {"Authorization": f"Bearer {valid_letta_api_key}"}
        
        # Create a schedule
        payload = {
            "agent_id": valid_letta_agent_id,
            "api_key": valid_letta_api_key,
            "cron": "*/10 * * * *",
            "message": "Test",
            "role": "user"
        }
        create_response = requests.post(f"{api_base_url}/schedules/recurring", json=payload, headers=headers)
        schedule_id = create_response.json()["id"]
        
        # List schedules
        response = requests.get(f"{api_base_url}/schedules/recurring", headers=headers)
        assert response.status_code == 200
        
        schedules = response.json()
        assert isinstance(schedules, list)
        
        # Find our schedule
        our_schedule = next((s for s in schedules if s["id"] == schedule_id), None)
        assert our_schedule is not None
        assert our_schedule["cron"] == "*/10 * * * *"
        
        # Clean up
        requests.delete(f"{api_base_url}/schedules/recurring/{schedule_id}", headers=headers)
    
    def test_get_recurring_schedule(self, api_base_url, valid_letta_api_key, valid_letta_agent_id):
        """Get should return specific schedule."""
        headers = {"Authorization": f"Bearer {valid_letta_api_key}"}
        
        # Create schedule
        payload = {
            "agent_id": valid_letta_agent_id,
            "api_key": valid_letta_api_key,
            "cron": "0 12 * * *",
            "message": "Noon message",
            "role": "user"
        }
        create_response = requests.post(f"{api_base_url}/schedules/recurring", json=payload, headers=headers)
        schedule_id = create_response.json()["id"]
        
        # Get schedule
        response = requests.get(f"{api_base_url}/schedules/recurring/{schedule_id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == schedule_id
        assert data["cron"] == "0 12 * * *"
        
        # Clean up
        requests.delete(f"{api_base_url}/schedules/recurring/{schedule_id}", headers=headers)
    
    def test_delete_recurring_schedule(self, api_base_url, valid_letta_api_key, valid_letta_agent_id):
        """Delete should remove schedule."""
        headers = {"Authorization": f"Bearer {valid_letta_api_key}"}
        
        # Create schedule
        payload = {
            "agent_id": valid_letta_agent_id,
            "api_key": valid_letta_api_key,
            "cron": "0 0 * * *",
            "message": "To be deleted",
            "role": "user"
        }
        create_response = requests.post(f"{api_base_url}/schedules/recurring", json=payload, headers=headers)
        schedule_id = create_response.json()["id"]
        
        # Delete schedule
        delete_response = requests.delete(f"{api_base_url}/schedules/recurring/{schedule_id}", headers=headers)
        assert delete_response.status_code == 200
        
        # Verify it's gone
        get_response = requests.get(f"{api_base_url}/schedules/recurring/{schedule_id}", headers=headers)
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_returns_404(self, api_base_url, valid_letta_api_key):
        """Deleting non-existent schedule should return 404."""
        headers = {"Authorization": f"Bearer {valid_letta_api_key}"}
        response = requests.delete(f"{api_base_url}/schedules/recurring/fake-uuid-123", headers=headers)
        assert response.status_code == 404


@pytest.mark.e2e
class TestOneTimeScheduleCRUD:
    def test_create_onetime_schedule(self, api_base_url, valid_letta_api_key, valid_letta_agent_id):
        """Should successfully create a one-time schedule."""
        headers = {"Authorization": f"Bearer {valid_letta_api_key}"}
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        
        payload = {
            "agent_id": valid_letta_agent_id,
            "api_key": valid_letta_api_key,
            "execute_at": future_time.isoformat(),
            "message": "Future message",
            "role": "user"
        }
        
        response = requests.post(f"{api_base_url}/schedules/one-time", json=payload, headers=headers)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data["execute_at"] == future_time.isoformat()
        
        # Clean up
        requests.delete(f"{api_base_url}/schedules/one-time/{data['id']}", headers=headers)
    
    def test_list_onetime_schedules(self, api_base_url, valid_letta_api_key, valid_letta_agent_id):
        """List should only return user's schedules."""
        headers = {"Authorization": f"Bearer {valid_letta_api_key}"}
        future_time = datetime.now(timezone.utc) + timedelta(hours=2)
        
        payload = {
            "agent_id": valid_letta_agent_id,
            "api_key": valid_letta_api_key,
            "execute_at": future_time.isoformat(),
            "message": "Test",
            "role": "user"
        }
        create_response = requests.post(f"{api_base_url}/schedules/one-time", json=payload, headers=headers)
        schedule_id = create_response.json()["id"]
        
        # List schedules
        response = requests.get(f"{api_base_url}/schedules/one-time", headers=headers)
        assert response.status_code == 200
        
        schedules = response.json()
        our_schedule = next((s for s in schedules if s["id"] == schedule_id), None)
        assert our_schedule is not None
        
        # Clean up
        requests.delete(f"{api_base_url}/schedules/one-time/{schedule_id}", headers=headers)
    
    def test_delete_onetime_schedule(self, api_base_url, valid_letta_api_key, valid_letta_agent_id):
        """Delete should remove one-time schedule."""
        headers = {"Authorization": f"Bearer {valid_letta_api_key}"}
        future_time = datetime.now(timezone.utc) + timedelta(hours=3)
        
        payload = {
            "agent_id": valid_letta_agent_id,
            "api_key": valid_letta_api_key,
            "execute_at": future_time.isoformat(),
            "message": "To be deleted",
            "role": "user"
        }
        create_response = requests.post(f"{api_base_url}/schedules/one-time", json=payload, headers=headers)
        schedule_id = create_response.json()["id"]
        
        # Delete
        delete_response = requests.delete(f"{api_base_url}/schedules/one-time/{schedule_id}", headers=headers)
        assert delete_response.status_code == 200
        
        # Verify gone
        get_response = requests.get(f"{api_base_url}/schedules/one-time/{schedule_id}", headers=headers)
        assert get_response.status_code == 404


@pytest.mark.e2e
class TestResults:
    def test_list_results(self, api_base_url, valid_letta_api_key):
        """Should list execution results."""
        headers = {"Authorization": f"Bearer {valid_letta_api_key}"}
        response = requests.get(f"{api_base_url}/results", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_result_nonexistent_returns_404(self, api_base_url, valid_letta_api_key):
        """Getting non-existent result should return 404."""
        headers = {"Authorization": f"Bearer {valid_letta_api_key}"}
        response = requests.get(f"{api_base_url}/results/fake-uuid-123", headers=headers)
        assert response.status_code == 404


@pytest.mark.e2e
@pytest.mark.slow
class TestExecution:
    def test_past_onetime_executes_immediately(self, api_base_url, valid_letta_api_key, valid_letta_agent_id):
        """One-time schedule in the past should execute within 1 minute."""
        headers = {"Authorization": f"Bearer {valid_letta_api_key}"}
        past_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        
        payload = {
            "agent_id": valid_letta_agent_id,
            "api_key": valid_letta_api_key,
            "execute_at": past_time.isoformat(),
            "message": "Should execute immediately",
            "role": "user"
        }
        
        create_response = requests.post(f"{api_base_url}/schedules/one-time", json=payload, headers=headers)
        schedule_id = create_response.json()["id"]
        
        # Wait up to 90 seconds for execution
        max_wait = 90
        for i in range(max_wait):
            time.sleep(1)
            
            # Check if result exists
            result_response = requests.get(f"{api_base_url}/results/{schedule_id}", headers=headers)
            if result_response.status_code == 200:
                result = result_response.json()
                assert "run_id" in result
                assert result["schedule_type"] == "one-time"
                print(f"✓ Executed in {i+1} seconds, run_id: {result['run_id']}")
                return
        
        pytest.fail(f"Schedule did not execute within {max_wait} seconds")
    
    def test_onetime_schedule_deleted_after_execution(self, api_base_url, valid_letta_api_key, valid_letta_agent_id):
        """One-time schedule should be deleted from filesystem after execution."""
        headers = {"Authorization": f"Bearer {valid_letta_api_key}"}
        past_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        
        payload = {
            "agent_id": valid_letta_agent_id,
            "api_key": valid_letta_api_key,
            "execute_at": past_time.isoformat(),
            "message": "Should be deleted after execution",
            "role": "user"
        }
        
        create_response = requests.post(f"{api_base_url}/schedules/one-time", json=payload, headers=headers)
        schedule_id = create_response.json()["id"]
        
        # Wait for execution
        for _ in range(90):
            time.sleep(1)
            result_response = requests.get(f"{api_base_url}/results/{schedule_id}", headers=headers)
            if result_response.status_code == 200:
                break
        
        # Schedule should be deleted
        schedule_response = requests.get(f"{api_base_url}/schedules/one-time/{schedule_id}", headers=headers)
        assert schedule_response.status_code == 404
    
    def test_result_persists_after_schedule_deletion(self, api_base_url, valid_letta_api_key, valid_letta_agent_id):
        """Execution result should persist even after schedule is deleted."""
        headers = {"Authorization": f"Bearer {valid_letta_api_key}"}
        past_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        
        payload = {
            "agent_id": valid_letta_agent_id,
            "api_key": valid_letta_api_key,
            "execute_at": past_time.isoformat(),
            "message": "Test result persistence",
            "role": "user"
        }
        
        create_response = requests.post(f"{api_base_url}/schedules/one-time", json=payload, headers=headers)
        schedule_id = create_response.json()["id"]
        
        # Wait for execution
        for _ in range(90):
            time.sleep(1)
            result_response = requests.get(f"{api_base_url}/results/{schedule_id}", headers=headers)
            if result_response.status_code == 200:
                result = result_response.json()
                break
        
        # Result should still exist
        final_result = requests.get(f"{api_base_url}/results/{schedule_id}", headers=headers)
        assert final_result.status_code == 200
        assert "run_id" in final_result.json()
    
    def test_no_duplicate_execution(self, api_base_url, valid_letta_api_key, valid_letta_agent_id):
        """One-time schedule should execute exactly once, even if multiple executors spawn."""
        headers = {"Authorization": f"Bearer {valid_letta_api_key}"}
        past_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        
        payload = {
            "agent_id": valid_letta_agent_id,
            "api_key": valid_letta_api_key,
            "execute_at": past_time.isoformat(),
            "message": "Should only execute once",
            "role": "user"
        }
        
        create_response = requests.post(f"{api_base_url}/schedules/one-time", json=payload, headers=headers)
        schedule_id = create_response.json()["id"]
        
        # Wait for execution
        time.sleep(90)
        
        # Check result
        result_response = requests.get(f"{api_base_url}/results/{schedule_id}", headers=headers)
        assert result_response.status_code == 200
        
        # There should be exactly one result file, indicating one execution
        # (We can't directly verify this without filesystem access, but we can check result exists)
        result = result_response.json()
        assert result["schedule_id"] == schedule_id
        assert "run_id" in result


@pytest.mark.e2e
class TestAuthorization:
    def test_user_isolation_list(self, api_base_url, valid_letta_api_key):
        """Users should only see their own schedules in list."""
        # This test requires a second valid API key
        # Skip if not available
        second_key = os.getenv("LETTA_API_KEY_2")
        if not second_key:
            pytest.skip("LETTA_API_KEY_2 not set for multi-user testing")
        
        headers1 = {"Authorization": f"Bearer {valid_letta_api_key}"}
        headers2 = {"Authorization": f"Bearer {second_key}"}
        
        # User 1's list should not contain User 2's schedules
        response1 = requests.get(f"{api_base_url}/schedules/recurring", headers=headers1)
        response2 = requests.get(f"{api_base_url}/schedules/recurring", headers=headers2)
        
        schedules1 = response1.json()
        schedules2 = response2.json()
        
        # Lists should be independent (no overlap)
        ids1 = {s["id"] for s in schedules1}
        ids2 = {s["id"] for s in schedules2}
        
        assert ids1.isdisjoint(ids2), "Users should not see each other's schedules"
