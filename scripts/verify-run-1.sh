#!/usr/bin/env bash
# OpenDoor Relay - Run 1 Verification Script (POSIX Bash)
set -euo pipefail

BASE_URL="http://127.0.0.1:8000"

echo "=========================================================="
echo " OpenDoor Relay — Run 1 Automated Hero Path Verification "
echo "=========================================================="

# Check health
echo "[1/8] Verifying GET /health..."
HEALTH=$(curl -s "$BASE_URL/health")
echo "$HEALTH" | grep -q '"status":"healthy"'

# Reset demo
echo "[2/8] Resetting synthetic demo data..."
curl -s -X POST "$BASE_URL/api/demo/reset" > /dev/null

# Trigger failure
echo "[3/8] Triggering Provider A failure..."
FAILURE=$(curl -s -X POST "$BASE_URL/api/cases/case-synthetic-001/provider-failure" \
  -H "Content-Type: application/json" \
  -d '{"trigger_text": "Provider A declared sudden unavailability 45m before cutoff"}')
echo "$FAILURE" | grep -q '"state":"REPLACEMENT_PENDING"'
echo "$FAILURE" | grep -q '"provider_id":"prov-b-beacon"'

# Extract token
TOKEN=$(echo "$FAILURE" | grep -o '"response_url":"[^"]*' | awk -F'/' '{print $NF}')

# Validate offer
echo "[4/8] Validating provider offer details via token..."
curl -s "$BASE_URL/api/provider/offer/$TOKEN" | grep -q "Beacon Live Access"

# Provider accepts
echo "[5/8] Recording Provider B acceptance via token..."
RESPOND=$(curl -s -X POST "$BASE_URL/api/provider/respond/$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "ACCEPT", "response_text": "Accepted"}')
echo "$RESPOND" | grep -q '"offer_state":"ACCEPTED"'
echo "$RESPOND" | grep -q '"case_state":"ATTENDEE_CONFIRMATION_PENDING"'

# Replay for idempotency
echo "[6/8] Testing duplicate response idempotency..."
REPLAY=$(curl -s -X POST "$BASE_URL/api/provider/respond/$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "ACCEPT", "response_text": "Accepted"}')
echo "$REPLAY" | grep -q '"offer_state":"ACCEPTED"'

# Attendee confirms
echo "[7/8] Recording attendee confirmation..."
CONFIRM=$(curl -s -X POST "$BASE_URL/api/cases/case-synthetic-001/attendee-confirm")
echo "$CONFIRM" | grep -q '"state":"ATTENDEE_CONFIRMED"'

# Check timeline
echo "[8/9] Verifying audit timeline and headline metrics..."
TIMELINE=$(curl -s "$BASE_URL/api/cases/case-synthetic-001/timeline")
echo "$TIMELINE" | grep -q '"current_state":"ATTENDEE_CONFIRMED"'
echo "$TIMELINE" | grep -q '"time_to_confirmed_seconds"'

# Check evaluation endpoint
echo "[9/9] Verifying evaluation reports NOT_GENERATED for Run 1..."
EVAL_STATUS=$(curl -s "$BASE_URL/api/evaluation/latest")
echo "$EVAL_STATUS" | grep -q '"status":"NOT_GENERATED"'
echo "$EVAL_STATUS" | grep -q '"run":"RUN_1"'

echo "=========================================================="
echo " VERIFICATION SUCCESS: Run 1 Local Hero Path PASSED!     "
echo "=========================================================="
