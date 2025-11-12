# Letta Schedules CLI

A command-line interface for sending messages to Letta AI agents and managing schedules.

## Features

- **Send messages to agents** - Immediately or scheduled for later
- **Natural language scheduling** - "in 5 minutes", "tomorrow at 9am", "every weekday"
- **Recurring schedules** - Daily check-ins, weekly summaries, custom patterns
- **View execution results** - Track message delivery and run IDs
- **Beautiful output** - Clean tables and colored success messages
- **Easy configuration** - One-time API key setup

## Installation

### From Source

```bash
# Clone the repository
cd cli

# Build the binary
go build -o letta-schedules

# Move to your PATH (optional)
sudo mv letta-schedules /usr/local/bin/
```

### Using Go Install

```bash
go install github.com/letta/letta-schedules-cli@latest
```

### Cross-Platform Build

```bash
# macOS
GOOS=darwin GOARCH=amd64 go build -o letta-schedules-darwin-amd64
GOOS=darwin GOARCH=arm64 go build -o letta-schedules-darwin-arm64

# Linux
GOOS=linux GOARCH=amd64 go build -o letta-schedules-linux-amd64
GOOS=linux GOARCH=arm64 go build -o letta-schedules-linux-arm64

# Windows
GOOS=windows GOARCH=amd64 go build -o letta-schedules-windows-amd64.exe
```

## Quick Start

### 1. Configure API Credentials

```bash
# Set your Letta API key
letta-schedules config set-api-key sk-xxx...

# Set the API URL (optional, defaults to Modal deployment)
letta-schedules config set-url https://your-api-url.com

# View current configuration
letta-schedules config show
```

### 2. Send a Message to an Agent

```bash
# Send immediately
letta-schedules send \
  --agent-id agent-xxx \
  --message "Hello! How are you doing?"

# Or schedule for later
letta-schedules send \
  --agent-id agent-xxx \
  --message "Reminder: Follow up on project" \
  --execute-at "tomorrow at 9am"
```

### 3. Create a Recurring Schedule

```bash
letta-schedules recurring create \
  --agent-id agent-xxx \
  --message "Daily check-in" \
  --cron "every weekday at 9am"
```

### 4. List Schedules

```bash
letta-schedules onetime list
letta-schedules recurring list
```

## Natural Language Support

The CLI supports natural language input for both time expressions and cron schedules, making it easy to create schedules without memorizing syntax!

### One-Time Schedules (Timestamps)

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

# ISO 8601 (still supported)
--execute-at "2025-11-12T19:30:00Z"
```

### Recurring Schedules (Cron Expressions)

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
--cron "every weekend"     # Sat-Sun at 9am

# Weekly/Monthly
--cron "weekly"            # Every Monday at 9am
--cron "monthly"           # 1st of month at 9am

# Traditional cron (still supported)
--cron "*/5 * * * *"       # Every 5 minutes
--cron "0 9 * * 1-5"       # Weekdays at 9am
```

## Usage

### Configuration Commands

```bash
# Set API key
letta-schedules config set-api-key <key>

# Set base URL
letta-schedules config set-url <url>

# Show configuration
letta-schedules config show
```

### Recurring Schedules

```bash
# Create a recurring schedule
letta-schedules recurring create \
  --agent-id <agent-id> \
  --message "Your message" \
  --cron "0 9 * * *" \
  --role user

# List all recurring schedules
letta-schedules recurring list

# Get details of a specific schedule
letta-schedules recurring get <schedule-id>

# Delete a schedule
letta-schedules recurring delete <schedule-id>
```

#### Cron Expression Examples

- `0 9 * * *` - Every day at 9:00 AM
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 1` - Every Monday at midnight
- `*/30 * * * *` - Every 30 minutes

### One-Time Schedules

```bash
# Create a one-time schedule
letta-schedules onetime create \
  --agent-id <agent-id> \
  --message "Reminder message" \
  --execute-at "2025-11-07T10:00:00Z" \
  --role user

# List all one-time schedules
letta-schedules onetime list

# Get details of a specific schedule
letta-schedules onetime get <schedule-id>

# Delete a schedule
letta-schedules onetime delete <schedule-id>
```

### Execution Results

```bash
# List all execution results
letta-schedules results list

# Get result for a specific schedule
letta-schedules results get <schedule-id>
```

## Sending Messages (One-Time Schedules)

The `send` (alias: `onetime create`) command allows you to send messages to agents immediately or scheduled for later.

### Send Immediately

```bash
# Send a message right now (executes within 1 minute)
letta-schedules send \
  --agent-id agent-xxx \
  --message "Hey, how's the project going?"
```

### Schedule for Later

```bash
# Relative time
letta-schedules send \
  --agent-id agent-xxx \
  --message "Follow up reminder" \
  --execute-at "in 2 hours"

# Specific day/time
letta-schedules send \
  --agent-id agent-xxx \
  --message "Weekly summary time!" \
  --execute-at "next monday at 10am"
```

### Future: Cross-Server Messaging

**Coming soon:** Permission system to allow messaging agents across different Letta servers.

This will enable:
- Send messages to agents on any Letta instance (cloud or self-hosted)
- Permission tables to control who can message which agents
- Cross-organization agent communication
- Federated agent networks

## Configuration

The CLI stores configuration in `~/.letta-schedules/config.yaml`:

```yaml
api_key: sk-xxx...
base_url: https://letta--schedules-api.modal.run
```

## Examples

### Daily Agent Check-in

```bash
letta-schedules recurring create \
  --agent-id agent-123 \
  --message "Good morning! Please provide a daily summary." \
  --cron "0 9 * * *"
```

### Hourly Status Update

```bash
letta-schedules recurring create \
  --agent-id agent-123 \
  --message "Status update please" \
  --cron "0 * * * *"
```

### One-Time Reminder

```bash
letta-schedules onetime create \
  --agent-id agent-123 \
  --message "Meeting in 1 hour" \
  --execute-at "2025-11-07T14:00:00Z"
```

## Development

### Prerequisites

- Go 1.21+

### Build

```bash
go build -o letta-schedules
```

### Run Tests

```bash
go test ./...
```

### Update Dependencies

```bash
go mod tidy
```

## License

MIT
