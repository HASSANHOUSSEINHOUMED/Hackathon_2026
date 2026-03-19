# Backend API - DocuFlow

API Node.js/Express pour la gestion des documents et fournisseurs.

## 📦 Technologies

- **Node.js 20** avec **Express 4.18**
- **Mongoose** pour MongoDB
- **Socket.io** pour les notifications temps réel
- **Multer** pour l'upload de fichiers
- **MinIO SDK** pour le stockage Data Lake
- **OpenAI SDK** pour le raffinement LLM

## 🏗️ Structure

```
backend/
├── models/
│   ├── Document.js      # Schéma MongoDB des documents
│   └── Supplier.js      # Schéma MongoDB des fournisseurs
├── routes/
│   ├── documents.js     # CRUD documents
│   ├── suppliers.js     # CRUD fournisseurs + vérification SIREN
│   ├── process.js       # Upload + OCR + validation
│   ├── validation.js    # Résultats de validation
│   └── llm.js           # Re-extraction via OpenAI
├── utils/
│   └── storage.js       # Client MinIO
├── server.js            # Point d'entrée
├── Dockerfile
└── package.json
```

## 🔌 Endpoints API

### Documents

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/documents` | Liste tous les documents |
| GET | `/api/documents/:id` | Détail d'un document |
| DELETE | `/api/documents/:id` | Supprime un document |

### Upload & Traitement

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/process` | Upload + OCR + validation (mode batch ou individuel) |

**Mode Batch :**
Lorsque plusieurs documents sont envoyés, le backend effectue :
1. Phase 1 : OCR de tous les documents
2. Phase 2 : Validation batch (règles inter-documents)
3. Phase 3 : Sauvegarde avec anomalies indexées

### Fournisseurs

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/suppliers` | Liste avec stats |
| GET | `/api/suppliers/verify/:number` | Vérifie SIREN/SIRET via API gouv |
| POST | `/api/suppliers` | Crée un fournisseur |

### LLM (OpenAI)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/llm/status` | Vérifie si l'API est disponible |
| POST | `/api/llm/reextract/:id` | Re-extraction via GPT-4o-mini |

### Validation

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/validation/results` | Anomalies agrégées |

### Système

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/health` | Health check |

## ⚙️ Variables d'environnement

```env
PORT=4000
MONGO_URI=mongodb://admin:admin@mongodb:27017/docuflow?authSource=admin
OCR_SERVICE_URL=http://ocr-service:5001
VALIDATION_SERVICE_URL=http://validation-service:5002
MINIO_ENDPOINT=minio
MINIO_PORT=9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
OPENAI_API_KEY=sk-...  # Optionnel
```

## 🚀 Développement local

```bash
# Avec Docker (recommandé)
docker compose up -d backend

# Sans Docker
npm install
npm run dev
```

## 📡 WebSocket Events

Le backend émet des événements Socket.io pour le temps réel :

| Event | Payload | Description |
|-------|---------|-------------|
| `document:processed` | `{document_id, type, file_name, anomalies_count}` | Document traité |
| `anomaly:detected` | `{rule, severity, message, file_name}` | Anomalie détectée |
| `document:llm_refined` | `{document_id, type, file_name}` | Document raffiné par LLM |

## 🗄️ Schémas MongoDB

### Document

```javascript
{
  document_id: String,      // Hash MD5 du fichier
  file_name: String,
  doc_type: "facture" | "devis" | "kbis" | "urssaf" | "siret" | "rib" | "inconnu",
  pipeline_status: "raw" | "ocr_done" | "validated" | "llm_refined" | "curated",
  entities: {
    siret, tva_intra, montant_ht, tva, montant_ttc,
    date_emission, date_expiration, raison_sociale, iban, bic
  },
  raw_text: String,         // Texte OCR brut
  anomalies: [{ rule, severity, message }],
  minio_paths: { raw, clean, curated },
  llm_extracted: Boolean,
  created_at: Date
}
```

### Supplier

```javascript
{
  supplier_id: String,
  siret: String,
  raison_sociale: String,
  tva_intra: String,
  iban: String,
  bic: String,
  conformity_status: "ok" | "warning" | "error",
  documents: [String],      // IDs des documents liés
  verified: Boolean,        // Vérifié via API gouv
  api_data: Object          // Données de l'API recherche-entreprises
}
```
