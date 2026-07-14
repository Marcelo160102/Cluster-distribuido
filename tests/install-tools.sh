#!/usr/bin/env bash
# install-tools.sh — Verifica herramientas de pruebas de rendimiento
set -euo pipefail

echo "=== Verificando herramientas de pruebas ==="
echo "  Python + httpx: requerido para benchmark.py"
python3 -c "import httpx; print('  httpx OK')" 2>&1 || { echo "  ERROR: pip install httpx"; exit 1; }
echo "  tests/benchmark.py listo para ejecución"
echo "=== OK: todo listo ==="
