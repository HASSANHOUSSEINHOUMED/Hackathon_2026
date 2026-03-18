#!/usr/bin/env bash
# Arrête tous les services DocuFlow
set -euo pipefail

cd "$(dirname "$0")/.."

echo "🛑 Arrêt des services DocuFlow..."
docker compose down
echo "✅ Services arrêtés"
