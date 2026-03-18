#!/usr/bin/env bash
# ═══════════════════════════════════════
# Script de déploiement DocuFlow
# ═══════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

echo "╔══════════════════════════════════════╗"
echo "║       DocuFlow — Déploiement         ║"
echo "╚══════════════════════════════════════╝"
echo ""

# 1. Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker non trouvé. Veuillez installer Docker Desktop."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker daemon non démarré."
    exit 1
fi

echo "✅ Docker détecté"

# 2. Fichier .env
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ .env créé à partir de .env.example"
    else
        echo "⚠️  Pas de .env.example trouvé, création d'un .env minimal"
        cat > .env <<EOF
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MONGO_USER=admin
MONGO_PASSWORD=admin
FERNET_KEY=
EOF
    fi
fi

# 3. Générer FERNET_KEY si vide
if grep -q "^FERNET_KEY=$" .env 2>/dev/null; then
    FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || openssl rand -base64 32)
    sed -i "s|^FERNET_KEY=.*|FERNET_KEY=${FERNET_KEY}|" .env
    echo "✅ FERNET_KEY générée"
fi

# 4. Build des images
echo ""
echo "🔨 Construction des images Docker..."
docker compose build --parallel

# 5. Démarrer l'infrastructure
echo ""
echo "🚀 Démarrage des services..."
docker compose up -d

# 6. Attendre que les services soient prêts
echo ""
echo "⏳ Vérification des services..."

wait_for_service() {
    local name=$1
    local url=$2
    local max_attempts=${3:-30}
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo "  ✅ $name"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    echo "  ⚠️  $name (timeout après ${max_attempts} tentatives)"
    return 1
}

sleep 10
wait_for_service "MinIO" "http://localhost:9000/minio/health/live" 30
wait_for_service "MongoDB" "http://localhost:27017" 20 || true
wait_for_service "Backend" "http://localhost:4000/api/health" 30
wait_for_service "OCR Service" "http://localhost:5001/api/health" 60
wait_for_service "Validation" "http://localhost:5002/api/health" 30
wait_for_service "Frontend" "http://localhost:3000" 20
wait_for_service "Airflow" "http://localhost:8080/health" 60

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║           DocuFlow — Déployé !                   ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  Frontend    → http://localhost:3000             ║"
echo "║  Backend API → http://localhost:4000/api         ║"
echo "║  OCR Service → http://localhost:5001/api         ║"
echo "║  Validation  → http://localhost:5002/api         ║"
echo "║  MinIO       → http://localhost:9001             ║"
echo "║  Airflow     → http://localhost:8080             ║"
echo "╚══════════════════════════════════════════════════╝"
