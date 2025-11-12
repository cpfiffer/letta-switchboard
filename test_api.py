#!/usr/bin/env python3
import requests
import os
import json
from datetime import datetime, timedelta, timezone

BASE_URL = os.getenv("LETTA_SWITCHBOARD_URL", "https://letta--letta-switchboard-api-dev.modal.run")
API_KEY = os.getenv("LETTA_API_KEY")
AGENT_ID = os.getenv("LETTA_AGENT_ID", "agent-a29146cc-2fb3-452d-8c0c-bf71e5db609a")

if not API_KEY:
    print("ERROR: LETTA_API_KEY environment variable not set!")
    print("This must be a VALID Letta API key that will be validated against Letta's API.")
    print("Set it with: export LETTA_API_KEY=sk-...")
    exit(1)

print("Configuration:")
print(f"  Base URL: {BASE_URL}")
print(f"  Agent ID: {AGENT_ID}")
print(f"  API Key: {API_KEY[:20]}..." if API_KEY else "  API Key: Not set")


def test_create_recurring_schedule():
    print("\n=== Testing: Create Recurring Schedule ===")
    payload = {
        "agent_id": AGENT_ID,
        "api_key": API_KEY,
        "cron": "*/5 * * * *",
        "message": "This is a test recurring message every 5 minutes",
        "role": "user"
    }
    
    response = requests.post(f"{BASE_URL}/schedules/recurring", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"Created schedule ID: {data['id']}")
        print(json.dumps(data, indent=2))
        return data['id']
    else:
        print(f"Error: {response.text}")
        return None


def test_create_onetime_schedule():
    print("\n=== Testing: Create One-Time Schedule ===")
    
    execute_time = datetime.now(timezone.utc) + timedelta(minutes=1)
    execute_time_str = execute_time.isoformat()
    
    payload = {
        "agent_id": AGENT_ID,
        "api_key": API_KEY,
        "execute_at": execute_time_str,
        "message": f"This is a test one-time message scheduled for {execute_time_str}",
        "role": "user"
    }
    
    response = requests.post(f"{BASE_URL}/schedules/one-time", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"Created schedule ID: {data['id']}")
        print(json.dumps(data, indent=2))
        return data['id']
    else:
        print(f"Error: {response.text}")
        return None


def test_list_recurring_schedules():
    print("\n=== Testing: List Recurring Schedules ===")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(f"{BASE_URL}/schedules/recurring", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} recurring schedules")
        for schedule in data:
            print(f"  - ID: {schedule['id']}, Cron: {schedule['cron']}")
    else:
        print(f"Error: {response.text}")


def test_list_onetime_schedules():
    print("\n=== Testing: List One-Time Schedules ===")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(f"{BASE_URL}/schedules/one-time", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} one-time schedules")
        for schedule in data:
            print(f"  - ID: {schedule['id']}, Execute at: {schedule['execute_at']}")
    else:
        print(f"Error: {response.text}")


def test_list_results():
    print("\n=== Testing: List Execution Results ===")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(f"{BASE_URL}/results", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} execution results")
        for result in data:
            print(f"  - Schedule ID: {result['schedule_id']}")
            print(f"    Type: {result['schedule_type']}")
            print(f"    Run ID: {result['run_id']}")
            print(f"    Executed at: {result['executed_at']}")
    else:
        print(f"Error: {response.text}")


def test_get_result(schedule_id):
    print(f"\n=== Testing: Get Execution Result for {schedule_id} ===")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(f"{BASE_URL}/results/{schedule_id}", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Run ID: {data['run_id']}")
        print(json.dumps(data, indent=2))
    elif response.status_code == 404:
        print("No execution result yet (schedule may not have executed)")
    else:
        print(f"Error: {response.text}")


def test_get_recurring_schedule(schedule_id):
    print(f"\n=== Testing: Get Recurring Schedule {schedule_id} ===")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(f"{BASE_URL}/schedules/recurring/{schedule_id}", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")


def test_get_onetime_schedule(schedule_id):
    print(f"\n=== Testing: Get One-Time Schedule {schedule_id} ===")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(f"{BASE_URL}/schedules/one-time/{schedule_id}", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")


def test_delete_recurring_schedule(schedule_id):
    print(f"\n=== Testing: Delete Recurring Schedule {schedule_id} ===")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.delete(f"{BASE_URL}/schedules/recurring/{schedule_id}", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("Schedule deleted successfully")
    else:
        print(f"Error: {response.text}")


def test_delete_onetime_schedule(schedule_id):
    print(f"\n=== Testing: Delete One-Time Schedule {schedule_id} ===")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.delete(f"{BASE_URL}/schedules/one-time/{schedule_id}", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("Schedule deleted successfully")
    else:
        print(f"Error: {response.text}")


def main():
    print("=" * 60)
    print("Letta Schedules API Test Suite")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Agent ID: {AGENT_ID}")
    
    recurring_id = test_create_recurring_schedule()
    onetime_id = test_create_onetime_schedule()
    
    test_list_recurring_schedules()
    test_list_onetime_schedules()
    
    if recurring_id:
        test_get_recurring_schedule(recurring_id)
    
    if onetime_id:
        test_get_onetime_schedule(onetime_id)
    
    # Check execution results
    test_list_results()
    
    if recurring_id:
        test_get_result(recurring_id)
    
    if onetime_id:
        test_get_result(onetime_id)
    
    input("\n\nPress Enter to delete test schedules...")
    
    if recurring_id:
        test_delete_recurring_schedule(recurring_id)
    
    if onetime_id:
        test_delete_onetime_schedule(onetime_id)
    
    test_list_recurring_schedules()
    test_list_onetime_schedules()
    
    # Show final results
    print("\n=== Final Results After Deletion ===")
    test_list_results()
    
    print("\n" + "=" * 60)
    print("Test suite complete!")
    print("=" * 60)
    print("\nNote: Execution results remain even after schedules are deleted.")
    print("Check run status at: https://api.letta.com/v1/runs/{run_id}")


if __name__ == "__main__":
    main()
