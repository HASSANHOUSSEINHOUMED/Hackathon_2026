#!/usr/bin/env python3
"""Créer des documents de test simples."""
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

os.makedirs('./test_docs', exist_ok=True)

# Créer 3 documents de test simples
docs = [
    ('facture_001.pdf', 'FACTURE\nSIRET: 12345678901234\nMontant: 1500€\nDate: 2024-01-15'),
    ('facture_002.pdf', 'FACTURE\nSIRET: 98765432109876\nMontant: 2300€\nDate: 2024-01-20'),
    ('devis_001.pdf', 'DEVIS\nSIRET: 11111111111111\nMontant: 5000€\nDate: 2024-01-10')
]

for filename, text in docs:
    path = f'./test_docs/{filename}'
    c = canvas.Canvas(path, pagesize=letter)
    lines = text.split('\n')
    y = 750
    for line in lines:
        c.drawString(50, y, line)
        y -= 20
    c.save()
    print(f'✅ Créé: {filename}')

print(f'\n✅ {len(docs)} documents de test créés!')
