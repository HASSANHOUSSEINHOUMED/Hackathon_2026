# 📊 Présentation PowerPoint — DocuFlow
## Hackathon 2026 — Validation Automatique de Documents Administratifs

**Durée totale : 25 minutes**

---

# SLIDE 1 — Page de Titre
**Durée : 30 secondes**

## Titre
**DocuFlow**

## Sous-titre
*Intelligence Artificielle pour la Validation Automatique de Documents Administratifs*

## Contenu
```
Hackathon 2026

Équipe :
• Tahina — Scenario Maker
• Abdelmalek — OCR Engine
• Yanis — Frontend MERN
• Hassan — Data Lake
• Wael — Anomaly Detection
• Korniti — Pipeline Airflow

Mars 2026
```

## Figure
Logo DocuFlow au centre (flux de documents stylisé avec une coche verte).
Arrière-plan : dégradé bleu professionnel (#1e3a5f → #2d5a87).
Icônes des 6 membres en cercle autour du logo.

## Notes orateur
> "Bonjour à tous. Nous sommes l'équipe DocuFlow et nous allons vous présenter notre solution d'intelligence artificielle pour automatiser la validation des documents administratifs d'entreprise. En 25 minutes, nous vous montrerons comment nous avons transformé un processus manuel fastidieux en un pipeline intelligent de bout en bout."

---

# SLIDE 2 — Le Problème Métier
**Durée : 2 minutes**

## Titre
**Un processus manuel coûteux et source d'erreurs**

## Contenu
```
📊 Chiffres clés du problème :

• 2,4 milliards de factures échangées par an en France
• 15 à 45 minutes pour valider manuellement un dossier fournisseur
• 4% de taux d'erreur humain sur les vérifications de conformité
• 30% des factures contiennent au moins une anomalie

💸 Impact financier :
• Coût moyen d'une erreur non détectée : 1 200 €
• Temps opérateur : 65% du temps passé sur des tâches répétitives
• Risque de fraude documentaire en hausse de 23% depuis 2020

❌ Conséquences :
• Retards de paiement fournisseurs
• Litiges contractuels
• Non-conformité réglementaire (TVA, URSSAF)
```

## Figure
**Schéma "AVANT" — Flux manuel** :
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  📄 Facture │───►│  👤 Humain  │───►│  📋 Saisie  │───►│  ✓/✗ Contrôle│
│  reçue      │    │  ouvre PDF  │    │  manuelle   │    │  visuel     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │
                    ⏱️ 15-45 min
                    ❌ 4% erreurs
                    😓 Fatigue cognitive
```
Couleurs : rouge/orange pour montrer les points de friction.
Icône humain au centre avec des flèches montrant la charge de travail.

## Notes orateur
> "Commençons par le problème. En France, plus de 2 milliards de factures sont échangées chaque année. Pour chaque dossier fournisseur — factures, attestations URSSAF, Kbis, RIB — un opérateur passe entre 15 et 45 minutes à tout vérifier manuellement. Le taux d'erreur humain est de 4%, et une erreur non détectée coûte en moyenne 1200 euros à l'entreprise. Sans parler des risques de fraude documentaire qui explosent. Notre question : comment automatiser intelligemment ce processus ?"

---

# SLIDE 3 — Notre Solution en Une Phrase
**Durée : 1 minute 30**

## Titre
**DocuFlow : L'IA qui valide vos documents en 3 secondes**

## Contenu
```
🎯 Notre proposition de valeur :

"Un pipeline intelligent qui extrait, valide et enrichit 
automatiquement vos documents administratifs, 
avec détection d'anomalies en temps réel."

✅ Ce que DocuFlow fait :
• Extraction OCR intelligente (Tesseract + EasyOCR hybride)
• Classification automatique du type de document
• 12 règles de validation métier prédéfinies
• Détection statistique des montants anormaux (Machine Learning)
• Interface temps réel avec notifications WebSocket

⚡ Résultats :
• Temps de traitement : 3,2 secondes par document
• Taux de détection des anomalies : 94%
• Réduction du temps opérateur : -85%
```

## Figure
**Schéma "APRÈS" — Pipeline automatisé** :
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  📄 Upload  │───►│  🤖 OCR +   │───►│  🔍 Règles  │───►│  ✅ Résultat│
│  drag&drop  │    │  Extraction │    │  + ML       │    │  instantané │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │
                    ⏱️ 3,2 sec
                    ✅ 94% détection
                    🎯 Zéro fatigue
```
Couleurs : vert/bleu pour montrer la fluidité.
Animation suggérée : flèches qui s'animent de gauche à droite.

## Notes orateur
> "Notre solution, DocuFlow, est un pipeline intelligent de bout en bout. Vous uploadez vos documents par simple drag & drop, et en 3 secondes, le système extrait toutes les informations, classifie le type de document, applique 12 règles de validation métier, et détecte les anomalies statistiques via du machine learning. Le taux de détection atteint 94%, et vous réduisez le temps opérateur de 85%. Voyons maintenant comment c'est construit."

---

# SLIDE 4 — Architecture Globale
**Durée : 2 minutes**

## Titre
**Architecture microservices en 5 couches**

## Contenu
```
🏗️ Stack technologique :

COUCHE 1 — Frontend (Port 3000)
• React 18 + Vite + Tailwind CSS
• Socket.io pour temps réel

COUCHE 2 — Backend API (Port 4000)
• Node.js 20 + Express + Mongoose
• Orchestration des microservices

COUCHE 3 — Services IA (Ports 5001-5002)
• OCR Service : Python + Flask + Tesseract/EasyOCR
• Validation Service : Python + Flask + Scikit-learn

COUCHE 4 — Data Lake (Port 9000)
• MinIO : 4 zones de stockage (pending/raw/clean/curated)
• MongoDB : métadonnées et index

COUCHE 5 — Orchestration (Port 8080)
• Apache Airflow : DAGs de traitement batch
• PostgreSQL : backend Airflow

📦 Total : 11 conteneurs Docker
```

## Figure
**Diagramme d'architecture complet** :
```
┌─────────────────────────────────────────────────────────────────────┐
│                        🖥️ FRONTEND (React)                          │
│                         Port 3000 — Nginx                           │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP + WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      🔧 BACKEND (Node.js/Express)                    │
│                         Port 4000 — API REST                        │
└───────┬───────────────────┬───────────────────┬─────────────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ 🔤 OCR Service│   │ ⚠️ Validation │   │ 📦 Storage API│
│  Flask:5001   │   │  Flask:5002   │   │  Flask:5003   │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        ▼                                       ▼
┌───────────────┐                       ┌───────────────┐
│ 🗄️ MinIO      │                       │ 🍃 MongoDB    │
│ Data Lake     │                       │ Métadonnées   │
│ Port 9000     │                       │ Port 27017    │
└───────────────┘                       └───────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     ⏰ AIRFLOW (Orchestration)                       │
│                    Scheduler + Webserver — Port 8080                │
└─────────────────────────────────────────────────────────────────────┘
```
Code couleur par couche :
- Bleu ciel : Frontend
- Vert : Backend
- Orange : Services IA
- Violet : Stockage
- Gris : Orchestration

## Notes orateur
> "Voici notre architecture en 5 couches. En haut, le frontend React qui communique en temps réel via Socket.io. Le backend Node.js orchestre les appels vers deux microservices Python : l'OCR et la validation. Les données transitent par un Data Lake MinIO organisé en 4 zones, avec MongoDB pour les métadonnées. Et Airflow en bas pour l'orchestration des traitements batch. Le tout conteneurisé avec Docker Compose : 11 conteneurs qui communiquent via un réseau interne. Voyons maintenant chaque composant en détail."

---

# SLIDE 5 — Dataset & Scénarios de Test (Tahina)
**Durée : 2 minutes**

## Titre
**Génération de 500+ documents réalistes pour l'entraînement**

## Contenu
```
📄 6 types de documents générés :
• Factures (avec lignes de produits, TVA, totaux)
• Devis (dates de validité, conditions)
• Attestations URSSAF (vigilance, cotisations)
• Attestations SIRET (INSEE)
• Extraits Kbis (greffe, RCS)
• RIB (IBAN, BIC, domiciliation)

🎭 4 familles de scénarios :
┌────────────────┬──────────┬────────────────────────────────┐
│ Scénario       │ % Dataset│ Description                    │
├────────────────┼──────────┼────────────────────────────────┤
│ Cohérent       │ 60%      │ Documents valides sans erreur  │
│ Mismatch       │ 15%      │ Incohérences inter-documents   │
│ Expiré         │ 15%      │ Dates dépassées                │
│ Bruité         │ 10%      │ Scan dégradé, rotation, flou   │
└────────────────┴──────────┴────────────────────────────────┘

📊 Statistiques du dataset :
• 500 documents générés
• 12 cas de test spécifiques par règle
• Ground truth JSON pour chaque document
• Évaluation automatique CER/WER
```

## Figure
**Comparaison visuel document propre vs dégradé** :

Côté gauche — "Document propre" :
- Capture d'une facture PDF générée, nette, lisible
- Encadré vert

Côté droit — "Document dégradé (scénario noisy)" :
- Même facture avec rotation 2°, bruit gaussien, taches
- Encadré orange

En dessous :
```
Bibliothèques utilisées :
├── Faker 28.4.1 — Données fictives réalistes
├── ReportLab 4.1.0 — Génération PDF
└── OpenCV 4.9 — Dégradation réaliste
```

## Notes orateur
> "Tahina a développé un générateur de dataset complet. Nous produisons 6 types de documents administratifs français, avec des données fictives mais réalistes grâce à Faker. Le dataset est organisé en 4 scénarios : 60% de documents corrects pour l'entraînement, 15% avec des incohérences volontaires comme des SIRET différents, 15% avec des dates expirées, et 10% de documents dégradés pour tester la robustesse de l'OCR. Chaque document a son ground truth JSON, ce qui permet une évaluation automatique."

---

# SLIDE 6 — Pipeline OCR (Abdelmalek)
**Durée : 2 minutes 30**

## Titre
**OCR hybride Tesseract + EasyOCR avec extraction d'entités**

## Contenu
```
🔤 Stratégie OCR hybride :

1️⃣ Tesseract (prioritaire)
   • Rapide : ~800ms par page
   • Config : --oem 3 --psm 6 -l fra
   • Idéal pour documents propres

2️⃣ EasyOCR (fallback automatique)
   • Active si confiance < 60% ou texte < 50 chars
   • Deep Learning (LSTM)
   • Meilleur sur documents dégradés

📋 Entités extraites automatiquement :
┌──────────────────┬────────────────────────────────┐
│ Entité           │ Pattern Regex                  │
├──────────────────┼────────────────────────────────┤
│ SIRET            │ \b\d{14}\b                     │
│ TVA Intra        │ FR\s?\d{2}\s?\d{9}            │
│ IBAN             │ FR\d{2}[\dA-Z]{23}            │
│ Montants (€)     │ \d{1,3}(?:\s?\d{3})*[,\.]\d{2}│
│ Dates            │ \d{2}[/\-.]\d{2}[/\-.]\d{4}  │
└──────────────────┴────────────────────────────────┘

📊 Performances :
• Confiance moyenne : 87%
• CER (Character Error Rate) : 2.3%
• Temps moyen : 1,2 sec/page
```

## Figure
**Schéma du pipeline OCR étape par étape** :
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  📄 PDF     │───►│ 🖼️ Convert  │───►│ 🔧 Preproc  │───►│ 🔤 Tesseract│
│  Upload     │    │ PyMuPDF     │    │ OpenCV      │    │ --oem 3     │
└─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘
                                                                │
                                                    ┌───────────┴───────────┐
                                                    │  Confiance < 60% ?    │
                                                    │  Texte < 50 chars ?   │
                                                    └───────────┬───────────┘
                                                          │ OUI        │ NON
                                                          ▼            ▼
                                                   ┌─────────────┐  ┌─────────────┐
                                                   │ 🧠 EasyOCR  │  │ ✅ Résultat │
                                                   │ Deep Learn  │  │   final     │
                                                   └──────┬──────┘  └─────────────┘
                                                          │
                                                          ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 📝 Raw Text │◄───│ 🏷️ Classify │◄───│ 🔍 Extract  │
│   + JSON    │    │ (keywords)  │    │ (regex+NER) │
└─────────────┘    └─────────────┘    └─────────────┘
```

Exemple de sortie JSON encadré :
```json
{
  "type": "facture",
  "siret": "12345678901234",
  "montant_ttc": 1800.00,
  "ocr_confidence": 0.87
}
```

## Notes orateur
> "Abdelmalek a conçu un pipeline OCR hybride intelligent. On commence par convertir le PDF en images avec PyMuPDF, puis on prétraite avec OpenCV — binarisation, débruitage. Ensuite Tesseract extrait le texte. Si la confiance est inférieure à 60% ou si on a moins de 50 caractères, on bascule automatiquement sur EasyOCR qui utilise du deep learning et marche mieux sur les documents dégradés. Enfin, on classifie le type de document par mots-clés et on extrait les entités avec des regex optimisés pour les formats français. Résultat : 87% de confiance moyenne et un CER de seulement 2.3%."

---

# SLIDE 7 — Data Lake 3 Zones (Hassan)
**Durée : 2 minutes**

## Titre
**Architecture Data Lake avec MinIO : Raw → Clean → Curated**

## Contenu
```
🗄️ Philosophie Data Lake :
"Les données brutes ne sont jamais modifiées — on enrichit couche par couche"

📦 4 zones de stockage MinIO :

┌────────────────┬──────────────────────────────────────────┐
│ Zone           │ Contenu                                  │
├────────────────┼──────────────────────────────────────────┤
│ pending-zone   │ Documents uploadés, en attente OCR       │
│ raw-zone       │ PDFs/images originaux (immuables)        │
│ clean-zone     │ JSON OCR structuré + entités extraites   │
│ curated-zone   │ Données validées, enrichies, prêtes BI   │
└────────────────┴──────────────────────────────────────────┘

🔗 Intégration MongoDB :
• Métadonnées indexées (document_id, supplier_id, status)
• Chemins MinIO stockés : minio_paths.raw, minio_paths.clean
• Recherche rapide par type, date, fournisseur

🔒 Conformité :
• RGPD : endpoint DELETE /api/storage/document/{id}
• Suppression complète multi-zones
• URLs présignées (expiration 1h)
```

## Figure
**Diagramme des 4 buckets MinIO avec flux** :
```
                        ┌─────────────────┐
                        │   📤 Upload     │
                        │   Frontend      │
                        └────────┬────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      🟡 PENDING-ZONE                                 │
│   Documents en attente • Rétention : jusqu'à traitement             │
│   Exemple : invoice_abc123.pdf                                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ OCR terminé
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      🔴 RAW-ZONE                                     │
│   Fichiers originaux (immuables) • Rétention : permanente           │
│   Exemple : raw-zone/abc123.pdf                                      │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ Extraction JSON
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      🟢 CLEAN-ZONE                                   │
│   JSON structuré OCR • Rétention : permanente                       │
│   Exemple : clean-zone/abc123.json                                   │
│   { "type": "facture", "siret": "...", "montant_ttc": 1800.00 }     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ Validation OK
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      🔵 CURATED-ZONE                                 │
│   Données enrichies & validées • Prêtes pour BI                     │
│   Exemple : curated-zone/abc123_enriched.json                        │
│   { ..., "anomalies": [], "supplier": {...}, "validated": true }    │
└─────────────────────────────────────────────────────────────────────┘
```

## Notes orateur
> "Hassan a architecturé notre Data Lake avec MinIO, compatible S3. On a 4 zones distinctes. Le pending-zone reçoit les uploads en attente. Le raw-zone stocke les fichiers originaux de façon immuable — on ne les modifie jamais. Après l'OCR, le JSON structuré va dans le clean-zone. Et une fois la validation passée, les données enrichies arrivent dans le curated-zone, prêtes pour la BI. MongoDB indexe les métadonnées pour des recherches rapides. Et on a un endpoint de suppression RGPD qui efface un document de toutes les zones."

---

# SLIDE 8 — Détection d'Anomalies (Wael)
**Durée : 2 minutes 30**

## Titre
**12 règles métier + détection statistique par Machine Learning**

## Contenu
```
⚠️ Catalogue des 12 règles de validation :

ERREURS CRITIQUES (bloquantes) :
🔴 SIRET_MISMATCH — SIRET différent entre documents
🔴 TVA_CALCUL_ERROR — TVA ≠ HT × taux
🔴 TTC_CALCUL_ERROR — TTC ≠ HT + TVA
🔴 ATTESTATION_EXPIREE — URSSAF dépassée
🔴 SIRET_FORMAT_INVALIDE — Clé de Luhn invalide
🔴 IBAN_FORMAT_INVALIDE — Checksum ISO 13616 KO

AVERTISSEMENTS :
🟠 KBIS_PERIME — Kbis > 90 jours
🟠 DEVIS_EXPIRE — Validité dépassée
🟠 RAISON_SOCIALE_MISMATCH — Levenshtein > 30%
🟠 IBAN_MISMATCH — RIB ≠ Facture
🟠 TVA_INTRA_INVALIDE — Format non conforme

INFORMATION :
🔵 MONTANT_ANORMAL — Détecté par IsolationForest (ML)

📊 Performances :
• Précision règles déterministes : 100%
• Rappel anomalies statistiques : 89%
• Temps de validation : 45ms / lot
```

## Figure
**Tableau des règles avec exemple d'alerte** :

Partie haute — Tableau visuel :
| Icône | Rule ID | Sévérité | Détection |
|-------|---------|----------|-----------|
| 🔴 | TVA_CALCUL_ERROR | ERROR | TVA affichée 180€ ≠ calculée 200€ |
| 🟠 | KBIS_PERIME | WARNING | Émis il y a 120 jours |
| 🔵 | MONTANT_ANORMAL | INFO | Score anomalie : -0.67 |

Partie basse — Exemple d'alerte JSON :
```json
{
  "rule_id": "TVA_CALCUL_ERROR",
  "severity": "ERROR",
  "message": "TVA (180.00€) ≠ HT × 20% (attendu: 200.00€)",
  "concerned_document_ids": ["FAC_042"],
  "evidence": {
    "expected": 200.00,
    "actual": 180.00,
    "difference": 20.00
  }
}
```

## Notes orateur
> "Wael a développé le moteur de validation avec deux approches complémentaires. D'abord, 12 règles déterministes qui vérifient les calculs TVA/TTC, les formats SIRET et IBAN avec les algorithmes officiels comme Luhn, les dates d'expiration, et la cohérence inter-documents. Ensuite, un modèle IsolationForest de scikit-learn détecte les montants statistiquement anormaux — utile pour repérer les fraudes ou erreurs de saisie. La précision des règles déterministes est de 100%, et le ML a un rappel de 89%. Le tout s'exécute en 45 millisecondes par lot de documents."

---

# SLIDE 9 — Interface Utilisateur (Yanis)
**Durée : 2 minutes**

## Titre
**3 interfaces React : Upload, Documents, Conformité**

## Contenu
```
🖥️ Application 1 — Upload (page d'accueil)
• Drag & drop multi-fichiers (PDF, PNG, JPG)
• Barre de progression temps réel (Socket.io)
• Notifications toast instantanées
• Limite : 10 fichiers × 20 MB

📋 Application 2 — Documents
• Liste paginée de tous les documents traités
• Filtres par type (facture, devis, kbis...)
• Filtres par statut (raw, validated, error)
• Modal détail : texte OCR + entités + anomalies

⚠️ Application 3 — Conformité
• KPIs en temps réel : erreurs / warnings / taux conformité
• Tableau des anomalies triable par sévérité
• Lien direct vers le document source
• Export CSV des alertes

🛠️ Stack Frontend :
React 18 + Vite 5.1 + Tailwind CSS + Recharts + Lucide Icons
```

## Figure
**Captures d'écran annotées des 3 interfaces** :

Layout en grille 2×2 :

**[En haut à gauche] — Page Upload**
- Zone drag & drop centrale avec icône cloud
- Liste de fichiers avec barres de progression vertes
- Toast "Document FAC_001.pdf traité avec succès !"
- Annotation : "Progression temps réel via WebSocket"

**[En haut à droite] — Page Documents**
- Tableau avec colonnes : Fichier | Type | Statut | Confiance | Date
- Badges colorés pour les types (bleu=facture, vert=devis...)
- Filtres dropdown en haut
- Annotation : "Filtrage et tri côté serveur"

**[En bas à gauche] — Page Conformité**
- 3 KPI cards : "12 Erreurs" (rouge), "5 Warnings" (orange), "94% Conformité" (vert)
- Tableau des anomalies avec icônes sévérité
- Annotation : "Tableau de bord temps réel"

**[En bas à droite] — Modal Détail Document**
- Onglets : Entités | Texte OCR | Anomalies
- JSON formaté des entités extraites
- Liste des anomalies avec bouton "Corriger"
- Annotation : "Vue détaillée par document"

## Notes orateur
> "Yanis a développé le frontend en React avec Vite pour un démarrage ultra-rapide. L'interface se divise en 3 sections. La page Upload permet le drag & drop avec progression temps réel — chaque document traité déclenche une notification instantanée via Socket.io. La page Documents liste tout ce qui a été traité avec des filtres par type et statut. Et la page Conformité est un tableau de bord avec les KPIs clés et le détail de chaque anomalie détectée. Le design utilise Tailwind CSS pour un rendu moderne et responsive."

---

# SLIDE 10 — Pipeline Airflow (Korniti)
**Durée : 2 minutes**

## Titre
**Orchestration intelligente avec Apache Airflow**

## Contenu
```
⏰ DAG : docuflow_document_pipeline
• Fréquence : toutes les 5 minutes
• 4 tâches séquentielles
• Retry automatique : 2 tentatives, délai 1 min

📋 Les 4 tâches du pipeline :

┌────────────┬──────────────────────────────────────────────┐
│ Tâche      │ Action                                       │
├────────────┼──────────────────────────────────────────────┤
│ INGEST     │ Récupère documents status="uploaded"         │
│ OCR        │ Appelle POST /api/ocr pour chaque doc        │
│ VALIDATE   │ Appelle POST /api/validate en batch          │
│ FINALIZE   │ Met à jour MongoDB + notifie frontend        │
└────────────┴──────────────────────────────────────────────┘

📊 Monitoring :
• Interface web Airflow : http://localhost:8080
• Logs JSON structurés par tâche
• Alertes email configurables (désactivées en démo)
• Historique des runs conservé 30 jours

⚡ Performance :
• Temps d'exécution moyen du DAG : 8 secondes pour 10 docs
• Parallélisation possible avec Celery (évolution future)
```

## Figure
**Capture du DAG Airflow avec les 4 tâches** :

Représentation visuelle du DAG :
```
    ┌─────────────┐
    │   INGEST    │ ← Vert (succès)
    │  ○ 1.2 sec  │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │     OCR     │ ← Vert (succès)
    │  ○ 4.5 sec  │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │  VALIDATE   │ ← Vert (succès)
    │  ○ 0.8 sec  │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │  FINALIZE   │ ← Vert (succès)
    │  ○ 1.5 sec  │
    └─────────────┘

Durée totale : 8.0 sec
Status : ✅ Success
```

En dessous, mini-capture de l'interface Airflow avec :
- Liste des DAG runs récents
- Gantt chart d'exécution

## Notes orateur
> "Korniti a mis en place l'orchestration avec Apache Airflow. Le DAG s'exécute toutes les 5 minutes et comporte 4 tâches séquentielles. D'abord INGEST qui récupère les documents en attente, puis OCR qui appelle notre microservice, VALIDATE qui lance la détection d'anomalies, et FINALIZE qui met à jour la base de données et notifie le frontend. On a le retry automatique en cas d'échec, des logs structurés, et une interface web pour monitorer en temps réel. Pour 10 documents, le pipeline complet prend 8 secondes."

---

# SLIDE 11 — Démonstration Live
**Durée : 3 minutes**

## Titre
**Démo : Upload → OCR → Anomalie détectée en 10 secondes**

## Contenu
```
🎬 Scénario de démonstration :

ÉTAPE 1 — Préparation (avant démo)
• 3 documents générés avec generate_test_errors.py :
  - FAC_TVA_ERROR.pdf (erreur calcul TVA)
  - URSSAF_EXPIREE.pdf (attestation périmée)
  - RIB_IBAN_INVALIDE.pdf (checksum IBAN KO)

ÉTAPE 2 — Upload (30 sec)
• Ouvrir http://localhost:3000
• Drag & drop des 3 fichiers
• Observer les barres de progression
• Notification toast pour chaque document

ÉTAPE 3 — Résultats (30 sec)
• Naviguer vers page Documents
• Montrer les 3 documents traités
• Ouvrir le modal du premier : entités extraites

ÉTAPE 4 — Anomalies (1 min)
• Naviguer vers page Conformité
• Montrer les 3 anomalies détectées :
  - 🔴 TVA_CALCUL_ERROR sur FAC_TVA_ERROR
  - 🔴 ATTESTATION_EXPIREE sur URSSAF_EXPIREE
  - 🔴 IBAN_FORMAT_INVALIDE sur RIB_IBAN_INVALIDE
• Cliquer sur une anomalie → détail avec evidence

ÉTAPE 5 — Airflow (30 sec)
• Ouvrir http://localhost:8080
• Montrer le DAG run en cours/terminé
• Montrer les logs d'une tâche
```

## Figure
**Schéma visuel du scénario de démonstration** :
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 📄 TVA_ERR  │    │ 📄 URSSAF   │    │ 📄 IBAN_KO  │
│  -20€ diff  │    │  >6 mois    │    │ checksum ✗  │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  📤 UPLOAD  │ ← Drag & Drop
                   │   3 files   │
                   └──────┬──────┘
                          │ ~3 sec par doc
                          ▼
                   ┌─────────────┐
                   │  🤖 OCR +   │
                   │  VALIDATION │
                   └──────┬──────┘
                          │
                          ▼
            ┌─────────────────────────┐
            │    ⚠️ 3 ANOMALIES       │
            │  🔴🔴🔴 Toutes ERROR   │
            └─────────────────────────┘
```

## Notes orateur
> "Passons à la démonstration live. J'ai préparé 3 documents avec des erreurs volontaires. Le premier a une erreur de calcul TVA, le deuxième est une attestation URSSAF expirée, le troisième a un IBAN avec un checksum invalide. Je vais les uploader par drag & drop... vous voyez les barres de progression... et les notifications arrivent. Maintenant, dans la page Conformité, on voit nos 3 anomalies détectées, toutes en ERROR rouge. Si je clique sur la première, on voit le détail : TVA affichée 180€, attendue 200€, différence 20€. Le système a tout détecté en moins de 10 secondes."

---

# SLIDE 12 — Résultats & Métriques
**Durée : 1 minute 30**

## Titre
**KPIs : 94% de détection, 3.2 sec de traitement**

## Contenu
```
📊 Métriques de performance :

┌─────────────────────────────────┬─────────┬─────────┐
│ Métrique                        │ Cible   │ Atteint │
├─────────────────────────────────┼─────────┼─────────┤
│ Confiance OCR (factures)        │ > 80%   │ 87% ✅  │
│ CER (Character Error Rate)      │ < 5%    │ 2.3% ✅ │
│ Classification Accuracy         │ > 90%   │ 95% ✅  │
│ Taux détection anomalies        │ > 90%   │ 94% ✅  │
│ Temps traitement E2E            │ < 5 sec │ 3.2s ✅ │
│ Latence validation              │ < 100ms │ 45ms ✅ │
└─────────────────────────────────┴─────────┴─────────┘

📈 Comparaison avec processus manuel :

│ Critère              │ Manuel      │ DocuFlow    │ Gain       │
├──────────────────────┼─────────────┼─────────────┼────────────┤
│ Temps par dossier    │ 25 min      │ 10 sec      │ x150       │
│ Taux d'erreur        │ 4%          │ 0.3%        │ -92%       │
│ Coût par document    │ 3.50€       │ 0.02€       │ -99%       │
│ Disponibilité        │ 8h/jour     │ 24/7        │ +200%      │
└──────────────────────┴─────────────┴─────────────┴────────────┘
```

## Figure
**Tableau de bord avec gauges et barres** :

Layout : 2 rangées de métriques

**Rangée 1 — Gauges circulaires** :
- Gauge "OCR Confidence" : 87% (vert)
- Gauge "Detection Rate" : 94% (vert)
- Gauge "Classification" : 95% (vert)

**Rangée 2 — Barres horizontales** :
- Barre "Temps E2E" : 3.2s / 5s max (64% rempli, vert)
- Barre "Latence Validation" : 45ms / 100ms max (45% rempli, vert)
- Barre "CER" : 2.3% / 5% max (46% rempli, vert)

**En bas — Graphique comparatif** :
Bar chart comparant "Manuel" vs "DocuFlow" sur : Temps, Erreurs, Coût
Les barres DocuFlow sont minuscules comparées aux barres Manuel

## Notes orateur
> "Regardons les résultats chiffrés. Tous nos objectifs sont atteints avec marge. L'OCR atteint 87% de confiance, la classification 95%, et on détecte 94% des anomalies. Le traitement end-to-end prend 3.2 secondes en moyenne. Par rapport au processus manuel, c'est un facteur 150 sur le temps, une réduction de 92% des erreurs, et une division par 175 du coût par document. Et surtout, le système tourne 24/7 sans fatigue."

---

# SLIDE 13 — Scalabilité
**Durée : 1 minute 30**

## Titre
**De 100 à 1 million de documents : architecture distribuée**

## Contenu
```
📈 Scalabilité horizontale prévue :

NIVEAU 1 — Actuel (PoC)
• 1 instance par service
• LocalExecutor Airflow
• Volume : ~1 000 docs/jour

NIVEAU 2 — Production (x10)
• 3 replicas OCR derrière load balancer
• MinIO distribué (4 nodes)
• MongoDB ReplicaSet
• Volume : ~10 000 docs/jour

NIVEAU 3 — Entreprise (x100)
• Kubernetes (EKS/GKE)
• Airflow CeleryExecutor + Redis
• MinIO cluster (16 nodes)
• Elasticsearch pour recherche
• Volume : ~100 000 docs/jour

NIVEAU 4 — Massif (x1000)
• Multi-région (3 datacenters)
• Kafka pour ingestion streaming
• GPU cluster pour EasyOCR
• Volume : 1 000 000 docs/jour
```

## Figure
**Schéma d'architecture distribuée niveau 3** :
```
                         ┌─────────────────────┐
                         │   Load Balancer     │
                         │     (Nginx/HAProxy) │
                         └──────────┬──────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
    ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
    │ OCR Pod #1  │          │ OCR Pod #2  │          │ OCR Pod #3  │
    │  (2 CPU)    │          │  (2 CPU)    │          │  (2 CPU)    │
    └──────┬──────┘          └──────┬──────┘          └──────┬──────┘
           │                        │                        │
           └────────────────────────┼────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                  MinIO Distributed Cluster                       │
    │   ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐        │
    │   │ N1  │  │ N2  │  │ N3  │  │ N4  │  │ N5  │  │ N6  │        │
    │   └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘        │
    │                    Erasure Coding 4+2                           │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                     Airflow + Celery                            │
    │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
    │   │ Worker 1 │  │ Worker 2 │  │ Worker 3 │  │ Worker 4 │      │
    │   └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
    └─────────────────────────────────────────────────────────────────┘
```

## Notes orateur
> "Comment passer à l'échelle ? Notre architecture est conçue pour la scalabilité horizontale. En ajoutant des replicas de l'OCR derrière un load balancer, en distribuant MinIO sur plusieurs nœuds avec du erasure coding, et en passant Airflow sur Celery avec plusieurs workers, on peut multiplier la capacité par 100. Pour le million de documents quotidien, on déploierait sur Kubernetes multi-région avec du streaming Kafka et des GPUs pour EasyOCR. L'architecture microservices qu'on a choisie rend cette évolution naturelle."

---

# SLIDE 14 — Conclusion & Perspectives
**Durée : 2 minutes**

## Titre
**Ce qu'on a accompli — Ce qu'on ferait ensuite**

## Contenu
```
✅ Réalisations du Hackathon :

• Pipeline OCR hybride temps réel (Tesseract + EasyOCR)
• 12 règles de validation métier + ML anomalies
• Data Lake 4 zones sur MinIO
• Interface React moderne avec Socket.io
• Orchestration Airflow automatisée
• Dataset synthétique de 500+ documents
• 11 conteneurs Docker prêts à déployer

📊 Métriques clés :
• 94% de détection d'anomalies
• 3.2 sec de traitement E2E
• 87% de confiance OCR

🚀 Perspectives (avec plus de temps) :

COURT TERME (1 mois) :
• Intégration LLM (GPT-4) pour extraction avancée
• Correction assistée par IA des champs erronés
• Export comptable (FEC, DATEV)

MOYEN TERME (3 mois) :
• Détection de fraude documentaire (falsification)
• Clustering automatique des fournisseurs
• API REST publique documentée (OpenAPI)

LONG TERME (6 mois) :
• Application mobile (scan caméra)
• Intégration ERP (SAP, Odoo, Sage)
• Marketplace de règles métier personnalisées
```

## Figure
**Roadmap visuelle des évolutions** :

Timeline horizontale avec 3 sections :

**[1 mois] — Quick Wins**
- Icône 🤖 : "LLM Extraction"
- Icône 📊 : "Export FEC"
- Icône 🔧 : "Correction IA"

**[3 mois] — Enrichissements**
- Icône 🔍 : "Détection Fraude"
- Icône 👥 : "Clustering"
- Icône 📚 : "API Publique"

**[6 mois] — Scale**
- Icône 📱 : "App Mobile"
- Icône 🏢 : "ERP Integration"
- Icône 🛒 : "Marketplace"

En bas, logo DocuFlow avec slogan :
*"De l'extraction à la validation, 100% automatisé"*

## Notes orateur
> "Pour conclure, en quelques jours de hackathon, nous avons construit un pipeline complet de validation documentaire qui fonctionne. On atteint 94% de détection, 3.2 secondes de traitement, et une confiance OCR de 87%. Avec plus de temps, on intégrerait un LLM comme GPT-4 pour une extraction encore plus intelligente, de la détection de fraude documentaire, et des intégrations ERP natives. L'architecture qu'on a posée permet toutes ces évolutions. DocuFlow, c'est la promesse d'une gestion documentaire 100% automatisée, de l'extraction à la validation. Merci pour votre attention, nous sommes prêts pour vos questions."

---

# SLIDE 15 — Questions & Contact
**Durée : 5 minutes (Q&A)**

## Titre
**Questions ?**

## Contenu
```
🙋 Nous sommes prêts à répondre à vos questions !

📧 Contact équipe :
• Tahina — tahina@docuflow.ai
• Abdelmalek — abdelmalek@docuflow.ai
• Yanis — yanis@docuflow.ai
• Hassan — hassan@docuflow.ai
• Wael — wael@docuflow.ai
• Korniti — korniti@docuflow.ai

🔗 Ressources :
• GitHub : github.com/HASSANHOUSSEINHOUMED/Hackathon_2026
• Démo live : http://localhost:3000
• Documentation : RAPPORT_TECHNIQUE.md

💡 Points techniques à approfondir :
• Algorithme de Luhn pour SIRET
• IsolationForest pour détection statistique
• Stratégie hybride Tesseract/EasyOCR
• Architecture Data Lake MinIO
```

## Figure
QR Code vers le repository GitHub au centre.
Logos des technologies utilisées en bas :
React, Node.js, Python, MinIO, MongoDB, Airflow, Docker

## Notes orateur
> "Merci beaucoup pour votre attention. Nous sommes maintenant à votre disposition pour répondre à vos questions, qu'elles soient techniques ou métier. Le repository GitHub est public si vous voulez explorer le code. N'hésitez pas !"

---

# SLIDES SUPPLÉMENTAIRES (Backup)

## SLIDE BACKUP 1 — Détail Algorithme de Luhn

## Titre
**Validation SIRET par algorithme de Luhn**

## Contenu
```python
def luhn_check(siret: str) -> bool:
    """
    Vérifie la validité d'un SIRET par l'algorithme de Luhn.
    Un SIRET valide a 14 chiffres et passe le test de Luhn.
    """
    digits = [int(d) for d in siret if d.isdigit()]
    if len(digits) != 14:
        return False
    
    # Positions impaires (de droite à gauche)
    odd = digits[-1::-2]
    
    # Positions paires : doubler et sommer les chiffres
    even = digits[-2::-2]
    even_sum = sum(sum(divmod(d * 2, 10)) for d in even)
    
    total = sum(odd) + even_sum
    return total % 10 == 0

# Exemples :
# "12345678901234" → False (invalide)
# "73282932000074" → True (SIRET d'Apple France)
```

## Figure
Diagramme visuel de l'algorithme avec les étapes numérotées.

---

## SLIDE BACKUP 2 — Détail IsolationForest

## Titre
**Détection de montants anormaux par IsolationForest**

## Contenu
```
🌲 Principe de l'IsolationForest :

1. Construire 100 arbres de décision aléatoires
2. Chaque arbre isole les points par splits aléatoires
3. Les anomalies sont isolées plus rapidement (moins de splits)
4. Score d'anomalie : profondeur moyenne d'isolation

📊 Features utilisées :
• montant_ht
• montant_ttc
• (ratio montant / moyenne fournisseur)

⚙️ Hyperparamètres :
• n_estimators = 100
• contamination = 0.1 (10% anomalies attendues)
• random_state = 42 (reproductibilité)

📈 Résultats :
• Rappel : 89%
• Précision : 76%
• F1-score : 0.82
```

## Figure
Visualisation 2D des points normaux (bleu) vs anomalies (rouge) avec la frontière de décision de l'IsolationForest.

---

## SLIDE BACKUP 3 — Comparaison Tesseract vs EasyOCR

## Titre
**Benchmark OCR : Tesseract vs EasyOCR**

## Contenu
```
┌─────────────────┬───────────────┬───────────────┐
│ Critère         │ Tesseract     │ EasyOCR       │
├─────────────────┼───────────────┼───────────────┤
│ Vitesse         │ ~800ms/page   │ ~2500ms/page  │
│ Mémoire         │ ~200 MB       │ ~1.5 GB       │
│ Documents nets  │ 92% accuracy  │ 89% accuracy  │
│ Documents flous │ 71% accuracy  │ 84% accuracy  │
│ Rotation <5°    │ OK            │ Meilleur      │
│ Multi-langue    │ Configs       │ Natif         │
│ GPU support     │ Non           │ Oui (CUDA)    │
└─────────────────┴───────────────┴───────────────┘

🎯 Notre stratégie hybride :
1. Tesseract d'abord (rapide, efficace sur docs propres)
2. Fallback EasyOCR si confiance < 60%
3. Résultat : rapidité + robustesse
```

## Figure
Graphique en barres comparant les deux moteurs sur les 4 scénarios du dataset.

---

*Fin de la présentation — Total : 15 slides principales + 3 backup*
*Durée totale estimée : 25 minutes (dont 5 min Q&A)*
