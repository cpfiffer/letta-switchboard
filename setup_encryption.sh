#!/bin/bash

echo "=== Letta Schedules Encryption Setup ==="
echo ""

# Check if modal is installed
if ! command -v modal &> /dev/null; then
    echo "ERROR: modal CLI not found. Install with: pip install modal"
    exit 1
fi

# Check if user is authenticated
if ! modal profile list &> /dev/null; then
    echo "ERROR: Not authenticated with Modal. Run: modal setup"
    exit 1
fi

echo "Generating encryption key..."
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

if [ -z "$ENCRYPTION_KEY" ]; then
    echo "ERROR: Failed to generate encryption key"
    exit 1
fi

echo "Generated encryption key: ${ENCRYPTION_KEY:0:20}..."
echo ""

echo "Creating Modal secret 'letta-switchboard-encryption'..."

# Check if secret already exists
if modal secret list | grep -q "letta-switchboard-encryption"; then
    echo "WARNING: Secret 'letta-switchboard-encryption' already exists."
    echo "Delete it first with: modal secret delete letta-switchboard-encryption"
    exit 1
fi

# Create the secret
modal secret create letta-switchboard-encryption LETTA_SWITCHBOARD_ENCRYPTION_KEY="$ENCRYPTION_KEY" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Success! Encryption secret created."
    echo ""
    echo "IMPORTANT: Save this key securely!"
    echo "Encryption key: $ENCRYPTION_KEY"
    echo ""
    echo "If you lose this key, all encrypted schedules will be unrecoverable."
    echo ""
    echo "Next step: modal deploy app.py"
else
    echo ""
    echo "❌ Failed to create secret. Error above."
    exit 1
fi
