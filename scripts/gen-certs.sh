#!/usr/bin/env bash
# gen-certs.sh — Genera certificado SSL self-signed para el LB
set -euo pipefail

CERT_DIR="${1:-./certs}"
mkdir -p "$CERT_DIR"

if [[ -f "$CERT_DIR/selfsigned.crt" && -f "$CERT_DIR/selfsigned.key" ]]; then
    echo "Certificados ya existen en $CERT_DIR"
    exit 0
fi

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$CERT_DIR/selfsigned.key" \
    -out "$CERT_DIR/selfsigned.crt" \
    -subj "/CN=localhost"

echo "Certificados generados:"
echo "  CRT: $CERT_DIR/selfsigned.crt"
echo "  KEY: $CERT_DIR/selfsigned.key"
