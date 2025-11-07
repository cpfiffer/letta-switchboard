# Letta Schedules CLI

A command-line interface for managing scheduled messages for Letta AI agents.

## Features

- Create and manage recurring schedules with cron expressions
- Create and manage one-time schedules
- View execution results
- Beautiful table output
- Easy configuration management

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

### 2. Create a Recurring Schedule

```bash
letta-schedules recurring create \
  --agent-id agent-xxx \
  --message "Daily check-in" \
  --cron "0 9 * * *"
```

### 3. List Schedules

```bash
letta-schedules recurring list
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

## Configuration

The CLI stores configuration in `~/.letta-schedules/config.yaml`:

```yaml
api_key: sk-xxx...
base_url: https://letta--letta-schedules-api.modal.run
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
