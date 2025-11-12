import modal
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
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


@web_app.post("/schedules/recurring")
async def create_recurring_schedule(schedule: RecurringScheduleCreate):
    if not validate_api_key(schedule.api_key):
        raise HTTPException(status_code=401, detail="Invalid Letta API key")
    
    schedule_obj = RecurringSchedule(**schedule.model_dump())
    schedule_dict = schedule_obj.model_dump(mode='json')
    file_path = get_recurring_schedule_path(schedule.api_key, schedule_obj.id)
    save_schedule(file_path, schedule_dict)
    response_dict = schedule_dict.copy()
    response_dict.pop("api_key", None)
    return JSONResponse(content=response_dict, status_code=201)


@web_app.post("/schedules/one-time")
async def create_onetime_schedule(schedule: OneTimeScheduleCreate):
    if not validate_api_key(schedule.api_key):
        raise HTTPException(status_code=401, detail="Invalid Letta API key")
    
    schedule_obj = OneTimeSchedule(**schedule.model_dump())
    schedule_dict = schedule_obj.model_dump(mode='json')
    file_path = get_onetime_schedule_path(schedule.api_key, schedule.execute_at, schedule_obj.id)
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
    
    # Save execution result if successful
    if result.get("success") and result.get("run_id"):
        save_execution_result(
            api_key=api_key,
            schedule_id=schedule_id,
            run_id=result["run_id"],
            schedule_type=schedule_type,
            agent_id=agent_id,
            message=message,
        )
    
    return result


def save_execution_result(api_key: str, schedule_id: str, run_id: str, schedule_type: str, agent_id: str, message: str):
    """Save execution result to results folder."""
    api_key_hash = get_api_key_hash(api_key)
    result_dir = f"{RESULTS_BASE}/{api_key_hash}"
    Path(result_dir).mkdir(parents=True, exist_ok=True)
    
    result_file = f"{result_dir}/{schedule_id}.json"
    
    result_data = {
        "schedule_id": schedule_id,
        "schedule_type": schedule_type,
        "run_id": run_id,
        "agent_id": agent_id,
        "message": message,
        "executed_at": datetime.utcnow().isoformat(),
    }
    
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
