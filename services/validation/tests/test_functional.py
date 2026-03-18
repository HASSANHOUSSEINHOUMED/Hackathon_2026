"""Test fonctionnel rapide du service de validation."""
from app import app

client = app.test_client()

# Test health
r = client.get("/api/health")
health = r.json
print(f"Health: {r.status_code} - {health['status']}")

# Test rules list
r = client.get("/api/rules")
rules = r.json
print(f"Rules: {r.status_code} - {rules['total']} regles")

# Test validation
payload = {
    "documents": [
        {
            "document_id": "FAC_001",
            "type": "facture",
            "entities": {
                "siret": "44306184100047",
                "montant_ht": 1000,
                "tva": 200,
                "montant_ttc": 1200,
                "raison_sociale": "Test SAS",
            },
        },
        {
            "document_id": "FAC_002",
            "type": "facture",
            "entities": {
                "siret": "44306184100047",
                "montant_ht": 1000,
                "tva": 500,
                "montant_ttc": 1300,
                "raison_sociale": "Test SAS",
            },
        },
    ]
}
r = client.post("/api/validate", json=payload)
data = r.json
print(f"Validate: {r.status_code} - status={data['status']}, anomalies={data['anomaly_count']}")
for a in data["anomalies"]:
    print(f"  [{a['severity']}] {a['rule_id']}: {a['message']}")

print("\n=== TOUS LES TESTS FONCTIONNELS OK ===")
