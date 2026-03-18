#!/usr/bin/env bash
# Réinitialise complètement DocuFlow (supprime les volumes)
set -euo pipefail

cd "$(dirname "$0")/.."

echo "⚠️  ATTENTION : Cette action va supprimer toutes les données !"
read -p "Confirmer ? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Annulé."
    exit 0
fi

echo "🗑️  Arrêt et suppression des volumes..."
docker compose down -v --remove-orphans

echo "🗑️  Nettoyage des images..."
docker compose rm -f

echo "✅ Réinitialisation complète"
