from letta_client import Letta, MessageCreate, TextContent
import logging
import json

logger = logging.getLogger(__name__)


def parse_error(e: Exception) -> dict:
    """Extract error message and metadata from exceptions."""
    error_str = str(e)
    result = {"message": error_str, "permanent": False}

    # Check for common timeout errors
    if "timed out" in error_str.lower():
        result["message"] = "Request timed out"
        return result

    # Check for connection errors
    if "connection" in error_str.lower() and "error" in error_str.lower():
        result["message"] = "Connection error"
        return result

    # Try to extract body from HTTP errors (letta_client format)
    if "body:" in error_str:
        try:
            # Extract the body part
            body_start = error_str.find("body:") + 5
            body_str = error_str[body_start:].strip()
            body = eval(body_str)  # Safe here since it's from our own API response

            if isinstance(body, dict):
                error_msg = body.get("error", "")
                reasons = body.get("reasons", [])
                status_code = None

                # Try to get status code
                if "status_code:" in error_str:
                    try:
                        sc_start = error_str.find("status_code:") + 12
                        sc_end = error_str.find(",", sc_start)
                        status_code = int(error_str[sc_start:sc_end].strip())
                    except (ValueError, IndexError):
                        pass

                # For auth errors - permanent, should remove schedule
                if status_code in (401, 403):
                    result["message"] = f"Authentication failed: {error_msg}"
                    result["permanent"] = True
                    return result

                # For not found - permanent, should remove schedule
                if status_code == 404 or "not-found" in str(reasons).lower():
                    result["message"] = "Agent not found"
                    result["permanent"] = True
                    return result

                # For rate limits - transient, keep schedule
                if status_code == 429 or error_msg == "Rate limited":
                    if reasons:
                        result["message"] = f"Rate limited: {', '.join(reasons)}"
                    else:
                        result["message"] = "Rate limited"
                    return result

                # Generic API error
                if error_msg:
                    if reasons:
                        result["message"] = f"{error_msg}: {', '.join(reasons)}"
                    else:
                        result["message"] = error_msg
                    return result
        except Exception:
            pass

    # Fallback: truncate if too long
    if len(error_str) > 100:
        result["message"] = error_str[:100] + "..."

    return result


def validate_api_key(api_key: str) -> bool:
    try:
        client = Letta(token=api_key)
        client.agents.list(limit=1)
        return True
    except Exception as e:
        error_info = parse_error(e)
        logger.error(f"API key validation failed: {error_info['message']}")
        return False


async def execute_letta_message(agent_id: str, api_key: str, message: str, role: str = "user"):
    try:
        client = Letta(token=api_key)

        # Use create_async() with proper MessageCreate objects
        run = client.agents.messages.create_async(
            agent_id=agent_id,
            messages=[
                MessageCreate(
                    role=role,
                    content=[
                        TextContent(text=message)
                    ]
                )
            ]
        )

        logger.info(f"Successfully queued message for agent {agent_id}, run_id: {run.id}")
        return {"success": True, "run_id": run.id}

    except Exception as e:
        error_info = parse_error(e)
        logger.error(f"Failed to send message to agent {agent_id}: {error_info['message']}")
        return {
            "success": False,
            "error": error_info["message"],
            "permanent": error_info["permanent"]
        }
