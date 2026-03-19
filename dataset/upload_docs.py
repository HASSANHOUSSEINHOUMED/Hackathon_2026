#!/usr/bin/env python3
"""Upload les documents générés vers le backend."""
import os
import requests
from pathlib import Path

BASE_URL = "http://localhost:4000/api"
OUTPUT_DIR = "./test_docs/raw"

files_to_upload = sorted(Path(OUTPUT_DIR).glob("*.pdf"))  # Tous les documents

if not files_to_upload:
    print("❌ Aucun PDF trouvé!")
    exit(1)

print(f"📤 Uploading {len(files_to_upload)} documents...")

for pdf_file in files_to_upload:
    try:
        with open(pdf_file, 'rb') as f:
            files = {'documents': (pdf_file.name, f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/process", files=files, timeout=60)
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ {pdf_file.name}")
            else:
                print(f"⚠️  {pdf_file.name} - Status {response.status_code}")
    except Exception as e:
        print(f"❌ {pdf_file.name} - {str(e)}")

print("\n✅ Upload terminé!")
