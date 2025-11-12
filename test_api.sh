#!/bin/bash

BASE_URL="${LETTA_SWITCHBOARD_URL:-https://your-modal-app-url.modal.run}"
AGENT_ID="${LETTA_AGENT_ID:-your-agent-id}"
API_KEY="${LETTA_API_KEY}"

if [ -z "$API_KEY" ]; then
  echo "ERROR: LETTA_API_KEY environment variable not set!"
  echo "This must be a VALID Letta API key that will be validated against Letta's API."
  echo "Set it with: export LETTA_API_KEY=sk-..."
  exit 1
fi

echo "========================================"
echo "Letta Schedules API Test (curl)"
echo "========================================"
echo "Base URL: $BASE_URL"
echo "Agent ID: $AGENT_ID"
echo "API Key: ${API_KEY:0:20}..."
echo ""

echo "1. Creating recurring schedule (every 5 minutes)..."
RECURRING_RESPONSE=$(curl -s -X POST "$BASE_URL/schedules/recurring" \
  -H "Content-Type: application/json" \
  -d "{
    \"agent_id\": \"$AGENT_ID\",
    \"api_key\": \"$API_KEY\",
    \"cron\": \"*/5 * * * *\",
    \"message\": \"Test recurring message\",
    \"role\": \"user\"
  }")

echo "$RECURRING_RESPONSE" | python3 -m json.tool
RECURRING_ID=$(echo "$RECURRING_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
echo "Recurring Schedule ID: $RECURRING_ID"
echo ""

echo "2. Creating one-time schedule (2 minutes from now)..."
EXECUTE_AT=$(python3 -c "from datetime import datetime, timedelta, timezone; print((datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat())")
ONETIME_RESPONSE=$(curl -s -X POST "$BASE_URL/schedules/one-time" \
  -H "Content-Type: application/json" \
  -d "{
    \"agent_id\": \"$AGENT_ID\",
    \"api_key\": \"$API_KEY\",
    \"execute_at\": \"$EXECUTE_AT\",
    \"message\": \"Test one-time message\",
    \"role\": \"user\"
  }")

echo "$ONETIME_RESPONSE" | python3 -m json.tool
ONETIME_ID=$(echo "$ONETIME_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
echo "One-Time Schedule ID: $ONETIME_ID"
echo ""

echo "3. Listing all recurring schedules..."
curl -s -H "Authorization: Bearer $API_KEY" "$BASE_URL/schedules/recurring" | python3 -m json.tool
echo ""

echo "4. Listing all one-time schedules..."
curl -s -H "Authorization: Bearer $API_KEY" "$BASE_URL/schedules/one-time" | python3 -m json.tool
echo ""

if [ ! -z "$RECURRING_ID" ]; then
  echo "5. Getting specific recurring schedule..."
  curl -s -H "Authorization: Bearer $API_KEY" "$BASE_URL/schedules/recurring/$RECURRING_ID" | python3 -m json.tool
  echo ""
fi

if [ ! -z "$ONETIME_ID" ]; then
  echo "6. Getting specific one-time schedule..."
  curl -s -H "Authorization: Bearer $API_KEY" "$BASE_URL/schedules/one-time/$ONETIME_ID" | python3 -m json.tool
  echo ""
fi

echo "7. Listing execution results..."
curl -s -H "Authorization: Bearer $API_KEY" "$BASE_URL/results" | python3 -m json.tool
echo ""

if [ ! -z "$RECURRING_ID" ]; then
  echo "8. Getting execution result for recurring schedule..."
  curl -s -H "Authorization: Bearer $API_KEY" "$BASE_URL/results/$RECURRING_ID" | python3 -m json.tool
  echo ""
fi

if [ ! -z "$ONETIME_ID" ]; then
  echo "9. Getting execution result for one-time schedule..."
  curl -s -H "Authorization: Bearer $API_KEY" "$BASE_URL/results/$ONETIME_ID" | python3 -m json.tool
  echo ""
fi

read -p "Press Enter to delete test schedules..."

if [ ! -z "$RECURRING_ID" ]; then
  echo "Deleting recurring schedule..."
  curl -s -X DELETE -H "Authorization: Bearer $API_KEY" "$BASE_URL/schedules/recurring/$RECURRING_ID" | python3 -m json.tool
  echo ""
fi

if [ ! -z "$ONETIME_ID" ]; then
  echo "Deleting one-time schedule..."
  curl -s -X DELETE -H "Authorization: Bearer $API_KEY" "$BASE_URL/schedules/one-time/$ONETIME_ID" | python3 -m json.tool
  echo ""
fi

echo "Final results after deletion..."
curl -s -H "Authorization: Bearer $API_KEY" "$BASE_URL/results" | python3 -m json.tool
echo ""

echo "========================================"
echo "Test complete!"
echo "========================================"
echo ""
echo "Note: Execution results remain even after schedules are deleted."
echo "Check run status at: https://api.letta.com/v1/runs/{run_id}"
