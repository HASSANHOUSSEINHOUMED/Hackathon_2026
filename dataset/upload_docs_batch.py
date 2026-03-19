#!/usr/bin/env python3
"""Upload dataset PDFs to backend in batches of 10 files."""
from pathlib import Path
import requests

BASE_URL = "http://localhost:4000/api/process"
PDF_DIR = Path("./test_docs/raw")
BATCH_SIZE = 10
TIMEOUT = 240


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def main() -> None:
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print("No PDFs found in test_docs/raw")
        raise SystemExit(1)

    print(f"Uploading {len(pdfs)} PDFs in batches of {BATCH_SIZE}...")
    total_success = 0
    total_error = 0

    for idx, batch in enumerate(chunked(pdfs, BATCH_SIZE), start=1):
        files = []
        handlers = []
        try:
            for p in batch:
                fh = open(p, "rb")
                handlers.append(fh)
                files.append(("documents", (p.name, fh, "application/pdf")))

            resp = requests.post(BASE_URL, files=files, timeout=TIMEOUT)
            if resp.status_code != 200:
                total_error += len(batch)
                print(f"Batch {idx}: HTTP {resp.status_code} ({len(batch)} docs)")
                continue

            data = resp.json()
            success = int(data.get("success", 0))
            total = int(data.get("total", len(batch)))
            errs = max(total - success, 0)
            total_success += success
            total_error += errs
            print(f"Batch {idx}: success={success}/{total}")
        except Exception as exc:
            total_error += len(batch)
            print(f"Batch {idx}: exception={exc}")
        finally:
            for h in handlers:
                try:
                    h.close()
                except Exception:
                    pass

    print("Done")
    print(f"Total success: {total_success}")
    print(f"Total errors: {total_error}")


if __name__ == "__main__":
    main()
