# Scripts de déploiement - DocuFlow

Scripts shell pour la gestion du projet.

## 📁 Fichiers

| Script | Description |
|--------|-------------|
| `deploy.sh` | Déploiement complet (build + start) |
| `stop.sh` | Arrêt de tous les services |
| `reset.sh` | Reset complet (supprime toutes les données) |
| `test_e2e.sh` | Tests end-to-end |

## 🚀 Utilisation

### Linux / macOS

```bash
chmod +x scripts/*.sh

# Déployer
./scripts/deploy.sh

# Arrêter
./scripts/stop.sh

# Reset complet
./scripts/reset.sh

# Tests
./scripts/test_e2e.sh
```

### Windows (PowerShell)

Les scripts sont conçus pour Bash. Sur Windows, utilisez directement les commandes Docker Compose :

```powershell
# Déployer
docker compose up -d --build

# Arrêter
docker compose down

# Reset complet (supprime volumes)
docker compose down -v

# Voir les logs
docker compose logs -f
```

## 📜 Détail des scripts

### deploy.sh

```bash
#!/bin/bash
set -e

echo "🚀 Déploiement DocuFlow..."

# Créer .env si absent
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 .env créé depuis .env.example"
fi

# Build et démarrage
docker compose build
docker compose up -d

# Attendre que les services soient prêts
echo "⏳ Attente des services..."
sleep 10

# Health checks
curl -sf http://localhost:4000/api/health > /dev/null && echo "✅ Backend OK"
curl -sf http://localhost:5001/api/health > /dev/null && echo "✅ OCR OK"
curl -sf http://localhost:5002/api/health > /dev/null && echo "✅ Validation OK"

echo "🎉 DocuFlow déployé avec succès !"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:4000"
```

### stop.sh

```bash
#!/bin/bash
echo "🛑 Arrêt de DocuFlow..."
docker compose down
echo "✅ Services arrêtés"
```

### reset.sh

```bash
#!/bin/bash
echo "⚠️  Reset complet de DocuFlow..."
echo "Ceci va supprimer TOUTES les données !"
read -p "Continuer ? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker compose down -v
    docker system prune -f
    echo "✅ Reset terminé"
fi
```

### test_e2e.sh

```bash
#!/bin/bash
set -e

echo "🧪 Tests end-to-end..."

# Vérifier que les services tournent
docker compose ps | grep -q "Up" || { echo "❌ Services non démarrés"; exit 1; }

# Test health endpoints
curl -sf http://localhost:4000/api/health
curl -sf http://localhost:5001/api/health
curl -sf http://localhost:5002/api/health

# Test upload d'un document
curl -sf -X POST -F "documents=@dataset/output/raw/FAC_001.pdf" \
    http://localhost:4000/api/process

echo "✅ Tests e2e passés"
```

## ⚠️ Notes

- Les scripts nécessitent `curl` pour les health checks
- Le script `reset.sh` supprime **toutes** les données (MongoDB, MinIO)
- Sur Windows Git Bash, les scripts fonctionnent généralement
