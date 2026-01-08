# Letta Scheduling Dashboard

## ⚠️ Important Update: Now Using Letta's Native Scheduling

**Letta now provides built-in scheduling!** This project has been simplified to a web dashboard that calls Letta's API directly.

### What Changed?

- ✅ **Dashboard Updated** - Now calls Letta API directly from your browser
- ❌ **Old API Deprecated** - Backend scheduling endpoints return 410 Gone
- ➡️ **Migration Required** - Use Letta's native scheduling API

### Quick Links

🎛️ **Web Dashboard:** https://letta--switchboard-api.modal.run/dashboard  
📖 **Letta Scheduling Docs:** https://docs.letta.com/guides/agents/scheduling/  
💻 **GitHub:** https://github.com/cpfiffer/letta-switchboard

---

## Migration Guide

### For Dashboard Users

The dashboard now calls Letta's API directly! Just continue using it - no changes needed.

1. Visit https://letta--switchboard-api.modal.run/dashboard
2. Enter your Letta API key and agent ID
3. Create schedules as before

### For API Users

If you were calling the old Switchboard API, you need to migrate to Letta's native API:

**Old Endpoint (Deprecated):**
```bash
POST https://letta--switchboard-api.modal.run/schedules/one-time
{
  "agent_id": "agent-xxx",
  "execute_at": "2025-11-13T09:00:00Z",
  "message": "Hello",
  "role": "user"
}
```

**New Endpoint (Use This):**
```bash
POST https://api.letta.com/v1/agents/agent-xxx/schedule
{
  "schedule": {
    "type": "one-time",
    "scheduled_at": 1731499200000
  },
  "messages": [{
    "role": "user",
    "content": "Hello"
  }]
}
```

**Key Changes:**
- `execute_at` (ISO string) → `scheduled_at` (Unix milliseconds)
- `message` (string) → `messages` (array of message objects)
- Cron expressions unchanged (still 5-field format)

**Full Documentation:** https://docs.letta.com/guides/agents/scheduling/

---

## Quick Start

### Use the Web Dashboard

Visit **[https://letta--switchboard-api.modal.run/dashboard](https://letta--switchboard-api.modal.run/dashboard)**

1. Enter your Letta API key (stored in browser session only)
2. Enter your agent ID
3. View, create, and delete schedules
4. Dashboard calls Letta's API directly from your browser

Features:
- **Direct Letta API integration** - No backend needed
- **Timezone support** - Local browser time, UTC, or major timezones  
- **Simple interface** - Clean, easy-to-use dashboard
- **No installation** - Just visit the URL!

### Use Letta's API Directly

For programmatic access, use Letta's scheduling API:

**Create a one-time schedule:**
```bash
curl -X POST https://api.letta.com/v1/agents/agent-xxx/schedule \
  -H "Authorization: Bearer YOUR_LETTA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule": {
      "type": "one-time",
      "scheduled_at": 1731499200000
    },
    "messages": [{
      "role": "user",
      "content": "Hello!"
    }]
  }'
```

**Create a recurring schedule:**
```bash
curl -X POST https://api.letta.com/v1/agents/agent-xxx/schedule \
  -H "Authorization: Bearer YOUR_LETTA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule": {
      "type": "recurring",
      "cron_expression": "0 9 * * 1-5"
    },
    "messages": [{
      "role": "user",
      "content": "Daily standup"
    }]
  }'
```

**List schedules:**
```bash
curl https://api.letta.com/v1/agents/agent-xxx/schedule \
  -H "Authorization: Bearer YOUR_LETTA_API_KEY"
```

**Delete a schedule:**
```bash
curl -X DELETE https://api.letta.com/v1/agents/agent-xxx/schedule/SCHEDULE_ID \
  -H "Authorization: Bearer YOUR_LETTA_API_KEY"
```

**Full Documentation:** https://docs.letta.com/guides/agents/scheduling/

## What is This?

A simple web dashboard for managing Letta agent schedules. The dashboard calls Letta's native scheduling API directly from your browser.

### Features

✅ **Web Dashboard** - Clean interface for managing schedules  
✅ **Direct Letta Integration** - Calls Letta API from browser  
✅ **No Backend** - Pure client-side (except for hosting the HTML)  
✅ **Timezone Support** - Schedule in local time or UTC  
✅ **Free to Use** - Just visit the URL

### Why Use This Dashboard?

**Easy to Use**  
Simple interface for creating and managing Letta schedules without writing API calls.

**No Installation**  
Just visit the URL - no setup, no configuration, no CLI to install.

**Direct Letta API**  
Your schedules are stored and executed by Letta Cloud. Check execution history at https://app.letta.com

## How It Works

1. **Visit the dashboard** → https://letta--switchboard-api.modal.run/dashboard
2. **Enter credentials** → Your Letta API key and agent ID
3. **Create schedules** → Dashboard calls Letta API from your browser
4. **Letta executes** → Letta Cloud handles scheduling and execution
5. **Check results** → View execution history at https://app.letta.com

**Architecture:**
- Dashboard is pure client-side JavaScript
- API calls go directly to Letta (https://api.letta.com)
- No Switchboard backend involved in scheduling
- Your API key never leaves your browser (stored in session storage)

## Natural Language Examples

### One-Time Messages

```bash
# Relative time
--execute-at "in 5 minutes"
--execute-at "in 2 hours"
--execute-at "in 3 days"

# Tomorrow
--execute-at "tomorrow at 9am"
--execute-at "tomorrow at 14:30"

# Next weekday
--execute-at "next monday at 3pm"
--execute-at "next friday at 10:00"

# ISO 8601 (still works)
--execute-at "2025-11-12T19:30:00Z"
```

### Recurring Schedules

```bash
# Minutes
--cron "every 5 minutes"
--cron "every 30 minutes"

# Hourly/Daily
--cron "every hour"
--cron "daily at 9am"
--cron "daily at 14:30"

# Weekdays
--cron "every monday"
--cron "every friday at 3pm"
--cron "every weekday"     # Mon-Fri at 9am

# Traditional cron (still works)
--cron "*/5 * * * *"       # Every 5 minutes
```
```

This will test all endpoints (create, list, get, delete) for both recurring and one-time schedules.

**Features:**
- Validates API key before running
- Shows configuration at startup
- Tests create, list, get, and delete operations
- Pretty prints all responses

### Bash Test Script

```bash
./test_api.sh
```

Same functionality using curl commands.

**Example with inline variables:**
```bash
LETTA_API_KEY=sk-xxx LETTA_AGENT_ID=agent-yyy python test_api.py
```

## CLI Usage (Recommended)

The easiest way to interact with letta-switchboard is via the CLI:

```bash
# Send a message immediately
letta-switchboard send --agent-id agent-xxx --message "Hello!"

# Send a message later
letta-switchboard send --agent-id agent-xxx --message "Reminder" --execute-at "tomorrow at 9am"

# Create recurring schedule
letta-switchboard recurring create --agent-id agent-xxx --message "Daily standup" --cron "every weekday at 9am"

# List schedules
letta-switchboard onetime list
letta-switchboard recurring list

# View results
letta-switchboard results list
```

See [CLI Documentation](cli/README.md) for installation and full usage guide.

## API Usage

Base URL: `https://letta--schedules-api.modal.run`

### Authentication

All endpoints require Bearer token authentication using your Letta API key:

```bash
curl -H "Authorization: Bearer your-letta-api-key" https://your-modal-app.modal.run/schedules/recurring
```

**Security Model:**
- **API Key Validation**: All requests validate your API key against Letta's API (lightweight `list agents` call with `limit=1`)
- **Create endpoints**: Verify API key is valid before creating schedule
- **List endpoints**: Returns only schedules created with your API key
- **Get/Delete endpoints**: Returns 403 Forbidden if the schedule wasn't created with your API key
- **Privacy**: API keys are never returned in responses, only used for authentication and execution

**Error Codes:**
- `401 Unauthorized`: Invalid or expired Letta API key
- `403 Forbidden`: Valid API key, but trying to access someone else's schedule
- `404 Not Found`: Schedule doesn't exist

### Create Recurring Schedule

Schedule a message to be sent on a cron schedule:

```bash
curl -X POST https://your-modal-app.modal.run/schedules/recurring \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-123",
    "api_key": "your-letta-api-key",
    "cron": "0 9 * * *",
    "message": "Good morning! Time for your daily check-in.",
    "role": "user"
  }'
```

**Cron Format:** `minute hour day month day_of_week`
- `0 9 * * *` - Every day at 9:00 AM
- `*/15 * * * *` - Every 15 minutes
- `0 */2 * * *` - Every 2 hours
- `0 0 * * 0` - Every Sunday at midnight

### Create One-Time Schedule

Schedule a message for a specific time:

```bash
curl -X POST https://your-modal-app.modal.run/schedules/one-time \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-123",
    "api_key": "your-letta-api-key",
    "execute_at": "2025-11-07T14:30:00-05:00",
    "message": "Reminder: Meeting in 30 minutes",
    "role": "user"
  }'
```

**Timestamp Format:** ISO 8601 with timezone
- `2025-11-07T14:30:00-05:00` (EST)
- `2025-11-07T14:30:00Z` (UTC)

### List All Schedules

```bash
# List your recurring schedules
curl -H "Authorization: Bearer your-letta-api-key" \
  https://your-modal-app.modal.run/schedules/recurring

# List your one-time schedules
curl -H "Authorization: Bearer your-letta-api-key" \
  https://your-modal-app.modal.run/schedules/one-time
```

### Get Specific Schedule

```bash
# Get recurring schedule
curl -H "Authorization: Bearer your-letta-api-key" \
  https://your-modal-app.modal.run/schedules/recurring/{schedule_id}

# Get one-time schedule
curl -H "Authorization: Bearer your-letta-api-key" \
  https://your-modal-app.modal.run/schedules/one-time/{schedule_id}
```

### Delete Schedule

```bash
# Delete recurring schedule
curl -X DELETE -H "Authorization: Bearer your-letta-api-key" \
  https://your-modal-app.modal.run/schedules/recurring/{schedule_id}

# Delete one-time schedule
curl -X DELETE -H "Authorization: Bearer your-letta-api-key" \
  https://your-modal-app.modal.run/schedules/one-time/{schedule_id}
```

### Get Execution Results

```bash
# List all execution results
curl -H "Authorization: Bearer your-letta-api-key" \
  https://your-modal-app.modal.run/results

# Get result for specific schedule
curl -H "Authorization: Bearer your-letta-api-key" \
  https://your-modal-app.modal.run/results/{schedule_id}
```

**Result Format:**
```json
{
  "schedule_id": "uuid",
  "schedule_type": "recurring",
  "run_id": "run_abc123",
  "agent_id": "agent-123",
  "message": "The scheduled message",
  "executed_at": "2025-11-07T00:15:00"
}
```

**Note:** Results are stored when the message is queued to Letta. To check the actual run status, use the Letta API:
```bash
# Get the run_id from results
RESULT=$(curl -H "Authorization: Bearer your-letta-api-key" \
  https://your-modal-app.modal.run/results/{schedule_id})

RUN_ID=$(echo $RESULT | jq -r '.run_id')

# Check run status with Letta
curl -H "Authorization: Bearer your-letta-api-key" \
  https://api.letta.com/v1/runs/$RUN_ID
```

## Response Format

### Recurring Schedule Response
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "agent-123",
  "cron": "0 9 * * *",
  "message": "Good morning!",
  "role": "user",
  "created_at": "2025-11-06T10:00:00",
  "last_run": "2025-11-06T09:00:00"
}
```

**Note:** API keys are stored securely and never returned in responses.

### One-Time Schedule Response
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "agent-123",
  "execute_at": "2025-11-07T14:30:00-05:00",
  "message": "Reminder!",
  "role": "user",
  "created_at": "2025-11-06T10:00:00"
}
```

**Note:** 
- API keys are stored securely and never returned in responses
- Once executed, one-time schedules are deleted from storage (check `/results` endpoint for execution history)

## How It Works

1. **API receives schedule request** → Validates and stores as JSON in Modal Volume
2. **Cron job runs every minute** → Checks all schedules in Volume
3. **Due schedules identified** → Spawns async executor functions
4. **Executor verifies schedule exists** → Skips if schedule was deleted after spawn
5. **For one-time schedules** → Deletes schedule file immediately (prevents re-execution)
6. **Executor calls Letta API** → Sends message to specified agent
7. **Saves execution result** → Stores run_id and metadata in results folder
8. **For recurring schedules** → Updates `last_run` timestamp in schedule file

**Race Condition Prevention:**
- One-time schedules are **deleted before execution** (not after)
- If multiple executors spawn, only first one successfully deletes
- Second executor finds no file → skips gracefully
- Filesystem is source of truth: file exists = hasn't run yet

## Storage Structure

Schedules and execution results are stored in a hash-based directory structure:

```
/data/
├── schedules/
│   ├── recurring/
│   │   ├── {api_key_hash}/        # SHA256 hash of API key (first 16 chars)
│   │   │   ├── {uuid-1}.json.enc  # Encrypted schedule files
│   │   │   └── {uuid-2}.json.enc
│   │   └── {another_hash}/
│   │       └── {uuid-3}.json.enc
│   └── one-time/
│       ├── 2025-11-06/             # Date bucket
│       │   ├── 14/                 # Hour bucket (00-23)
│       │   │   ├── {api_key_hash}/
│       │   │   │   └── {uuid}.json.enc
│       │   │   └── {another_hash}/
│       │   │       └── {uuid}.json.enc
│       │   └── 15/
│       └── 2025-11-07/
└── results/
    ├── {api_key_hash}/
    │   ├── {schedule_uuid}.json.enc  # Execution results with run_id
    │   └── {schedule_uuid}.json.enc
    └── {another_hash}/
```

**Security Features:**
- All schedule files are encrypted at rest using Fernet (AES-128-CBC)
- API keys never stored in plaintext
- User isolation via hash-based directories
- Time-based bucketing for efficient queries

**Performance Benefits:**
- **Recurring schedules:** O(user's schedules) instead of O(all schedules)
- **One-time schedules:** O(schedules in current hour) instead of O(all schedules)
- Only checks relevant time buckets during cron execution
- Automatic cleanup: Empty directories are removed after each cron run

## Monitoring

View logs in Modal dashboard:
```bash
modal app logs letta-switchboard
```

Or watch logs in real-time:
```bash
modal app logs letta-switchboard --follow
```

## Limitations

- **Minimum granularity:** 1 minute (cron runs every minute)
- **Timezone handling:** One-time schedules support timezones; recurring schedules run in UTC
- **Authentication:** Bearer token authentication with validation against Letta API
- **Encryption key management:** Single master key for all schedules (consider key rotation strategy for production)

## Future Improvements

- [ ] Encryption key rotation mechanism
- [ ] Execution history/logs API endpoint
- [ ] Rate limiting per user
- [ ] Email/webhook notifications on failures
- [ ] Pagination for list endpoints
- [ ] Timezone support for recurring schedules
- [ ] Schedule validation (max schedules per user)
- [ ] Cleanup of old date buckets (>7 days) to prevent unbounded growth

## Costs

Modal pricing (as of 2024):
- **Compute:** ~$0.000162/second for basic CPU
- **Volume storage:** ~$0.10/GB/month
- **Estimated monthly cost:** $5-10 for moderate usage (hundreds of schedules)

Free tier: 30 credits/month (~$30 value)

---

## Self-Hosting

Want to run your own instance? Switchboard is fully self-hostable on Modal.

### Prerequisites

1. Clone the repository:
```bash
git clone https://github.com/cpfiffer/letta-switchboard.git
cd letta-switchboard
```

2. Install Modal CLI:
```bash
pip install modal
modal setup
```

### Deploy Your Instance

**1. Set up encryption (required):**
```bash
# Automated setup
./setup_encryption.sh

# Or manually
ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
echo "Save this key: $ENCRYPTION_KEY"
modal secret create letta-switchboard-encryption \
  LETTA_SWITCHBOARD_ENCRYPTION_KEY="$ENCRYPTION_KEY"
```

**2. Deploy to Modal:**
```bash
modal deploy app.py
```

**3. Get your API URL:**
```bash
modal app list
# Look for 'switchboard' and note the URL
```

**4. Configure CLI to use your instance:**
```bash
letta-switchboard config set-url https://your-instance.modal.run
```

### Local Development

Run locally with hot reloading:
```bash
# Enable dev mode (no encryption)
export LETTA_SWITCHBOARD_DEV_MODE=true

# Start local server
modal serve app.py
```

**Dev Mode Features:**
- Files stored in plaintext JSON (easy to inspect)
- No encryption overhead
- Perfect for debugging
- Auto-reload on code changes

**View files in dev mode:**
```bash
# View a schedule
cat /tmp/letta-switchboard-volume/schedules/recurring/abc123/uuid.json | jq

# List all schedules
ls -la /tmp/letta-switchboard-volume/schedules/
```

### Testing Your Instance

Set environment variables:
```bash
export LETTA_API_KEY="sk-..."
export LETTA_AGENT_ID="agent-xxx"
export LETTA_SWITCHBOARD_URL="https://your-instance.modal.run"
```

Run tests:
```bash
# Python test suite
python test_api.py

# Bash test script
./test_api.sh

# Unit tests
pytest -m "not e2e"

# Full E2E tests (requires modal serve running)
pytest
```

### Cost Estimate

Running your own instance on Modal:
- **Free tier:** ~$30/month of free credits
- **API requests:** Free (minimal compute)
- **Cron job:** Runs every minute (~43,000 times/month)
- **Storage:** First 1GB free, then $0.10/GB/month
- **Expected cost:** $0-5/month for personal use

The hosted service at `letta--switchboard-api.modal.run` is free to use!

---

## License

MIT
