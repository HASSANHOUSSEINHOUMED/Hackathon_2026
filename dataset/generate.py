"""
Orchestrateur principal — Génère le dataset complet de documents administratifs.

Usage :
    python generate.py --n 15 --output ./output --scenarios all
"""
import argparse
import json
import random
import sys
from pathlib import Path

from tqdm import tqdm

# Ajouter le répertoire courant au path
sys.path.insert(0, str(Path(__file__).parent))

from company_factory import CompanyFactory
from config import (
    DEGRADATION_LEVELS,
    DOC_TYPES,
    N_DOCS,
    SCENARIOS,
    TVA_RATES,
)
from degrade import degrade_pdf_to_image, pdf_to_clean_image
from generators.attestation_siret import generate_attestation_siret
from generators.attestation_urssaf import generate_attestation_urssaf
from generators.devis import generate_devis
from generators.facture import generate_facture
from generators.kbis import generate_kbis
from generators.rib import generate_rib

# Correspondance type → fonction de génération
GENERATORS = {
    "facture": generate_facture,
    "devis": generate_devis,
    "attestation_urssaf": generate_attestation_urssaf,
    "attestation_siret": generate_attestation_siret,
    "kbis": generate_kbis,
    "rib": generate_rib,
}

# Préfixes par type
PREFIXES = {
    "facture": "FAC",
    "devis": "DEV",
    "attestation_urssaf": "URSSAF",
    "attestation_siret": "SIRET",
    "kbis": "KBIS",
    "rib": "RIB",
}


def choose_scenario() -> str:
    """Choisit un scénario aléatoire selon les probabilités configurées."""
    rand = random.random()
    cumul = 0.0
    for scenario, proba in SCENARIOS.items():
        cumul += proba
        if rand <= cumul:
            return scenario
    return "coherent"


def generate_document(
    doc_type: str,
    company,
    output_dir: Path,
    doc_index: int,
    scenario: str,
) -> dict:
    """
    Génère un document unique avec son ground truth.

    Returns:
        dict contenant les métadonnées et le ground truth
    """
    prefix = PREFIXES[doc_type]
    doc_id = f"{prefix}_{doc_index:03d}"
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = str(raw_dir / f"{doc_id}.pdf")

    # Paramètres selon le scénario
    coherent = scenario not in ("mismatch",)
    expired = scenario == "expired"
    tva_rate = random.choice(TVA_RATES)

    # Appel au générateur approprié
    if doc_type == "facture":
        ground_truth = generate_facture(
            company, pdf_path,
            coherent=coherent, doc_index=doc_index, tva_rate=tva_rate,
        )
    elif doc_type == "devis":
        ground_truth = generate_devis(
            company, pdf_path,
            coherent=coherent, expired=expired,
            doc_index=doc_index, tva_rate=tva_rate,
        )
    elif doc_type == "attestation_urssaf":
        ground_truth = generate_attestation_urssaf(
            company, pdf_path, expired=expired, doc_index=doc_index,
        )
    elif doc_type == "attestation_siret":
        ground_truth = generate_attestation_siret(
            company, pdf_path, expired=expired, doc_index=doc_index,
        )
    elif doc_type == "kbis":
        ground_truth = generate_kbis(
            company, pdf_path, expired=expired, doc_index=doc_index,
        )
    elif doc_type == "rib":
        ground_truth = generate_rib(
            company, pdf_path, doc_index=doc_index,
        )
    else:
        raise ValueError(f"Type de document inconnu : {doc_type}")

    # Image propre (tous les documents)
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    clean_image_path = str(images_dir / f"{doc_id}_clean.jpg")
    try:
        pdf_to_clean_image(pdf_path, clean_image_path)
    except Exception as e:
        print(f"  Image propre impossible ({e}), ignoree.")
        clean_image_path = None

    # Image degradee (scenario noisy uniquement)
    noisy_path = None
    if scenario == "noisy":
        noisy_dir = output_dir / "noisy"
        noisy_dir.mkdir(parents=True, exist_ok=True)
        level = random.choice(DEGRADATION_LEVELS)
        noisy_filename = f"{doc_id}_{level}.jpg"
        noisy_path = str(noisy_dir / noisy_filename)
        try:
            degrade_pdf_to_image(pdf_path, noisy_path, level=level)
        except Exception as e:
            print(f"  Degradation impossible ({e}), ignoree.")
            noisy_path = None

    # Anomalies attendues selon le scénario
    anomalies_expected = []
    if scenario == "mismatch" and doc_type in ("facture", "devis"):
        if not coherent:
            anomalies_expected.append("SIRET_MISMATCH")
            if doc_type == "facture" and ground_truth.get("tva") != ground_truth.get("tva_affichee"):
                anomalies_expected.append("TVA_CALCUL_ERROR")
    if scenario == "expired":
        if doc_type == "attestation_urssaf":
            anomalies_expected.append("ATTESTATION_EXPIREE")
        elif doc_type == "kbis":
            anomalies_expected.append("KBIS_PERIME")
        elif doc_type == "devis":
            anomalies_expected.append("DEVIS_EXPIRE")

    # Construction du résultat
    result = {
        "document_id": doc_id,
        "file_path": f"raw/{doc_id}.pdf",
        "clean_image_path": f"images/{doc_id}_clean.jpg" if clean_image_path else None,
        "noisy_path": f"noisy/{Path(noisy_path).name}" if noisy_path else None,
        "type": doc_type,
        "scenario": scenario,
        "anomalies_expected": anomalies_expected,
        "expected_fields": ground_truth,
    }

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Génère un dataset de documents administratifs fictifs.",
    )
    parser.add_argument(
        "--n", type=int, default=N_DOCS,
        help=f"Nombre de documents par type (défaut: {N_DOCS})",
    )
    parser.add_argument(
        "--output", type=str, default="./output",
        help="Répertoire de sortie (défaut: ./output)",
    )
    parser.add_argument(
        "--scenarios", type=str, default="all",
        choices=["all", "coherent", "mismatch", "expired", "noisy"],
        help="Scénarios à générer (défaut: all)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Graine aléatoire pour la reproductibilité (défaut: 42)",
    )
    parser.add_argument("--types", type=str, default=None,
        help="Types a generer (virgule-separés, ex: rib,kbis). Defaut: tous")
    parser.add_argument("--skip-existing", action="store_true",
        help="Ignore les documents deja generes (reprise apres interruption)")
    args = parser.parse_args()

    random.seed(args.seed)
    output_dir = Path(args.output)
    labels_dir = output_dir / "labels"
    labels_dir.mkdir(parents=True, exist_ok=True)

    print(f"Génération: {args.n} docs/type -> {output_dir.resolve()}")

    factory = CompanyFactory()
    manifest = []
    doc_counter = 0

    # Filtrer les types si --types est spécifié
    active_types = DOC_TYPES
    if args.types:
        requested = [t.strip().lower() for t in args.types.split(",")]
        active_types = [t for t in DOC_TYPES if t in requested]
        # Maintenir les IDs corrects en sautant les types ignorés
        for t in DOC_TYPES:
            if t not in active_types:
                doc_counter += args.n

    # Distribution cyclique équilibrée
    all_scenarios = list(SCENARIOS.keys())

    for doc_type in active_types:
        print(f"\n[{doc_type.upper()}] ({args.n} documents)")

        for i in tqdm(range(1, args.n + 1), desc=f"  {doc_type}", ncols=70):
            company = factory.generate()

            if args.scenarios == "all":
                scenario = all_scenarios[(i - 1) % len(all_scenarios)]
            else:
                scenario = args.scenarios

            doc_counter += 1

            # Mode --skip-existing: sauter si déjà généré
            prefix = PREFIXES[doc_type]
            doc_id_check = f"{prefix}_{doc_counter:03d}"
            label_path = labels_dir / f"{doc_id_check}.json"
            if args.skip_existing and label_path.exists():
                with open(label_path, encoding="utf-8") as lf:
                    manifest.append(json.load(lf))
                continue

            result = generate_document(
                doc_type=doc_type,
                company=company,
                output_dir=output_dir,
                doc_index=doc_counter,
                scenario=scenario,
            )
            manifest.append(result)

            with open(label_path, "w", encoding="utf-8") as lf:
                json.dump(result, lf, ensure_ascii=False, indent=2)

    manifest_path = output_dir / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, ensure_ascii=False, indent=2)

    print(f"\n=== {len(manifest)} documents generes ===")
    from collections import Counter
    sc = Counter(d["scenario"] for d in manifest)
    tc = Counter(d["type"] for d in manifest)
    print("Par scenario:", dict(sc))
    print("Par type:", dict(tc))


if __name__ == "__main__":
    main()
