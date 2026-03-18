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
from degrade import degrade_pdf_to_image
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

    # Dégradation pour le scénario noisy
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
            print(f"  ⚠ Dégradation impossible ({e}), PDF conservé tel quel.")
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
    args = parser.parse_args()

    random.seed(args.seed)
    output_dir = Path(args.output)
    labels_dir = output_dir / "labels"
    labels_dir.mkdir(parents=True, exist_ok=True)

    print(f"═══════════════════════════════════════════")
    print(f"  Génération du dataset — {args.n} docs/type")
    print(f"  Sortie : {output_dir.resolve()}")
    print(f"═══════════════════════════════════════════")

    factory = CompanyFactory()
    manifest = []
    doc_counter = 0

    for doc_type in DOC_TYPES:
        print(f"\n📄 {doc_type.upper()} ({args.n} documents)")

        for i in tqdm(range(1, args.n + 1), desc=f"  {doc_type}", ncols=70):
            # Générer une entreprise par document
            company = factory.generate()

            # Choisir le scénario
            if args.scenarios == "all":
                scenario = choose_scenario()
            else:
                scenario = args.scenarios

            doc_counter += 1
            result = generate_document(
                doc_type=doc_type,
                company=company,
                output_dir=output_dir,
                doc_index=doc_counter,
                scenario=scenario,
            )
            manifest.append(result)

            # Sauvegarder le ground truth individuel
            label_path = labels_dir / f"{result['document_id']}.json"
            with open(label_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

    # Sauvegarder le manifeste global
    manifest_path = output_dir / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # Résumé
    print(f"\n═══════════════════════════════════════════")
    print(f"  ✅ {len(manifest)} documents générés")
    print(f"  📁 PDF bruts :   {output_dir / 'raw'}")
    print(f"  📁 Dégradés :    {output_dir / 'noisy'}")
    print(f"  📁 Labels :      {labels_dir}")
    print(f"  📋 Manifeste :   {manifest_path}")

    # Stats par scénario
    from collections import Counter
    scenario_counts = Counter(d["scenario"] for d in manifest)
    type_counts = Counter(d["type"] for d in manifest)
    print(f"\n  Par scénario :")
    for s, count in scenario_counts.most_common():
        print(f"    {s:12s} : {count}")
    print(f"\n  Par type :")
    for t, count in type_counts.most_common():
        print(f"    {t:20s} : {count}")
    print(f"═══════════════════════════════════════════")


if __name__ == "__main__":
    main()
