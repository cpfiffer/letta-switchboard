import modal
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException, Header, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Optional

security = HTTPBearer()

from models import (
    RecurringScheduleCreate,
    RecurringSchedule,
    OneTimeScheduleCreate,
    OneTimeSchedule,
)
from scheduler import is_recurring_schedule_due, is_onetime_schedule_due
from letta_executor import execute_letta_message, validate_api_key
from crypto_utils import get_api_key_hash, get_encryption_key, encrypt_json, decrypt_json
from dateutil import parser as date_parser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = modal.App("switchboard")

import os as local_os

# Read dev mode setting from local environment
dev_mode_enabled = local_os.getenv("LETTA_SWITCHBOARD_DEV_MODE", "false")

image = (
    modal.Image.debian_slim()
    .pip_install_from_requirements("requirements.txt")
    .env({"LETTA_SWITCHBOARD_DEV_MODE": dev_mode_enabled})  # Must come before add_local_*
    .add_local_python_source("models", "scheduler", "letta_executor", "crypto_utils")
    .add_local_file("dashboard.html", "/root/dashboard.html")
)

volume = modal.Volume.from_name("letta-switchboard-volume", create_if_missing=True)

try:
    encryption_secret = modal.Secret.from_name("letta-switchboard-encryption")
except Exception:
    logger.warning("letta-switchboard-encryption secret not found, will use env var or generate temporary key")
    encryption_secret = None

VOLUME_PATH = "/data"
SCHEDULES_BASE = f"{VOLUME_PATH}/schedules"
RESULTS_BASE = f"{VOLUME_PATH}/results"

web_app = FastAPI()

# Lazy-load encryption key (will check env vars at runtime)
_encryption_key = None

def get_encryption_key_cached():
    global _encryption_key
    if _encryption_key is None:
        _encryption_key = get_encryption_key()
    return _encryption_key


def get_recurring_schedule_path(api_key: str, schedule_id: str) -> str:
    """Get file path for recurring schedule."""
    api_key_hash = get_api_key_hash(api_key)
    return f"{SCHEDULES_BASE}/recurring/{api_key_hash}/{schedule_id}.json"


def get_onetime_schedule_path(api_key: str, execute_at: str, schedule_id: str) -> str:
    """Get file path for one-time schedule with time bucketing."""
    api_key_hash = get_api_key_hash(api_key)
    dt = date_parser.parse(execute_at)
    date_str = dt.strftime("%Y-%m-%d")
    hour_str = dt.strftime("%H")
    return f"{SCHEDULES_BASE}/one-time/{date_str}/{hour_str}/{api_key_hash}/{schedule_id}.json"


def save_schedule(file_path: str, schedule_data: dict):
    """Save encrypted schedule to file."""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    encrypted_data = encrypt_json(schedule_data, get_encryption_key_cached())
    with open(file_path, "wb") as f:
        f.write(encrypted_data)
    volume.commit()


def load_schedule(file_path: str) -> dict:
    """Load and decrypt schedule from file."""
    try:
        with open(file_path, "rb") as f:
            encrypted_data = f.read()
        return decrypt_json(encrypted_data, get_encryption_key_cached())
    except FileNotFoundError:
        return None


def delete_schedule(file_path: str):
    """Delete schedule file."""
    try:
        Path(file_path).unlink()
        volume.commit()
        return True
    except FileNotFoundError:
        return False


def list_recurring_schedules_for_user(api_key: str) -> List[dict]:
    """List all recurring schedules for a specific user."""
    api_key_hash = get_api_key_hash(api_key)
    user_dir = f"{SCHEDULES_BASE}/recurring/{api_key_hash}"
    schedules = []
    
    if not Path(user_dir).exists():
        return schedules
    
    for file_path in Path(user_dir).glob("*.json"):
        try:
            with open(file_path, "rb") as f:
                encrypted_data = f.read()
            schedule = decrypt_json(encrypted_data, get_encryption_key_cached())
            schedules.append(schedule)
        except Exception as e:
            logger.error(f"Failed to load schedule {file_path}: {e}")
    
    return schedules


def list_onetime_schedules_for_user(api_key: str) -> List[dict]:
    """List all one-time schedules for a specific user."""
    api_key_hash = get_api_key_hash(api_key)
    base_dir = f"{SCHEDULES_BASE}/one-time"
    schedules = []
    
    if not Path(base_dir).exists():
        return schedules
    
    # Traverse all date/hour buckets
    for date_dir in Path(base_dir).iterdir():
        if not date_dir.is_dir():
            continue
        for hour_dir in date_dir.iterdir():
            if not hour_dir.is_dir():
                continue
            user_dir = hour_dir / api_key_hash
            if not user_dir.exists():
                continue
            
            for file_path in user_dir.glob("*.json"):
                try:
                    with open(file_path, "rb") as f:
                        encrypted_data = f.read()
                    schedule = decrypt_json(encrypted_data, get_encryption_key_cached())
                    schedules.append(schedule)
                except Exception as e:
                    logger.error(f"Failed to load schedule {file_path}: {e}")
    
    return schedules


def list_all_recurring_schedules() -> List[dict]:
    """List all recurring schedules across all users (for cron job)."""
    schedules = []
    recurring_dir = f"{SCHEDULES_BASE}/recurring"
    
    if not Path(recurring_dir).exists():
        return schedules
    
    for user_dir in Path(recurring_dir).iterdir():
        if not user_dir.is_dir():
            continue
        for file_path in user_dir.glob("*.json"):
            try:
                with open(file_path, "rb") as f:
                    encrypted_data = f.read()
                schedule = decrypt_json(encrypted_data, get_encryption_key_cached())
                schedules.append(schedule)
            except Exception as e:
                logger.error(f"Failed to load schedule {file_path}: {e}")
    
    return schedules


def list_onetime_schedules_for_time(date_str: str, hour_str: str) -> List[dict]:
    """List all one-time schedules for a specific date/hour (for cron job)."""
    schedules = []
    time_dir = f"{SCHEDULES_BASE}/one-time/{date_str}/{hour_str}"
    
    if not Path(time_dir).exists():
        return schedules
    
    for user_dir in Path(time_dir).iterdir():
        if not user_dir.is_dir():
            continue
        for file_path in user_dir.glob("*.json"):
            try:
                with open(file_path, "rb") as f:
                    encrypted_data = f.read()
                schedule = decrypt_json(encrypted_data, get_encryption_key_cached())
                schedules.append(schedule)
            except Exception as e:
                logger.error(f"Failed to load schedule {file_path}: {e}")
    
    return schedules


def find_onetime_schedule_for_user(api_key: str, schedule_id: str) -> tuple[dict, str]:
    """Find a one-time schedule by ID for a specific user. Returns (schedule, file_path)."""
    api_key_hash = get_api_key_hash(api_key)
    base_dir = f"{SCHEDULES_BASE}/one-time"
    
    if not Path(base_dir).exists():
        return None, None
    
    # Search through all time buckets for this user
    for date_dir in Path(base_dir).iterdir():
        if not date_dir.is_dir():
            continue
        for hour_dir in date_dir.iterdir():
            if not hour_dir.is_dir():
                continue
            user_dir = hour_dir / api_key_hash
            if not user_dir.exists():
                continue
            
            file_path = user_dir / f"{schedule_id}.json"
            if file_path.exists():
                try:
                    with open(file_path, "rb") as f:
                        encrypted_data = f.read()
                    schedule = decrypt_json(encrypted_data, get_encryption_key_cached())
                    return schedule, str(file_path)
                except Exception as e:
                    logger.error(f"Failed to load schedule {file_path}: {e}")
    
    return None, None


@web_app.get("/")
async def root(request: Request):
    """Landing page with usage instructions."""
    
    # Check if browser is requesting HTML
    accept_header = request.headers.get("accept", "")
    wants_html = "text/html" in accept_header
    
    info = {
        "service": "Letta Switchboard",
        "description": "Free hosted message routing service for Letta agents",
        "version": "1.0.0",
        "documentation": "https://github.com/cpfiffer/letta-switchboard",
        "features": [
            "Send messages immediately or scheduled for later",
            "Recurring schedules with cron expressions",
            "Secure API key isolation",
            "Execution tracking with run IDs"
        ],
        "quick_start": {
            "curl_example": {
                "one_time": "curl -X POST https://letta--switchboard-api.modal.run/schedules/one-time -H 'Authorization: Bearer YOUR_LETTA_API_KEY' -H 'Content-Type: application/json' -d '{\"agent_id\": \"agent-xxx\", \"execute_at\": \"2025-11-13T09:00:00Z\", \"message\": \"Hello!\"}'",
                "recurring": "curl -X POST https://letta--switchboard-api.modal.run/schedules/recurring -H 'Authorization: Bearer YOUR_LETTA_API_KEY' -H 'Content-Type: application/json' -d '{\"agent_id\": \"agent-xxx\", \"cron\": \"0 9 * * 1-5\", \"message\": \"Daily standup\"}'"
            },
            "cli": {
                "install": "git clone https://github.com/cpfiffer/letta-switchboard.git && cd letta-switchboard/cli && go build -o letta-switchboard",
                "configure": "./letta-switchboard config set-api-key YOUR_LETTA_API_KEY",
                "send": "./letta-switchboard send --agent-id agent-xxx --message 'Hello!'",
                "schedule": "./letta-switchboard send --agent-id agent-xxx --message 'Reminder' --execute-at 'tomorrow at 9am'",
                "recurring": "./letta-switchboard recurring create --agent-id agent-xxx --message 'Daily standup' --cron 'every weekday'"
            }
        },
        "endpoints": {
            "POST /schedules/one-time": "Create a one-time schedule",
            "POST /schedules/recurring": "Create a recurring schedule",
            "GET /schedules/one-time": "List your one-time schedules",
            "GET /schedules/recurring": "List your recurring schedules",
            "GET /schedules/one-time/{id}": "Get specific one-time schedule",
            "GET /schedules/recurring/{id}": "Get specific recurring schedule",
            "DELETE /schedules/one-time/{id}": "Delete one-time schedule",
            "DELETE /schedules/recurring/{id}": "Delete recurring schedule",
            "GET /results": "List execution results",
            "GET /results/{schedule_id}": "Get result for specific schedule"
        },
        "authentication": "All endpoints require 'Authorization: Bearer YOUR_LETTA_API_KEY' header",
        "support": "https://github.com/cpfiffer/letta-switchboard/issues"
    }
    
    if wants_html:
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Letta Switchboard</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * { box-sizing: border-box; }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #f8f9fa;
                    margin: 0;
                    padding: 24px;
                    line-height: 1.6;
                    color: #1a1a1a;
                }
                .container {
                    max-width: 720px;
                    margin: 0 auto;
                }
                h1 {
                    font-size: 28px;
                    font-weight: 600;
                    margin: 0 0 8px 0;
                }
                .subtitle {
                    color: #666;
                    margin-bottom: 24px;
                }
                .status {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    background: #e8f5e9;
                    color: #2e7d32;
                    padding: 4px 10px;
                    border-radius: 4px;
                    font-size: 13px;
                    font-weight: 500;
                    margin-bottom: 24px;
                }
                .status::before {
                    content: '';
                    width: 8px;
                    height: 8px;
                    background: #4caf50;
                    border-radius: 50%;
                }
                .dashboard-btn {
                    display: inline-block;
                    background: #1a1a1a;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 500;
                    margin-bottom: 32px;
                }
                .dashboard-btn:hover {
                    background: #333;
                }
                h2 {
                    font-size: 18px;
                    font-weight: 600;
                    margin: 32px 0 12px 0;
                    padding-bottom: 8px;
                    border-bottom: 1px solid #e0e0e0;
                }
                .features {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: 12px;
                    margin-bottom: 8px;
                }
                .feature {
                    background: white;
                    padding: 12px 16px;
                    border-radius: 6px;
                    border: 1px solid #e0e0e0;
                }
                .feature-title {
                    font-weight: 600;
                    margin-bottom: 2px;
                }
                .feature-desc {
                    color: #666;
                    font-size: 14px;
                }
                pre {
                    background: #1a1a1a;
                    color: #e0e0e0;
                    padding: 16px;
                    border-radius: 6px;
                    overflow-x: auto;
                    font-family: 'SF Mono', Consolas, monospace;
                    font-size: 13px;
                    line-height: 1.5;
                    margin: 12px 0;
                }
                pre .comment { color: #6a9955; }
                pre .string { color: #ce9178; }
                code {
                    background: #f0f0f0;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'SF Mono', Consolas, monospace;
                    font-size: 13px;
                }
                .endpoints {
                    background: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    overflow: hidden;
                }
                .endpoint {
                    display: flex;
                    padding: 10px 16px;
                    border-bottom: 1px solid #e0e0e0;
                    font-size: 14px;
                }
                .endpoint:last-child { border-bottom: none; }
                .endpoint-method {
                    font-family: 'SF Mono', Consolas, monospace;
                    font-weight: 600;
                    width: 220px;
                    flex-shrink: 0;
                }
                .endpoint-desc {
                    color: #666;
                }
                .note {
                    background: #fff3e0;
                    border-left: 3px solid #ff9800;
                    padding: 12px 16px;
                    margin: 16px 0;
                    border-radius: 0 6px 6px 0;
                }
                .links {
                    display: flex;
                    gap: 24px;
                    flex-wrap: wrap;
                }
                .links a {
                    color: #1a1a1a;
                    text-decoration: none;
                    font-weight: 500;
                }
                .links a:hover {
                    text-decoration: underline;
                }
                @media (max-width: 600px) {
                    .endpoint { flex-direction: column; gap: 4px; }
                    .endpoint-method { width: auto; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Letta Switchboard</h1>
                <p class="subtitle">Message scheduling and routing for Letta agents</p>
                <div class="status">Operational</div>
                <br>
                <a href="/dashboard" class="dashboard-btn">Open Dashboard</a>

                <h2>Features</h2>
                <div class="features">
                    <div class="feature">
                        <div class="feature-title">Scheduled Messages</div>
                        <div class="feature-desc">Send messages now or schedule for later</div>
                    </div>
                    <div class="feature">
                        <div class="feature-title">Recurring Schedules</div>
                        <div class="feature-desc">Cron expressions for repeated delivery</div>
                    </div>
                    <div class="feature">
                        <div class="feature-title">API Key Isolation</div>
                        <div class="feature-desc">Secure per-user schedule storage</div>
                    </div>
                    <div class="feature">
                        <div class="feature-title">Execution Tracking</div>
                        <div class="feature-desc">Track results with run IDs</div>
                    </div>
                </div>

                <h2>Quick Start</h2>
                <p>Schedule a one-time message:</p>
                <pre>curl -X POST https://letta--switchboard-api.modal.run/schedules/one-time \\
  -H 'Authorization: Bearer YOUR_LETTA_API_KEY' \\
  -H 'Content-Type: application/json' \\
  -d '{
    <span class="string">"agent_id"</span>: <span class="string">"agent-xxx"</span>,
    <span class="string">"execute_at"</span>: <span class="string">"2025-12-09T09:00:00Z"</span>,
    <span class="string">"message"</span>: <span class="string">"Hello from Switchboard!"</span>
  }'</pre>

                <p>Create a recurring schedule:</p>
                <pre>curl -X POST https://letta--switchboard-api.modal.run/schedules/recurring \\
  -H 'Authorization: Bearer YOUR_LETTA_API_KEY' \\
  -H 'Content-Type: application/json' \\
  -d '{
    <span class="string">"agent_id"</span>: <span class="string">"agent-xxx"</span>,
    <span class="string">"cron"</span>: <span class="string">"0 9 * * 1-5"</span>,
    <span class="string">"message"</span>: <span class="string">"Daily standup reminder"</span>
  }'</pre>

                <h2>CLI Tool</h2>
                <p>Natural language scheduling from your terminal:</p>
                <pre><span class="comment"># Install</span>
git clone https://github.com/cpfiffer/letta-switchboard.git
cd letta-switchboard/cli && go build -o letta-schedules
./letta-schedules config set-api-key YOUR_LETTA_API_KEY

<span class="comment"># Send a message</span>
./letta-schedules send --agent-id agent-xxx --message "Hello!"

<span class="comment"># Schedule with natural language</span>
./letta-schedules send --agent-id agent-xxx --message "Reminder" --at "tomorrow 9am"

<span class="comment"># Create recurring schedule</span>
./letta-schedules recurring create --agent-id agent-xxx --cron "every weekday" --message "Standup"</pre>

                <h2>API Endpoints</h2>
                <div class="endpoints">
                    <div class="endpoint">
                        <span class="endpoint-method">POST /schedules/one-time</span>
                        <span class="endpoint-desc">Create one-time schedule</span>
                    </div>
                    <div class="endpoint">
                        <span class="endpoint-method">POST /schedules/recurring</span>
                        <span class="endpoint-desc">Create recurring schedule</span>
                    </div>
                    <div class="endpoint">
                        <span class="endpoint-method">GET /schedules/one-time</span>
                        <span class="endpoint-desc">List one-time schedules</span>
                    </div>
                    <div class="endpoint">
                        <span class="endpoint-method">GET /schedules/recurring</span>
                        <span class="endpoint-desc">List recurring schedules</span>
                    </div>
                    <div class="endpoint">
                        <span class="endpoint-method">DELETE /schedules/{type}/{id}</span>
                        <span class="endpoint-desc">Delete a schedule</span>
                    </div>
                    <div class="endpoint">
                        <span class="endpoint-method">GET /results</span>
                        <span class="endpoint-desc">List execution results</span>
                    </div>
                </div>

                <div class="note">
                    <strong>Authentication required:</strong> All endpoints need <code>Authorization: Bearer YOUR_LETTA_API_KEY</code>
                </div>

                <h2>Links</h2>
                <div class="links">
                    <a href="/dashboard">Dashboard</a>
                    <a href="https://github.com/cpfiffer/letta-switchboard">Documentation</a>
                    <a href="https://github.com/cpfiffer/letta-switchboard/issues">Support</a>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    return info


@web_app.get("/dashboard")
async def dashboard():
    """Dashboard UI for managing schedules."""
    try:
        with open("/root/dashboard.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard not found")


@web_app.post("/schedules/recurring")
async def create_recurring_schedule(schedule: RecurringScheduleCreate, credentials: HTTPAuthorizationCredentials = Security(security)):
    api_key = credentials.credentials
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid Letta API key")
    
    # Inject api_key from Authorization header
    schedule_obj = RecurringSchedule(api_key=api_key, **schedule.model_dump())
    schedule_dict = schedule_obj.model_dump(mode='json')
    file_path = get_recurring_schedule_path(api_key, schedule_obj.id)
    save_schedule(file_path, schedule_dict)
    response_dict = schedule_dict.copy()
    response_dict.pop("api_key", None)
    return JSONResponse(content=response_dict, status_code=201)


@web_app.post("/schedules/one-time")
async def create_onetime_schedule(schedule: OneTimeScheduleCreate, credentials: HTTPAuthorizationCredentials = Security(security)):
    api_key = credentials.credentials
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid Letta API key")
    
    # Inject api_key from Authorization header
    schedule_obj = OneTimeSchedule(api_key=api_key, **schedule.model_dump())
    schedule_dict = schedule_obj.model_dump(mode='json')
    file_path = get_onetime_schedule_path(api_key, schedule.execute_at, schedule_obj.id)
    save_schedule(file_path, schedule_dict)
    response_dict = schedule_dict.copy()
    response_dict.pop("api_key", None)
    return JSONResponse(content=response_dict, status_code=201)


@web_app.get("/schedules/recurring")
async def list_recurring_schedules(credentials: HTTPAuthorizationCredentials = Security(security)):
    api_key = credentials.credentials
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid Letta API key")
    
    schedules = list_recurring_schedules_for_user(api_key)
    for schedule in schedules:
        schedule.pop("api_key", None)
    return JSONResponse(content=schedules)


@web_app.get("/schedules/one-time")
async def list_onetime_schedules(credentials: HTTPAuthorizationCredentials = Security(security)):
    api_key = credentials.credentials
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid Letta API key")
    
    schedules = list_onetime_schedules_for_user(api_key)
    for schedule in schedules:
        schedule.pop("api_key", None)
    return JSONResponse(content=schedules)


@web_app.get("/schedules/recurring/{schedule_id}")
async def get_recurring_schedule(schedule_id: str, credentials: HTTPAuthorizationCredentials = Security(security)):
    api_key = credentials.credentials
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid Letta API key")
    
    file_path = get_recurring_schedule_path(api_key, schedule_id)
    schedule = load_schedule(file_path)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if schedule.get("api_key") != api_key:
        raise HTTPException(status_code=403, detail="Forbidden")
    schedule_copy = schedule.copy()
    schedule_copy.pop("api_key", None)
    return JSONResponse(content=schedule_copy)


@web_app.get("/schedules/one-time/{schedule_id}")
async def get_onetime_schedule(schedule_id: str, credentials: HTTPAuthorizationCredentials = Security(security)):
    api_key = credentials.credentials
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid Letta API key")
    
    schedule, _ = find_onetime_schedule_for_user(api_key, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if schedule.get("api_key") != api_key:
        raise HTTPException(status_code=403, detail="Forbidden")
    schedule_copy = schedule.copy()
    schedule_copy.pop("api_key", None)
    return JSONResponse(content=schedule_copy)


@web_app.delete("/schedules/recurring/{schedule_id}")
async def delete_recurring_schedule(schedule_id: str, credentials: HTTPAuthorizationCredentials = Security(security)):
    api_key = credentials.credentials
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid Letta API key")
    
    file_path = get_recurring_schedule_path(api_key, schedule_id)
    schedule = load_schedule(file_path)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if schedule.get("api_key") != api_key:
        raise HTTPException(status_code=403, detail="Forbidden")
    if delete_schedule(file_path):
        return JSONResponse(content={"message": "Schedule deleted"})
    else:
        raise HTTPException(status_code=404, detail="Schedule not found")


@web_app.delete("/schedules/one-time/{schedule_id}")
async def delete_onetime_schedule(schedule_id: str, credentials: HTTPAuthorizationCredentials = Security(security)):
    api_key = credentials.credentials
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid Letta API key")
    
    schedule, file_path = find_onetime_schedule_for_user(api_key, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if schedule.get("api_key") != api_key:
        raise HTTPException(status_code=403, detail="Forbidden")
    if delete_schedule(file_path):
        return JSONResponse(content={"message": "Schedule deleted"})
    else:
        raise HTTPException(status_code=404, detail="Schedule not found")


@web_app.get("/results")
async def list_execution_results(credentials: HTTPAuthorizationCredentials = Security(security)):
    """List all execution results for the authenticated user."""
    api_key = credentials.credentials
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid Letta API key")
    
    api_key_hash = get_api_key_hash(api_key)
    results_dir = f"{RESULTS_BASE}/{api_key_hash}"
    results = []
    
    if Path(results_dir).exists():
        for result_file in Path(results_dir).glob("*.json"):
            try:
                with open(result_file, "rb") as f:
                    encrypted_data = f.read()
                result = decrypt_json(encrypted_data, get_encryption_key_cached())
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to load result {result_file}: {e}")
    
    return JSONResponse(content=results)


@web_app.get("/results/{schedule_id}")
async def get_execution_result(schedule_id: str, credentials: HTTPAuthorizationCredentials = Security(security)):
    """Get execution result for a specific schedule."""
    api_key = credentials.credentials
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid Letta API key")
    
    api_key_hash = get_api_key_hash(api_key)
    result_file = f"{RESULTS_BASE}/{api_key_hash}/{schedule_id}.json"
    
    if not Path(result_file).exists():
        raise HTTPException(status_code=404, detail="Result not found")
    
    try:
        with open(result_file, "rb") as f:
            encrypted_data = f.read()
        result = decrypt_json(encrypted_data, get_encryption_key_cached())
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Failed to load result: {e}")
        raise HTTPException(status_code=500, detail="Failed to load result")


@app.function(image=image, volumes={VOLUME_PATH: volume}, secrets=[encryption_secret] if encryption_secret else [])
@modal.asgi_app()
def api():
    return web_app


@app.function(image=image, volumes={VOLUME_PATH: volume}, secrets=[encryption_secret] if encryption_secret else [])
async def execute_schedule(
    schedule_id: str,
    agent_id: str,
    api_key: str,
    message: str,
    role: str,
    schedule_type: str,
    execute_at: str = None,
):
    logger.info(f"Executing {schedule_type} schedule {schedule_id} for agent {agent_id}")

    # Reload volume to see latest changes (in case schedule was deleted)
    volume.reload()

    # Check if schedule still exists before executing
    if schedule_type == "one-time" and execute_at:
        file_path = get_onetime_schedule_path(api_key, execute_at, schedule_id)
    else:
        file_path = get_recurring_schedule_path(api_key, schedule_id)

    schedule = load_schedule(file_path)
    if not schedule:
        # For one-time schedules, this is expected (already executed or deleted)
        # For recurring schedules, this indicates the schedule was deleted by the user
        if schedule_type == "one-time":
            logger.debug(f"One-time schedule {schedule_id} not found (already executed or deleted)")
        else:
            logger.info(f"Recurring schedule {schedule_id} was deleted, skipping execution")
        return {"success": False, "error": "Schedule deleted"}
    
    # For one-time schedules: DELETE IMMEDIATELY to prevent race condition
    # Filesystem becomes source of truth: if file exists, it hasn't run
    if schedule_type == "one-time":
        try:
            Path(file_path).unlink()
            volume.commit()
            logger.info(f"Deleted one-time schedule {schedule_id} to prevent re-execution")
        except Exception as e:
            logger.error(f"Failed to delete schedule {schedule_id}, may re-execute: {e}")
            return {"success": False, "error": "Could not lock schedule for execution"}
    
    # For recurring schedules: update last_run timestamp
    elif schedule_type == "recurring":
        schedule["last_run"] = datetime.utcnow().isoformat()
        save_schedule(file_path, schedule)
        logger.info(f"Updated last_run for recurring schedule {schedule_id}")
    
    # Execute the message
    result = await execute_letta_message(agent_id, api_key, message, role)
    
    # Always save execution result (success or failure)
    if result.get("success"):
        # Successful execution
        save_execution_result(
            api_key=api_key,
            schedule_id=schedule_id,
            schedule_type=schedule_type,
            agent_id=agent_id,
            message=message,
            run_id=result.get("run_id"),
            status="success"
        )
    else:
        # Failed execution - save error result
        error_msg = result.get("error", "Unknown error")
        logger.error(f"Execution failed for schedule {schedule_id}: {error_msg}")
        
        save_execution_result(
            api_key=api_key,
            schedule_id=schedule_id,
            schedule_type=schedule_type,
            agent_id=agent_id,
            message=message,
            error=error_msg,
            status="failed"
        )

        # Only terminate recurring schedules on permanent errors (401, 404)
        # Transient errors (timeouts, rate limits, 5xx) should not remove the schedule
        if schedule_type == "recurring" and result.get("permanent", False):
            try:
                Path(file_path).unlink()
                volume.commit()
                logger.warning(f"Terminated recurring schedule {schedule_id} due to permanent error: {error_msg}")
            except Exception as e:
                logger.error(f"Failed to delete failed recurring schedule {schedule_id}: {e}")
    
    return result


def save_execution_result(api_key: str, schedule_id: str, schedule_type: str, agent_id: str, message: str, run_id: str = None, error: str = None, status: str = "success"):
    """Save execution result to results folder (success or failure)."""
    api_key_hash = get_api_key_hash(api_key)
    result_dir = f"{RESULTS_BASE}/{api_key_hash}"
    Path(result_dir).mkdir(parents=True, exist_ok=True)
    
    result_file = f"{result_dir}/{schedule_id}.json"
    
    result_data = {
        "schedule_id": schedule_id,
        "schedule_type": schedule_type,
        "status": status,
        "agent_id": agent_id,
        "message": message,
        "executed_at": datetime.utcnow().isoformat(),
    }
    
    # Add run_id only if present (successful execution)
    if run_id:
        result_data["run_id"] = run_id
    
    # Add error only if present (failed execution)
    if error:
        result_data["error"] = error
    
    encrypted_data = encrypt_json(result_data, get_encryption_key_cached())
    with open(result_file, "wb") as f:
        f.write(encrypted_data)
    volume.commit()
    
    logger.info(f"Saved execution result for schedule {schedule_id}, run_id: {run_id}")


def cleanup_empty_directories():
    """Remove empty directories to keep filesystem clean."""
    removed_count = 0
    
    # Clean up one-time schedule directories (date/hour/user structure)
    onetime_base = f"{SCHEDULES_BASE}/one-time"
    if Path(onetime_base).exists():
        for date_dir in Path(onetime_base).iterdir():
            if not date_dir.is_dir():
                continue
            
            for hour_dir in date_dir.iterdir():
                if not hour_dir.is_dir():
                    continue
                
                # Remove empty user directories
                for user_dir in hour_dir.iterdir():
                    if user_dir.is_dir() and not any(user_dir.iterdir()):
                        user_dir.rmdir()
                        removed_count += 1
                        logger.debug(f"Removed empty directory: {user_dir}")
                
                # Remove empty hour directory
                if not any(hour_dir.iterdir()):
                    hour_dir.rmdir()
                    removed_count += 1
                    logger.debug(f"Removed empty directory: {hour_dir}")
            
            # Remove empty date directory
            if not any(date_dir.iterdir()):
                date_dir.rmdir()
                removed_count += 1
                logger.debug(f"Removed empty directory: {date_dir}")
    
    # Clean up recurring schedule directories (user structure only)
    recurring_base = f"{SCHEDULES_BASE}/recurring"
    if Path(recurring_base).exists():
        for user_dir in Path(recurring_base).iterdir():
            if user_dir.is_dir() and not any(user_dir.iterdir()):
                user_dir.rmdir()
                removed_count += 1
                logger.debug(f"Removed empty directory: {user_dir}")
    
    if removed_count > 0:
        logger.info(f"Cleanup: Removed {removed_count} empty directories")
        volume.commit()


@app.function(
    image=image,
    volumes={VOLUME_PATH: volume},
    secrets=[encryption_secret] if encryption_secret else [],
    schedule=modal.Cron("* * * * *"),
)
async def check_and_execute_schedules():
    logger.info("Checking schedules...")

    # Reload volume to see latest changes (deletes, updates, etc.)
    volume.reload()

    current_time = datetime.now(timezone.utc)
    
    # Check recurring schedules (all users)
    recurring_schedules = list_all_recurring_schedules()
    for schedule in recurring_schedules:
        if is_recurring_schedule_due(schedule, current_time):
            logger.info(f"Executing recurring schedule {schedule['id']}")
            execute_schedule.spawn(
                schedule_id=schedule["id"],
                agent_id=schedule["agent_id"],
                api_key=schedule["api_key"],
                message=schedule["message"],
                role=schedule["role"],
                schedule_type="recurring",
            )
    
    # Check one-time schedules (only current date/hour bucket)
    date_str = current_time.strftime("%Y-%m-%d")
    hour_str = current_time.strftime("%H")
    onetime_schedules = list_onetime_schedules_for_time(date_str, hour_str)
    
    for schedule in onetime_schedules:
        if is_onetime_schedule_due(schedule, current_time):
            logger.info(f"Executing one-time schedule {schedule['id']}")
            execute_schedule.spawn(
                schedule_id=schedule["id"],
                agent_id=schedule["agent_id"],
                api_key=schedule["api_key"],
                message=schedule["message"],
                role=schedule["role"],
                schedule_type="one-time",
                execute_at=schedule["execute_at"],
            )
    
    # Clean up empty directories
    cleanup_empty_directories()
    
    logger.info("Schedule check complete")
