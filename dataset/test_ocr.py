"""
test_ocr.py — Test rapide OCR sur le dataset existant
- PDFs raw/   : extraction directe via PyMuPDF (texte embarqué)
- Images noisy/ : Tesseract OCR
- Comparaison avec ground truth dataset/labels/
"""

import os
import json
import re
import time
from pathlib import Path

import fitz          # PyMuPDF
import pytesseract
from PIL import Image

DATASET_DIR = Path(__file__).parent
RAW_DIR = DATASET_DIR / "raw"
NOISY_DIR = DATASET_DIR / "noisy"
LABELS_DIR = DATASET_DIR / "labels"

TESSERACT_CONFIG = "--oem 3 --psm 6 -l fra"


# ─────────────────────────────────────────
# Extraction de texte
# ─────────────────────────────────────────

def extract_text_pdf(pdf_path: Path) -> tuple[str, float]:
    """Extrait le texte d'un PDF via PyMuPDF (pas d'OCR)."""
    t0 = time.time()
    doc = fitz.open(str(pdf_path))
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text.strip(), round((time.time() - t0) * 1000)


def extract_text_image(img_path: Path) -> tuple[str, float, float]:
    """Extrait le texte d'une image via Tesseract. Retourne (texte, confiance, ms)."""
    t0 = time.time()
    img = Image.open(str(img_path))
    data = pytesseract.image_to_data(img, config=TESSERACT_CONFIG,
                                     output_type=pytesseract.Output.DICT)
    # Confiance moyenne (mots valides uniquement)
    confidences = [int(c) for c in data['conf'] if str(c).strip() != '-1']
    avg_conf = round(sum(confidences) / len(confidences) / 100, 3) if confidences else 0.0
    text = pytesseract.image_to_string(img, config=TESSERACT_CONFIG)
    ms = round((time.time() - t0) * 1000)
    return text.strip(), avg_conf, ms


# ─────────────────────────────────────────
# Parsing du texte extrait (format raw PDFs : "clé: valeur")
# ─────────────────────────────────────────

def parse_kv_text(text: str) -> dict:
    """Parse le format 'clé: valeur' produit par l'ancien generate.py."""
    result = {}
    for line in text.splitlines():
        if ': ' in line:
            key, _, value = line.partition(': ')
            key = key.strip().lower().replace(' ', '_')
            value = value.strip()
            # Conversion numérique
            try:
                value = float(value)
            except ValueError:
                pass
            result[key] = value
    return result


# ─────────────────────────────────────────
# Comparaison avec ground truth
# ─────────────────────────────────────────

def compare_fields(extracted: dict, expected: dict) -> dict:
    """
    Compare les champs extraits avec le ground truth.
    Retourne un rapport par champ.
    """
    report = {}
    for key, expected_val in expected.items():
        extracted_val = extracted.get(key)
        if extracted_val is None:
            report[key] = {"status": "ABSENT", "expected": expected_val, "got": None}
        else:
            # Comparaison tolérante pour les nombres (arrondi 2 décimales)
            if isinstance(expected_val, (int, float)):
                match = abs(float(extracted_val) - float(expected_val)) < 0.01
            else:
                match = str(extracted_val).strip() == str(expected_val).strip()
            report[key] = {
                "status": "OK" if match else "MISMATCH",
                "expected": expected_val,
                "got": extracted_val,
            }
    return report


def field_accuracy(report: dict) -> float:
    if not report:
        return 0.0
    ok = sum(1 for v in report.values() if v["status"] == "OK")
    return round(ok / len(report) * 100, 1)


# ─────────────────────────────────────────
# Calcul CER (Character Error Rate)
# ─────────────────────────────────────────

def compute_cer(predicted: str, ground_truth: str) -> float:
    """CER via distance d'édition caractère par caractère."""
    # Distance de Levenshtein simple
    p, g = list(predicted), list(ground_truth)
    if not g:
        return 0.0
    prev = list(range(len(g) + 1))
    for i, cp in enumerate(p):
        curr = [i + 1]
        for j, cg in enumerate(g):
            curr.append(min(prev[j] + (0 if cp == cg else 1),
                            curr[-1] + 1,
                            prev[j + 1] + 1))
        prev = curr
    distance = prev[len(g)]
    return round(distance / max(len(g), 1) * 100, 2)


# ─────────────────────────────────────────
# Runner principal
# ─────────────────────────────────────────

def run_tests() -> None:
    results = {"pdf": [], "noisy": [], "errors": []}

    # ── PDFs raw ──────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  TEST PDFs (extraction directe PyMuPDF)")
    print("═" * 60)

    pdf_files = sorted(RAW_DIR.glob("*.pdf"))
    for pdf_path in pdf_files:
        doc_id = pdf_path.stem
        label_path = LABELS_DIR / f"{doc_id}.json"
        if not label_path.exists():
            continue

        with open(label_path, encoding="utf-8") as f:
            label = json.load(f)

        try:
            text, ms = extract_text_pdf(pdf_path)
            extracted = parse_kv_text(text)
            report = compare_fields(extracted, label["expected_fields"])
            accuracy = field_accuracy(report)

            # CER : on compare le texte brut des valeurs extraites vs attendus
            gt_text = " ".join(str(v) for v in label["expected_fields"].values())
            ext_text = " ".join(str(extracted.get(k, "")) for k in label["expected_fields"])
            cer = compute_cer(ext_text, gt_text)

            results["pdf"].append({
                "doc_id": doc_id,
                "type": label["type"],
                "scenario": label["scenario"],
                "accuracy_pct": accuracy,
                "cer_pct": cer,
                "duration_ms": ms,
                "fields": report,
            })

            status_icon = "✓" if accuracy == 100 else ("~" if accuracy >= 50 else "✗")
            print(f"  {status_icon} {doc_id:<35} acc={accuracy:5.1f}%  CER={cer:5.1f}%  ({ms}ms)")

        except Exception as e:
            results["errors"].append({"doc_id": doc_id, "error": str(e)})
            print(f"  ! {doc_id:<35} ERREUR: {e}")

    # ── Images noisy ──────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  TEST IMAGES NOISY (Tesseract OCR)")
    print("═" * 60)

    img_files = sorted(NOISY_DIR.glob("*.jpg"))
    for img_path in img_files:
        doc_id = img_path.stem
        label_path = LABELS_DIR / f"{doc_id}.json"
        if not label_path.exists():
            continue

        with open(label_path, encoding="utf-8") as f:
            label = json.load(f)

        try:
            text, conf, ms = extract_text_image(img_path)
            extracted = parse_kv_text(text)
            report = compare_fields(extracted, label["expected_fields"])
            accuracy = field_accuracy(report)

            gt_text = " ".join(str(v) for v in label["expected_fields"].values())
            ext_text = " ".join(str(extracted.get(k, "")) for k in label["expected_fields"])
            cer = compute_cer(ext_text, gt_text)

            results["noisy"].append({
                "doc_id": doc_id,
                "type": label["type"],
                "scenario": label["scenario"],
                "ocr_confidence": conf,
                "accuracy_pct": accuracy,
                "cer_pct": cer,
                "duration_ms": ms,
                "fields": report,
            })

            status_icon = "✓" if accuracy == 100 else ("~" if accuracy >= 50 else "✗")
            print(f"  {status_icon} {doc_id:<35} acc={accuracy:5.1f}%  CER={cer:5.1f}%  "
                  f"conf={conf:.2f}  ({ms}ms)")

        except Exception as e:
            results["errors"].append({"doc_id": doc_id, "error": str(e)})
            print(f"  ! {doc_id:<35} ERREUR: {e}")

    # ── Résumé ────────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  RÉSUMÉ")
    print("═" * 60)

    if results["pdf"]:
        avg_acc = sum(r["accuracy_pct"] for r in results["pdf"]) / len(results["pdf"])
        avg_cer = sum(r["cer_pct"] for r in results["pdf"]) / len(results["pdf"])
        print(f"  PDFs ({len(results['pdf'])} docs)   : précision moy={avg_acc:.1f}%  CER moy={avg_cer:.1f}%")

    if results["noisy"]:
        avg_acc = sum(r["accuracy_pct"] for r in results["noisy"]) / len(results["noisy"])
        avg_cer = sum(r["cer_pct"] for r in results["noisy"]) / len(results["noisy"])
        avg_conf = sum(r["ocr_confidence"] for r in results["noisy"]) / len(results["noisy"])
        print(f"  Noisy ({len(results['noisy'])} imgs) : précision moy={avg_acc:.1f}%  "
              f"CER moy={avg_cer:.1f}%  confiance OCR={avg_conf:.2f}")

    if results["errors"]:
        print(f"\n  Erreurs : {len(results['errors'])}")
        for e in results["errors"]:
            print(f"    - {e['doc_id']}: {e['error']}")

    # Sauvegarde rapport JSON
    report_path = DATASET_DIR / "ocr_test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Rapport sauvegardé : {report_path}")


if __name__ == "__main__":
    run_tests()
