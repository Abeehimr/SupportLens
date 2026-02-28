#!/usr/bin/env bash
# ── SupportLens end-to-end test ──────────────────────────────────────────────
# Runs against a live backend at BACKEND_URL (default: http://localhost:8000).
# Exits 0 if all checks pass, 1 on first failure.
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
PASS_COUNT=0
FAIL_COUNT=0

# ── colors ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ── helpers ──────────────────────────────────────────────────────────────────
log_pass() { echo -e "  ${GREEN}[PASS]${NC} $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
log_fail() { echo -e "  ${RED}[FAIL]${NC} $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }
log_info() { echo -e "  ${CYAN}[INFO]${NC} $1"; }
log_section() { echo -e "\n${YELLOW}[$1]${NC} $2"; }

check_status() {
    local label="$1" url="$2" expected_code="$3"
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [ "$code" = "$expected_code" ]; then
        log_pass "$label (HTTP $code)"
    else
        log_fail "$label -- expected $expected_code, got $code"
    fi
}

check_json_field() {
    local label="$1" json="$2" field="$3" expected="$4"
    local actual
    actual=$(echo "$json" | python3 -c "import sys,json; print(json.load(sys.stdin)$field)" 2>/dev/null || echo "__PARSE_ERROR__")
    if [ "$actual" = "$expected" ]; then
        log_pass "$label ($field = $actual)"
    else
        log_fail "$label -- expected $field=$expected, got $actual"
    fi
}

# ── wait for backend ────────────────────────────────────────────────────────
echo -e "${CYAN}[WAIT]${NC} Waiting for backend at $BACKEND_URL ..."
for i in $(seq 1 30); do
    if curl -sf "$BACKEND_URL/health" > /dev/null 2>&1; then
        log_info "Backend ready after ${i}s"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo -e "${RED}[FAIL]${NC} Backend did not become ready in 30s"; exit 1
    fi
    sleep 1
done

# ── 1. Health endpoint ──────────────────────────────────────────────────────
log_section "1" "Health endpoint"
HEALTH=$(curl -sf "$BACKEND_URL/health")
APP_STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "__PARSE_ERROR__")
# Accept both "healthy" (LLM key present) and "degraded" (no LLM key, fallback mode).
# Only "unhealthy" (DB down) is a real failure.
if [ "$APP_STATUS" = "healthy" ] || [ "$APP_STATUS" = "degraded" ]; then
    log_pass "App status = $APP_STATUS"
else
    log_fail "App status -- expected healthy or degraded, got $APP_STATUS"
fi
check_json_field "DB status"  "$HEALTH" "['database']['status']" "up"

# ── 2. Get baseline analytics ──────────────────────────────────────────────
log_section "2" "Baseline analytics"
ANALYTICS_BEFORE=$(curl -sf "$BACKEND_URL/analytics")
TOTAL_BEFORE=$(echo "$ANALYTICS_BEFORE" | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])")
log_info "Baseline total: $TOTAL_BEFORE"

# ── 3. Create a trace via POST /chat ────────────────────────────────────────
log_section "3" "POST /chat"
CHAT=$(curl -sf -X POST "$BACKEND_URL/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "I need a refund for my last payment"}')
CHAT_ID=$(echo "$CHAT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
BOT_RESP=$(echo "$CHAT" | python3 -c "import sys,json; print(json.load(sys.stdin)['bot_response'])" 2>/dev/null || echo "")
CATEGORY=$(echo "$CHAT" | python3 -c "import sys,json; print(json.load(sys.stdin)['category'])" 2>/dev/null || echo "")

if [ -n "$CHAT_ID" ]; then
    log_pass "Chat returned id=$CHAT_ID"
else
    log_fail "Chat did not return an id"
fi

if [ -n "$BOT_RESP" ]; then
    log_pass "Chat returned a bot_response"
else
    log_fail "Chat did not return a bot_response"
fi

log_info "Category: $CATEGORY"

# ── 4. Verify analytics total incremented ──────────────────────────────────
log_section "4" "Analytics after chat"
ANALYTICS_AFTER=$(curl -sf "$BACKEND_URL/analytics")
TOTAL_AFTER=$(echo "$ANALYTICS_AFTER" | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])")
EXPECTED=$((TOTAL_BEFORE + 1))
if [ "$TOTAL_AFTER" -eq "$EXPECTED" ]; then
    log_pass "Total incremented ($TOTAL_BEFORE -> $TOTAL_AFTER)"
else
    log_fail "Total did not increment -- expected $EXPECTED, got $TOTAL_AFTER"
fi

# ── 5. Verify trace appears in GET /traces ──────────────────────────────────
log_section "5" "GET /traces"
check_status "GET /traces" "$BACKEND_URL/traces" "200"

FOUND=$(curl -sf "$BACKEND_URL/traces" | python3 -c "
import sys, json
traces = json.load(sys.stdin)
print('yes' if any(t['id'] == '$CHAT_ID' for t in traces) else 'no')
")
if [ "$FOUND" = "yes" ]; then
    log_pass "New trace $CHAT_ID found in /traces"
else
    log_fail "New trace $CHAT_ID NOT found in /traces"
fi

# ── 6. Category filter ──────────────────────────────────────────────────────
log_section "6" "Category filter"
if [ -n "$CATEGORY" ] && [ "$CATEGORY" != "LLM_UNAVAILABLE" ]; then
    FILTER_CAT="$CATEGORY"
else
    FILTER_CAT="Billing"
fi

FILTERED=$(curl -sf "$BACKEND_URL/traces?category=$FILTER_CAT")
BAD_COUNT=$(echo "$FILTERED" | python3 -c "
import sys, json
traces = json.load(sys.stdin)
bad = [t for t in traces if t['category'] != '$FILTER_CAT']
print(len(bad))
")
if [ "$BAD_COUNT" -eq 0 ]; then
    log_pass "Category filter ($FILTER_CAT) -- all returned traces match"
else
    log_fail "Category filter ($FILTER_CAT) -- $BAD_COUNT traces did not match"
fi

# ── 7. LLM fallback check ──────────────────────────────────────────────────
log_section "7" "LLM fallback check"
if [ "$CATEGORY" = "LLM_UNAVAILABLE" ]; then
    log_pass "No API key -- category correctly set to LLM_UNAVAILABLE"
    LLM_COUNT=$(echo "$ANALYTICS_AFTER" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d['categories'].get('LLM_UNAVAILABLE', {}).get('count', 0))
")
    if [ "$LLM_COUNT" -gt 0 ]; then
        log_pass "LLM_UNAVAILABLE count in analytics: $LLM_COUNT"
    else
        log_fail "LLM_UNAVAILABLE not reflected in analytics"
    fi
else
    log_pass "LLM available -- category is $CATEGORY (not LLM_UNAVAILABLE)"
fi

# ── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo -e "  Results: ${GREEN}$PASS_COUNT passed${NC}, ${RED}$FAIL_COUNT failed${NC}"
echo "========================================"

if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
fi
