#!/usr/bin/env python3
"""Créer des documents PDF en français pour les tests."""
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

base_dir = r'c:\Users\hassa\Ecole_IPSSI\Hackathon_2026\dataset\test_docs'

# Documents en français
docs = {
    'facture_001.pdf': '''FACTURE

Émetteur: Entreprise Alpha SARL
SIRET: 12345678901234
Adresse: 123 Rue de Paris, 75001 Paris

Client: Entreprise Client
Email: contact@client.fr

Montant HT: 1 200,00 €
TVA 20%: 240,00 €
Montant TTC: 1 440,00 €

Conditions: Net 30 jours
Date: 15 janvier 2024''',
    
    'devis_001.pdf': '''DEVIS

Émetteur: Société Beta EURL
SIRET: 11111111111111
Adresse: 456 Avenue Lyon, 75002 Paris

Objet: Prestation de services IT

Montant HT: 4 000,00 €
TVA 20%: 800,00 €
Montant TTC: 4 800,00 €

Validité: 30 jours
Date: 10 janvier 2024''',
    
    'attestation_urssaf_001.pdf': '''ATTESTATION URSSAF

Entreprise: Gamma Ltd
SIRET: 44444444444444
Période: Décembre 2023

COTISATIONS SOCIALES
Montant versé: 800,00 €
Statut: Régularisée
Date paiement: 05 janvier 2024''',
    
    'kbis_001.pdf': '''EXTRAIT KBIS

Entreprise: Delta Commerce SARL
SIRET: 55555555555555
SIREN: 555555555
RCS: Paris 555 555 555

Activité: Commerce de détail
Adresse: 789 Boulevard Saint-Germain, 75005 Paris

Immatriculation: 1er janvier 2020''',
}

for filename, text in docs.items():
    path = os.path.join(base_dir, filename)
    c = canvas.Canvas(path, pagesize=A4)
    lines = text.split('\n')
    y = 800
    for line in lines:
        c.drawString(30, y, line)
        y -= 15
    c.save()
    print(f'✅ {filename} créé')

print(f'\n✅ {len(docs)} documents PDF en français créés!')
