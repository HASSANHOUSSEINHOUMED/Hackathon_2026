#!/usr/bin/env bash
# ═══════════════════════════════════════
# Test end-to-end DocuFlow
# ═══════════════════════════════════════
set -euo pipefail

BACKEND="http://localhost:4000"
OCR="http://localhost:5001"
VALIDATION="http://localhost:5002"
STORAGE="http://localhost:5003"

PASS=0
FAIL=0
TOTAL=0

check() {
    local name=$1
    local result=$2
    TOTAL=$((TOTAL + 1))
    if [ "$result" -eq 0 ]; then
        echo "  ✅ $name"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $name"
        FAIL=$((FAIL + 1))
    fi
}

echo "╔══════════════════════════════════════╗"
echo "║     DocuFlow — Tests End-to-End      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ═══════════════════════════════════════
# 1. Health checks
# ═══════════════════════════════════════
echo "📋 1. Health Checks"

curl -sf "$BACKEND/api/health" > /dev/null 2>&1
check "Backend API" $?

curl -sf "$OCR/api/health" > /dev/null 2>&1
check "OCR Service" $?

curl -sf "$VALIDATION/api/health" > /dev/null 2>&1
check "Validation Service" $?

curl -sf "$STORAGE/health" > /dev/null 2>&1
check "Storage API" $?

# ═══════════════════════════════════════
# 2. Validation Service
# ═══════════════════════════════════════
echo ""
echo "📋 2. Validation Service"

VALIDATION_RESP=$(curl -sf -X POST "$VALIDATION/api/validate" \
    -H "Content-Type: application/json" \
    -d '{
        "documents": [
            {
                "document_id": "TEST_FAC_001",
                "type": "facture",
                "entities": {
                    "siret": "44306184100047",
                    "montant_ht": 1000,
                    "tva": 200,
                    "montant_ttc": 1200,
                    "raison_sociale": "Test Company SAS"
                }
            }
        ]
    }' 2>/dev/null)
echo "$VALIDATION_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status'] in ('OK','WARNING','ERROR')" 2>/dev/null
check "Validation de document" $?

RULES_RESP=$(curl -sf "$VALIDATION/api/rules" 2>/dev/null)
echo "$RULES_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['total'] >= 12" 2>/dev/null
check "Liste des règles (≥12)" $?

# ═══════════════════════════════════════
# 3. Backend API
# ═══════════════════════════════════════
echo ""
echo "📋 3. Backend API"

DOCS_RESP=$(curl -sf "$BACKEND/api/documents" 2>/dev/null)
echo "$DOCS_RESP" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null
check "Liste des documents" $?

SUPPLIERS_RESP=$(curl -sf "$BACKEND/api/suppliers" 2>/dev/null)
echo "$SUPPLIERS_RESP" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null
check "Liste des fournisseurs" $?

# ═══════════════════════════════════════
# 4. Upload & Traitement
# ═══════════════════════════════════════
echo ""
echo "📋 4. Upload & Traitement"

# Créer un fichier PDF de test minimal
TEST_PDF="/tmp/test_docuflow.pdf"
python3 -c "
from reportlab.pdfgen import canvas
c = canvas.Canvas('$TEST_PDF')
c.drawString(100, 750, 'FACTURE N° TEST-001')
c.drawString(100, 730, 'SIRET: 443 061 841 00047')
c.drawString(100, 710, 'Montant HT: 1 000,00 EUR')
c.drawString(100, 690, 'TVA 20%: 200,00 EUR')
c.drawString(100, 670, 'Montant TTC: 1 200,00 EUR')
c.save()
" 2>/dev/null

if [ -f "$TEST_PDF" ]; then
    UPLOAD_RESP=$(curl -sf -X POST "$BACKEND/api/process" \
        -F "files=@$TEST_PDF" 2>/dev/null)
    echo "$UPLOAD_RESP" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null
    check "Upload de document" $?
    rm -f "$TEST_PDF"
else
    echo "  ⚠️  ReportLab non installé, skip upload test"
fi

# ═══════════════════════════════════════
# 5. Storage
# ═══════════════════════════════════════
echo ""
echo "📋 5. Storage"

STATS_RESP=$(curl -sf "$STORAGE/stats" 2>/dev/null)
echo "$STATS_RESP" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null
check "Storage stats" $?

# ═══════════════════════════════════════
# Résumé
# ═══════════════════════════════════════
echo ""
echo "═══════════════════════════════════════"
echo "Résultat : $PASS/$TOTAL tests passés"
if [ "$FAIL" -gt 0 ]; then
    echo "⚠️  $FAIL test(s) échoué(s)"
    exit 1
else
    echo "✅ Tous les tests passent !"
    exit 0
fi
