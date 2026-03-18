# Frontend - DocuFlow

Interface utilisateur React pour la validation de documents administratifs.

## 📦 Technologies

- **React 18** avec Hooks
- **Vite** pour le bundling rapide
- **Tailwind CSS** pour le styling
- **Recharts** pour les graphiques
- **Lucide React** pour les icônes
- **React Router DOM** pour la navigation
- **React Dropzone** pour l'upload drag & drop
- **React Hot Toast** pour les notifications

## 🏗️ Structure

```
frontend/
├── src/
│   ├── components/         # Composants réutilisables
│   ├── context/
│   │   └── UploadContext.jsx  # État global des uploads
│   ├── pages/
│   │   ├── UploadPage.jsx     # Page d'upload principale
│   │   ├── DocumentsPage.jsx  # Historique des documents
│   │   ├── CRMPage.jsx        # Gestion fournisseurs
│   │   └── ConformityPage.jsx # Tableau de conformité
│   ├── App.jsx            # Routes et layout
│   ├── main.jsx           # Point d'entrée
│   └── index.css          # Styles Tailwind
├── nginx.conf             # Configuration proxy
├── Dockerfile
├── vite.config.js
└── package.json
```

## 🎨 Pages

### 1. Upload (`/`)
- Upload drag & drop multiple
- Barre de progression
- Aperçu des résultats OCR en temps réel
- Détection automatique du type de document

### 2. Documents (`/documents`)
- Historique des documents traités
- Détails expandables (entités, anomalies)
- Bouton "Re-extraire avec IA" (OpenAI)
- Filtres par statut et type

### 3. CRM (`/crm`)
- Liste des fournisseurs
- Vérification SIREN/SIRET via API gouv
- Import de fournisseurs vérifiés
- Indicateurs de conformité

### 4. Conformité (`/conformity`)
- Tableau des anomalies détectées
- Filtres par sévérité (ERROR, WARNING, INFO)
- Liens vers les documents concernés

## ⚙️ Configuration

### Variables d'environnement (build-time)

```env
VITE_API_URL=http://localhost:4000
```

### Proxy Nginx (runtime)

Le fichier `nginx.conf` configure le proxy vers le backend :

```nginx
location /api/ {
    proxy_pass http://backend:4000/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## 🚀 Développement local

```bash
# Avec Docker (recommandé)
docker compose up -d frontend

# Sans Docker
npm install
npm run dev

# Build production
npm run build
```

## 🎯 Fonctionnalités clés

### Upload intelligent
- Support PDF, PNG, JPEG (max 20 Mo)
- Upload multiple (jusqu'à 10 fichiers)
- OCR automatique côté serveur
- Validation en temps réel

### Raffinement LLM
- Bouton pour re-extraire les entités avec GPT-4o-mini
- Correction automatique des erreurs OCR
- Fusion intelligente des entités existantes

### Temps réel
- Connexion WebSocket au backend
- Notifications toast instantanées
- Mise à jour automatique des listes

### Responsive
- Design adaptatif mobile/desktop
- Sidebar collapsible
- Tables scrollables
