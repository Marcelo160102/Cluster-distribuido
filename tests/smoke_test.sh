#!/usr/bin/env bash
# smoke_test.sh — Verificación rápida del estado del clúster
set -euo pipefail

BASE_URL="${1:-http://localhost:80}"
PASS=0
FAIL=0

green() { printf "\033[32m%s\033[0m\n" "$1"; }
red()   { printf "\033[31m%s\033[0m\n" "$1"; }

check() {
    local desc="$1" expected="$2" actual="$3"
    if echo "$actual" | grep -qF "$expected"; then
        green "  ✓ $desc"
        PASS=$((PASS + 1))
    else
        red "  ✗ $desc (esperaba '$expected', obtuvo: $actual)"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Smoke Test: Clúster Distribuido ==="
echo "Target: $BASE_URL"
echo ""

# 1. Health (LB)
RESP=$(curl -sf "$BASE_URL/health" 2>&1 || echo "FAILED")
check "GET /health" "alive" "$RESP"

# 2. Leer datos (con API Key)
RESP=$(curl -sf "$BASE_URL/data" -H "X-API-Key: cluster-demo-key-2026" 2>&1 || echo "FAILED")
echo "$RESP" | python3 -c "import sys,json; data=json.load(sys.stdin); assert isinstance(data, list), 'not a list'" 2>/dev/null && green "  ✓ GET /data (lista)" && PASS=$((PASS+1)) || { red "  ✗ GET /data (no es una lista)"; FAIL=$((FAIL+1)); }

# 3. Crear un endpoint VoIP (reintentar hasta dar con el líder)
APIKEY="X-API-Key: cluster-demo-key-2026"
PAYLOAD='{"data": "{\"extension\": \"999\", \"protocol\": \"SIP\", \"ip_address\": \"10.0.0.99\", \"status\": \"online\", \"user_agent\": \"SmokeTest\"}"}'
LEADER=""
for i in 1 2 3 4 5 6 7 8 9; do
    RESP=$(curl -s -X POST "$BASE_URL/data" -H "Content-Type: application/json" -H "$APIKEY" -d "$PAYLOAD" 2>&1 || true)
    if echo "$RESP" | grep -qF '"id"'; then
        LEADER="found"
        break
    fi
    sleep 1
done
if [[ "$LEADER" == "found" ]]; then
    green "  ✓ POST /data (crear)"
    PASS=$((PASS + 1))
else
    red "  ✗ POST /data (crear) — no se alcanzó el líder tras reintentos"
    FAIL=$((FAIL + 1))
fi

# 4. Verificar datos replicados (leer después de escribir)
sleep 2
RESP=$(curl -sf "$BASE_URL/data" -H "X-API-Key: cluster-demo-key-2026" 2>&1 || echo "FAILED")
check "GET /data (con datos)" "999" "$RESP"

echo ""
echo "=== Resultados: $PASS pasaron, $FAIL fallaron ==="
exit $FAIL
