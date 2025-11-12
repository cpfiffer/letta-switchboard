# Letta Switchboard

A serverless scheduling service for Letta agents built on Modal. Schedule recurring (cron-based) or one-time messages to be sent to your Letta agents at specified times.

## Architecture

- **FastAPI** - REST API for managing schedules
- **Modal Cron** - Runs every minute to check and execute due schedules
- **Modal Volume** - Persistent JSON storage for schedule definitions
- **Letta Client** - Executes scheduled messages via Letta API

## Features

- ✅ Schedule recurring messages with cron expressions
- ✅ Schedule one-time messages with ISO 8601 timestamps
- ✅ Full CRUD operations for schedules
- ✅ Timezone support for one-time schedules
- ✅ Automatic cleanup of executed one-time schedules
- ✅ Async execution via Modal

## Installation

1. Clone the repository:
```bash
cd letta-switchboard
```

2. Install Modal CLI:
```bash
pip install modal
```

3. Authenticate with Modal:
```bash
modal setup
```

## Deployment

### 1. Set Encryption Key (Required)

**Option A: Automated Setup Script**

```bash
./setup_encryption.sh
```

This will:
- Generate a secure encryption key
- Create the Modal secret
- Display the key for safekeeping

**Option B: Manual Setup**

```bash
# Generate a new encryption key
ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Display and save the key
echo "Your encryption key: $ENCRYPTION_KEY"

# Create Modal secret
modal secret create letta-switchboard-encryption \
  LETTA_SCHEDULES_ENCRYPTION_KEY="$ENCRYPTION_KEY"
```

**⚠️ CRITICAL:** Save the encryption key securely! If lost, all encrypted schedules become unrecoverable.

### 2. Deploy to Modal

```bash
modal deploy app.py
```

This will:
- Create the Modal app and volume
- Set up the scheduler cron job (runs every minute)
- Deploy the FastAPI endpoints with encryption

### 3. Get Your API URL

```bash
modal app list
```

Look for `letta-switchboard` and note the API endpoint URL.

## Local Development

Run locally with hot reloading:
```bash
# Enable dev mode (no encryption, easier debugging)
export LETTA_SCHEDULES_DEV_MODE=true
export LETTA_SCHEDULES_ENCRYPTION_KEY="any-value-ignored-in-dev-mode"

modal serve app.py
```

This starts a local development server with auto-reload on file changes.

**Dev Mode Features:**
- 🔓 Files stored in **plaintext JSON** (no encryption)
- Easy to inspect with `cat`, `jq`, etc.
- Clearly logged: `DEV MODE: Encryption disabled`
- Perfect for local debugging

**Important:** Never use dev mode in production! Set `LETTA_SCHEDULES_DEV_MODE=false` or leave unset for production.

**Inspecting files in dev mode:**
```bash
# View a schedule
cat /tmp/letta-switchboard-volume/schedules/recurring/abc123/uuid.json | jq

# View an execution result
cat /tmp/letta-switchboard-volume/results/abc123/uuid.json | jq

# List all schedules for a user
ls -la /tmp/letta-switchboard-volume/schedules/recurring/abc123/
```

## Testing

Two test scripts are provided. Both require environment variables:

### Setup Environment Variables

```bash
export LETTA_API_KEY="sk-..."              # Required: Your valid Letta API key
export LETTA_AGENT_ID="agent-xxx"          # Optional: Agent to test with
export LETTA_SCHEDULES_URL="https://..."   # Optional: Your Modal app URL
```

**Important:** The API key must be valid and will be validated against Letta's API during testing.

### Python Test Script

```bash
python test_api.py
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

## License

MIT
