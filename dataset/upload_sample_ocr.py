#!/usr/bin/env python3
"""Upload a small OCR sample (3 docs) and print concise extraction results."""
from pathlib import Path
import requests

BASE_URL = "http://localhost:4000/api/process"
RAW_DIR = Path("./test_docs/raw")


def pick_sample_files() -> list[Path]:
    wanted_prefixes = ["FAC_", "DEV_", "RIB_"]
    selected: list[Path] = []
    for prefix in wanted_prefixes:
        match = sorted(RAW_DIR.glob(f"{prefix}*.pdf"))
        if match:
            selected.append(match[0])
    return selected


def main() -> None:
    files = pick_sample_files()
    if len(files) < 3:
        print(f"ERROR: expected 3 files, got {len(files)}")
        for f in files:
            print(f"  - {f.name}")
        raise SystemExit(1)

    print("Uploading sample files:")
    for f in files:
        print(f"  - {f.name}")

    handles = []
    form_files = []
    try:
        for path in files:
            fh = open(path, "rb")
            handles.append(fh)
            form_files.append(("documents", (path.name, fh, "application/pdf")))

        resp = requests.post(BASE_URL, files=form_files, timeout=240)
        print(f"HTTP {resp.status_code}")
        if resp.status_code != 200:
            print(resp.text)
            raise SystemExit(2)

        data = resp.json()
        print(f"total={data.get('total')} success={data.get('success')}")

        for item in data.get("results", []):
            entities = item.get("entities") or {}
            print("---")
            print(f"file={item.get('file_name')} type={item.get('type')} ocr={item.get('ocr_confidence')}")
            print(
                "siret={siret} raison_sociale={raison_sociale} montant_ttc={montant_ttc}".format(
                    siret=entities.get("siret"),
                    raison_sociale=entities.get("raison_sociale"),
                    montant_ttc=entities.get("montant_ttc"),
                )
            )
    finally:
        for h in handles:
            try:
                h.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
