Générateur de Dataset – Documents Administratifs (Hackathon 2026)

Ce projet permet de générer automatiquement un dataset de documents administratifs fictifs (PDF et images) destiné à entraîner et tester un pipeline d’analyse documentaire (OCR, extraction d’informations et détection d’anomalies).

Le dataset contient plusieurs types de documents d’entreprise simulant des situations réelles rencontrées dans les processus de vérification documentaire.

Objectif

Créer un dataset contenant :

des documents cohérents

des documents incohérents

des documents expirés

des documents dégradés (simulation de scan)

Ces documents servent à tester un pipeline comprenant :

OCR

extraction de champs

détection d’anomalies entre documents

Types de documents générés

Le générateur crée les types de documents suivants :

Facture fournisseur

Champs générés :

SIRET émetteur

SIRET client

numéro de facture

date d’émission

montant HT

TVA (20 %)

montant TTC

RIB

adresse

Devis

Champs générés :

SIRET émetteur

date du devis

date de validité

désignation

quantité

prix unitaire

total HT

TVA

total TTC

Attestation SIRET

Champs générés :

SIRET

raison sociale

adresse

date de délivrance

date d’expiration

Attestation URSSAF

Champs générés :

SIRET

raison sociale

date début validité

date fin validité

numéro d’attestation

Extrait Kbis

Champs générés :

SIRET

SIREN

raison sociale

forme juridique

capital social

date immatriculation

dirigeant

RIB

Champs générés :

IBAN

BIC

titulaire

domiciliation bancaire

SIRET associé

Scénarios simulés dans le dataset

Le dataset est composé de 4 familles de scénarios.

Scénario A — Documents cohérents (≈30%)

Documents parfaitement valides.

Exemple :

même SIRET sur facture, URSSAF et Kbis

montants corrects

dates valides

RIB correspondant à l’entreprise

Ces documents servent de référence positive pour l’IA.

Scénario B — Incohérences inter-documents (≈30%)

Les informations ne correspondent pas entre les documents.

Exemples :

SIRET différent entre facture et URSSAF

TVA incorrecte

montant TTC incorrect

nom d’entreprise différent entre Kbis et facture

IBAN appartenant à une autre entreprise

Ces cas servent à entraîner la détection d’anomalies.

Scénario C — Documents expirés ou invalides (≈20%)

Documents valides mais périmés.

Exemples :

attestation URSSAF expirée

devis expiré

extrait Kbis de plus de 3 mois

attestation SIRET d’entreprise radiée

Scénario D — Documents bruités (≈20%)

Simulation de documents mal scannés.

Transformations appliquées :

rotation aléatoire (-15° à +15°)

flou gaussien

bruit

réduction de qualité

contraste dégradé

Ces documents servent à tester la robustesse de l’OCR.

Structure du projet
dataset/
│
├── raw/
│   Documents PDF générés proprement
│
├── noisy/
│   Versions dégradées (simulation scan)
│
├── labels/
│   Fichiers JSON contenant la vérité terrain
│
└── generate.py
    Script principal de génération du dataset
Ground Truth (vérité terrain)

Chaque document possède un fichier JSON associé contenant les informations attendues.

Exemple :

{
  "document_id": "FAC_001",
  "type": "facture",
  "scenario": "A",
  "degradation": "none",
  "expected_fields": {
    "siret": "12345678901234",
    "montant_ht": 1250.00,
    "tva": 250.00,
    "ttc": 1500.00,
    "date_emission": "2025-03-10"
  },
  "expected_anomalies": []
}

Ces fichiers permettent d’évaluer :

la précision de l’OCR

l’extraction des champs

la détection d’anomalies

Installation

Installer les dépendances Python :

pip install faker reportlab pillow numpy opencv-python pdf2image
Installation de Poppler (Windows)

La bibliothèque pdf2image nécessite Poppler.

Télécharger :

https://github.com/oschwartz10612/poppler-windows/releases

Extraire le dossier.

Ajouter au PATH :

C:\poppler\Library\bin
Génération du dataset

Lancer :

python generate.py

Le script va :

générer des entreprises fictives

créer les documents

produire les fichiers JSON de vérité terrain

générer les versions dégradées

Paramétrage

Dans generate.py, le nombre de documents peut être modifié :

generate_dataset(100)

Exemple :

generate_dataset(200)
Technologies utilisées

Python – langage principal

Faker – génération de données fictives

ReportLab – génération de PDF

OpenCV – dégradation des images

pdf2image – conversion PDF → image

Validation du dataset

Le dataset respecte les critères suivants :

au moins 10 entreprises fictives

tous les types de documents représentés

les 4 scénarios couverts

un fichier ground truth JSON par document

documents PDF + images dégradées

Utilisation prévue

Ce dataset est conçu pour :

entraînement de modèles OCR

extraction automatique d’informations

détection d’anomalies documentaires

validation de pipelines d’analyse documentaire