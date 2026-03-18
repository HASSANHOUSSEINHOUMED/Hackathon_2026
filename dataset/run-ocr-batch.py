"""
Envoie les PDFs générés au service OCR Docker et sauvegarde les résultats JSON.
Usage :
    python run_ocr_batch.py [--input ./output/raw] [--output ./output/ocr_results] [--ocr-url http://localhost:5001]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests
from tqdm import tqdm


def send_to_ocr(pdf_path: Path, ocr_url: str, timeout: int = 180) -> dict:
    """Envoie un PDF au service OCR et retourne le résultat JSON."""
    with open(pdf_path, "rb") as f:
        files = {"document": (pdf_path.name, f, "application/pdf")}
        resp = requests.post(f"{ocr_url}/api/ocr", files=files, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Batch OCR des PDFs générés via le service Docker")
    parser.add_argument("--input", type=str, default="./output/raw", help="Répertoire des PDFs")
    parser.add_argument("--output", type=str, default="./output/ocr_results", help="Répertoire de sortie JSON")
    parser.add_argument("--ocr-url", type=str, default="http://localhost:5001", help="URL du service OCR")
    parser.add_argument("--timeout", type=int, default=180, help="Timeout par document (secondes)")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        print(f"Répertoire introuvable : {input_dir}")
        sys.exit(1)

    # Vérifier que le service OCR est accessible
    try:
        health = requests.get(f"{args.ocr_url}/api/health", timeout=10)
        health.raise_for_status()
        print(f"Service OCR OK : {health.json().get('status')}")
    except Exception as e:
        print(f"Service OCR inaccessible ({args.ocr_url}) : {e}")
        print("Assurez-vous que Docker est lancé : docker compose up -d ocr-service")
        sys.exit(1)

    pdfs = sorted(input_dir.glob("*.pdf"))
    print(f"\n{len(pdfs)} PDFs à traiter dans {input_dir}")

    # Ignorer les PDFs déjà traités (reprise après interruption)
    already_done = {f.stem for f in output_dir.glob("*.json")}
    pdfs_to_process = [p for p in pdfs if p.stem not in already_done]
    if already_done:
        print(f"{len(already_done)} déjà traités, {len(pdfs_to_process)} restants")

    success = 0
    errors = 0
    total_time = 0

    for pdf in tqdm(pdfs_to_process, desc="OCR batch", ncols=80):
        doc_id = pdf.stem
        try:
            start = time.time()
            result = send_to_ocr(pdf, args.ocr_url, timeout=args.timeout)
            elapsed = time.time() - start
            total_time += elapsed

            # Remplacer le document_id (hash MD5) par l'ID du fichier
            # pour correspondre au ground truth (FAC_001, DEV_016, etc.)
            result["document_id"] = doc_id

            out_path = output_dir / f"{doc_id}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            success += 1
        except requests.exceptions.Timeout:
            print(f"\n  Timeout : {doc_id}")
            errors += 1
        except Exception as e:
            print(f"\n  Erreur {doc_id} : {e}")
            errors += 1

    print(f"\n{'═' * 50}")
    print(f"  Traités : {success}/{len(pdfs_to_process)}")
    print(f"  Erreurs : {errors}")
    if success > 0:
        print(f"  Temps moyen : {total_time / success:.1f}s / document")
    print(f"  Résultats : {output_dir}")
    print(f"{'═' * 50}")
    print(f"\nLancez maintenant l'évaluation :")
    print(f"  python evaluate_ocr.py")


if __name__ == "__main__":
    main()