#!/usr/bin/env bash
# install-tools.sh — Instala herramientas de pruebas de rendimiento
set -euo pipefail

echo "=== Instalando herramientas de pruebas ==="

# hey (https://github.com/rakyll/hey)
if ! command -v hey &>/dev/null; then
    echo "Instalando hey..."
    if command -v go &>/dev/null; then
        go install github.com/rakyll/hey@latest
    else
        # Binario precompilado
        OS=$(uname -s | tr '[:upper:]' '[:lower:]')
        ARCH=$(uname -m)
        case "$ARCH" in
            x86_64) ARCH="amd64" ;;
            aarch64) ARCH="arm64" ;;
        esac
        curl -sL "https://hey-release.s3.us-east-2.amazonaws.com/hey_${OS}_${ARCH}" -o /usr/local/bin/hey
        chmod +x /usr/local/bin/hey
    fi
else
    echo "  hey ya instalado"
fi

# wrk
if ! command -v wrk &>/dev/null; then
    echo "Instalando wrk..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y wrk
    else
        echo "  Advertencia: no se pudo instalar wrk automáticamente"
    fi
else
    echo "  wrk ya instalado"
fi

echo "=== Herramientas listas ==="
hey --version 2>/dev/null || true
wrk --version 2>/dev/null || true
