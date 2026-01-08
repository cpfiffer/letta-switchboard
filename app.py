import modal
from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from pathlib import Path

app = modal.App("switchboard")

# Simple image that just needs FastAPI
image = (
    modal.Image.debian_slim()
    .pip_install("fastapi")
    .add_local_file("dashboard.html", "/root/dashboard.html")
)

web_app = FastAPI()

# Deprecation message
DEPRECATION_RESPONSE = {
    "error": "API Deprecated",
    "message": "Letta now provides native scheduling. This API has been deprecated.",
    "documentation": "https://docs.letta.com/guides/agents/scheduling/",
    "migration_guide": {
        "old_api": "https://letta--switchboard-api.modal.run/schedules/*",
        "new_api": "https://api.letta.com/v1/agents/{agent_id}/schedule",
        "changes": [
            "execute_at: ISO string → scheduled_at: Unix milliseconds",
            "message: string → messages: [{role, content}]",
            "Cron expressions: same 5-field format (no change)",
            "API calls now go directly to Letta (no Switchboard backend)"
        ],
        "examples": {
            "one_time": {
                "old": {
                    "POST": "/schedules/one-time",
                    "body": {"agent_id": "agent-xxx", "execute_at": "2025-11-13T09:00:00Z", "message": "Hello", "role": "user"}
                },
                "new": {
                    "POST": "/v1/agents/{agent_id}/schedule",
                    "body": {"schedule": {"type": "one-time", "scheduled_at": 1731499200000}, "messages": [{"role": "user", "content": "Hello"}]}
                }
            },
            "recurring": {
                "old": {
                    "POST": "/schedules/recurring",
                    "body": {"agent_id": "agent-xxx", "cron": "0 9 * * *", "message": "Daily", "role": "user"}
                },
                "new": {
                    "POST": "/v1/agents/{agent_id}/schedule",
                    "body": {"schedule": {"type": "recurring", "cron_expression": "0 9 * * *"}, "messages": [{"role": "user", "content": "Daily"}]}
                }
            }
        }
    },
    "dashboard": {
        "message": "The web dashboard has been updated to call Letta's API directly",
        "url": "/dashboard"
    }
}

# Serve the dashboard
@web_app.get("/dashboard")
@web_app.get("/")
async def serve_dashboard():
    """Serve the updated dashboard that calls Letta API directly."""
    with open("/root/dashboard.html", "r") as f:
        return HTMLResponse(content=f.read())

# Deprecated endpoints - return 410 Gone
@web_app.post("/schedules/one-time")
@web_app.get("/schedules/one-time")
@web_app.get("/schedules/one-time/{schedule_id}")
@web_app.delete("/schedules/one-time/{schedule_id}")
async def deprecated_onetime():
    """Old one-time schedule endpoints - deprecated."""
    return JSONResponse(
        status_code=410,  # 410 Gone
        content=DEPRECATION_RESPONSE
    )

@web_app.post("/schedules/recurring")
@web_app.get("/schedules/recurring")
@web_app.get("/schedules/recurring/{schedule_id}")
@web_app.delete("/schedules/recurring/{schedule_id}")
async def deprecated_recurring():
    """Old recurring schedule endpoints - deprecated."""
    return JSONResponse(
        status_code=410,  # 410 Gone
        content=DEPRECATION_RESPONSE
    )

@web_app.get("/results")
@web_app.get("/results/{schedule_id}")
async def deprecated_results():
    """Old results endpoints - deprecated."""
    return JSONResponse(
        status_code=410,  # 410 Gone
        content={
            **DEPRECATION_RESPONSE,
            "note": "Execution results are now tracked in Letta Cloud. Check your agent's run history at https://app.letta.com"
        }
    )

# Health check
@web_app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "message": "Dashboard service running"}

# Deploy the app
@app.function(
    image=image,
    secrets=[],  # No secrets needed anymore!
    min_containers=1,  # Keep one instance warm
)
@modal.asgi_app()
def api():
    """Serve the FastAPI app."""
    return web_app
