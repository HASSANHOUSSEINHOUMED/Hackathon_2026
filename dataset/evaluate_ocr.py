"""
Évaluation de la qualité OCR en comparant les résultats extraits avec le ground truth.
Génère un rapport HTML avec tableaux et graphiques.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import editdistance
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def character_error_rate(reference: str, hypothesis: str) -> float:
    """Calcule le Character Error Rate (CER) entre deux chaînes."""
    if not reference:
        return 0.0 if not hypothesis else 1.0
    dist = editdistance.eval(reference, hypothesis)
    return dist / len(reference)


def evaluate_field(expected: str | None, extracted: str | None) -> dict:
    """Évalue un champ unique : correspondance exacte et CER."""
    if expected is None and extracted is None:
        return {"match": True, "cer": 0.0}
    if expected is None or extracted is None:
        return {"match": False, "cer": 1.0}
    expected_str = str(expected).strip()
    extracted_str = str(extracted).strip()
    cer = character_error_rate(expected_str, extracted_str)
    return {"match": expected_str == extracted_str, "cer": cer}


def load_ground_truth(labels_dir: Path) -> list[dict]:
    """Charge tous les fichiers de ground truth."""
    labels = []
    for label_file in sorted(labels_dir.glob("*.json")):
        with open(label_file, "r", encoding="utf-8") as f:
            labels.append(json.load(f))
    return labels


def load_ocr_results(ocr_dir: Path) -> dict[str, dict]:
    """Charge les résultats OCR indexés par document_id."""
    results = {}
    for result_file in sorted(ocr_dir.glob("*.json")):
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            doc_id = data.get("document_id", result_file.stem)
            results[doc_id] = data
    return results


def evaluate(labels: list[dict], ocr_results: dict[str, dict]) -> dict:
    """
    Compare le ground truth aux résultats OCR.
    Retourne les métriques par type et par niveau de dégradation.
    """
    # Champs à évaluer par type de document
    field_map = {
        "facture": ["siret", "tva_intra", "montant_ht", "tva", "montant_ttc", "date_emission", "iban"],
        "devis": ["siret", "montant_ht", "tva", "montant_ttc", "date_emission", "date_validite"],
        "attestation_urssaf": ["siret", "siren", "raison_sociale", "date_expiration"],
        "attestation_siret": ["siret", "siren", "raison_sociale", "code_naf"],
        "kbis": ["siret", "siren", "raison_sociale", "capital_social", "dirigeant", "tva_intra"],
        "rib": ["iban", "bic", "raison_sociale", "siret"],
    }

    metrics_by_type = defaultdict(lambda: {"cer_values": [], "field_matches": 0, "field_total": 0})
    metrics_by_degradation = defaultdict(lambda: {"cer_values": []})

    for label in labels:
        doc_id = label["document_id"]
        doc_type = label["type"]
        scenario = label["scenario"]
        expected = label.get("expected_fields", {})

        if doc_id not in ocr_results:
            continue

        ocr = ocr_results[doc_id]
        entities = ocr.get("entities", {})
        raw_text = ocr.get("raw_text", "")

        fields = field_map.get(doc_type, [])
        for field_name in fields:
            exp_val = expected.get(field_name)
            ext_val = entities.get(field_name)
            evaluation = evaluate_field(str(exp_val) if exp_val is not None else None,
                                        str(ext_val) if ext_val is not None else None)
            metrics_by_type[doc_type]["cer_values"].append(evaluation["cer"])
            if evaluation["match"]:
                metrics_by_type[doc_type]["field_matches"] += 1
            metrics_by_type[doc_type]["field_total"] += 1

            # Par scénario de dégradation
            if scenario == "noisy":
                deg_level = "noisy"
            else:
                deg_level = "clean"
            metrics_by_degradation[deg_level]["cer_values"].append(evaluation["cer"])

    # Calcul final
    results = {"by_type": {}, "by_degradation": {}, "global": {}}

    all_cers = []
    all_matches = 0
    all_total = 0

    for doc_type, m in metrics_by_type.items():
        cer_mean = float(np.mean(m["cer_values"])) if m["cer_values"] else 0.0
        accuracy = m["field_matches"] / m["field_total"] if m["field_total"] > 0 else 0.0
        results["by_type"][doc_type] = {
            "cer_mean": round(cer_mean, 4),
            "field_accuracy": round(accuracy, 4),
            "field_matches": m["field_matches"],
            "field_total": m["field_total"],
        }
        all_cers.extend(m["cer_values"])
        all_matches += m["field_matches"]
        all_total += m["field_total"]

    for level, m in metrics_by_degradation.items():
        cer_mean = float(np.mean(m["cer_values"])) if m["cer_values"] else 0.0
        results["by_degradation"][level] = {"cer_mean": round(cer_mean, 4)}

    results["global"] = {
        "cer_mean": round(float(np.mean(all_cers)), 4) if all_cers else 0.0,
        "field_accuracy": round(all_matches / all_total, 4) if all_total > 0 else 0.0,
        "documents_evaluated": len([l for l in labels if l["document_id"] in ocr_results]),
        "documents_total": len(labels),
    }

    return results


def generate_charts(results: dict, output_dir: Path) -> list[str]:
    """Génère les graphiques d'évaluation en PNG."""
    charts = []

    # 1. CER par type de document
    fig, ax = plt.subplots(figsize=(10, 5))
    types = list(results["by_type"].keys())
    cers = [results["by_type"][t]["cer_mean"] for t in types]
    bar_colors = ["#1B2A4A" if c < 0.1 else "#F4A261" if c < 0.3 else "#E63946" for c in cers]
    ax.bar(types, cers, color=bar_colors)
    ax.set_ylabel("CER moyen")
    ax.set_title("Character Error Rate par type de document")
    ax.set_ylim(0, max(cers + [0.5]) * 1.2)
    for i, v in enumerate(cers):
        ax.text(i, v + 0.01, f"{v:.3f}", ha="center", fontsize=9)
    plt.tight_layout()
    chart_path = str(output_dir / "cer_by_type.png")
    plt.savefig(chart_path, dpi=150)
    plt.close()
    charts.append(chart_path)

    # 2. Précision des champs par type
    fig, ax = plt.subplots(figsize=(10, 5))
    accs = [results["by_type"][t]["field_accuracy"] for t in types]
    bar_colors = ["#00C896" if a > 0.8 else "#F4A261" if a > 0.5 else "#E63946" for a in accs]
    ax.bar(types, accs, color=bar_colors)
    ax.set_ylabel("Taux de champs corrects")
    ax.set_title("Précision d'extraction par type de document")
    ax.set_ylim(0, 1.1)
    for i, v in enumerate(accs):
        ax.text(i, v + 0.02, f"{v:.1%}", ha="center", fontsize=9)
    plt.tight_layout()
    chart_path = str(output_dir / "accuracy_by_type.png")
    plt.savefig(chart_path, dpi=150)
    plt.close()
    charts.append(chart_path)

    # 3. CER par niveau de dégradation
    if results["by_degradation"]:
        fig, ax = plt.subplots(figsize=(6, 4))
        levels = list(results["by_degradation"].keys())
        cers_deg = [results["by_degradation"][l]["cer_mean"] for l in levels]
        ax.bar(levels, cers_deg, color=["#00C896", "#E63946"])
        ax.set_ylabel("CER moyen")
        ax.set_title("CER par niveau de dégradation")
        plt.tight_layout()
        chart_path = str(output_dir / "cer_by_degradation.png")
        plt.savefig(chart_path, dpi=150)
        plt.close()
        charts.append(chart_path)

    return charts


def generate_html_report(results: dict, charts: list[str], output_path: Path) -> None:
    """Génère un rapport HTML complet avec les résultats d'évaluation."""
    html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Rapport d'évaluation OCR — DocuFlow</title>
    <style>
        body { font-family: 'Inter', sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #F8F9FA; color: #2D3748; }
        h1 { color: #1B2A4A; border-bottom: 3px solid #00C896; padding-bottom: 10px; }
        h2 { color: #1B2A4A; margin-top: 30px; }
        table { border-collapse: collapse; width: 100%; margin: 15px 0; }
        th { background: #1B2A4A; color: white; padding: 10px; text-align: left; }
        td { padding: 8px 10px; border-bottom: 1px solid #E2E8F0; }
        tr:nth-child(even) { background: #EDF2F7; }
        .metric { font-size: 2em; font-weight: bold; color: #1B2A4A; }
        .good { color: #00C896; }
        .warn { color: #F4A261; }
        .bad { color: #E63946; }
        .kpi-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }
        .kpi-card { background: white; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        img { max-width: 100%; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <h1>📊 Rapport d'évaluation OCR — DocuFlow</h1>
"""

    # KPIs globaux
    g = results["global"]
    cer_class = "good" if g["cer_mean"] < 0.1 else "warn" if g["cer_mean"] < 0.3 else "bad"
    acc_class = "good" if g["field_accuracy"] > 0.8 else "warn" if g["field_accuracy"] > 0.5 else "bad"
    html += f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div>CER Moyen Global</div>
            <div class="metric {cer_class}">{g['cer_mean']:.3f}</div>
        </div>
        <div class="kpi-card">
            <div>Précision des champs</div>
            <div class="metric {acc_class}">{g['field_accuracy']:.1%}</div>
        </div>
        <div class="kpi-card">
            <div>Documents évalués</div>
            <div class="metric">{g['documents_evaluated']} / {g['documents_total']}</div>
        </div>
    </div>
"""

    # Tableau par type
    html += "<h2>Résultats par type de document</h2>\n<table>\n"
    html += "<tr><th>Type</th><th>CER moyen</th><th>Précision champs</th><th>Champs OK / Total</th></tr>\n"
    for doc_type, m in results["by_type"].items():
        html += f"<tr><td>{doc_type}</td><td>{m['cer_mean']:.4f}</td><td>{m['field_accuracy']:.1%}</td><td>{m['field_matches']} / {m['field_total']}</td></tr>\n"
    html += "</table>\n"

    # Tableau par dégradation
    if results["by_degradation"]:
        html += "<h2>CER par niveau de dégradation</h2>\n<table>\n"
        html += "<tr><th>Niveau</th><th>CER moyen</th></tr>\n"
        for level, m in results["by_degradation"].items():
            html += f"<tr><td>{level}</td><td>{m['cer_mean']:.4f}</td></tr>\n"
        html += "</table>\n"

    # Graphiques
    html += "<h2>Graphiques</h2>\n"
    for chart in charts:
        chart_name = Path(chart).name
        html += f'<img src="{chart_name}" alt="{chart_name}">\n'

    html += "</body></html>"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def main() -> None:
    parser = argparse.ArgumentParser(description="Évaluation OCR vs ground truth")
    parser.add_argument("--labels", type=str, default="./output/labels", help="Répertoire des ground truth")
    parser.add_argument("--ocr-results", type=str, default="./output/ocr_results", help="Répertoire des résultats OCR")
    parser.add_argument("--output", type=str, default="./output/evaluation", help="Répertoire de sortie du rapport")
    args = parser.parse_args()

    labels_dir = Path(args.labels)
    ocr_dir = Path(args.ocr_results)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not labels_dir.exists():
        print(f"❌ Répertoire de labels introuvable : {labels_dir}")
        sys.exit(1)

    labels = load_ground_truth(labels_dir)
    print(f"📄 {len(labels)} ground truth chargés")

    ocr_results = {}
    if ocr_dir.exists():
        ocr_results = load_ocr_results(ocr_dir)
        print(f"🔍 {len(ocr_results)} résultats OCR chargés")
    else:
        print(f"⚠  Aucun résultat OCR trouvé dans {ocr_dir}")
        print("   Exécutez d'abord le pipeline OCR pour obtenir des résultats.")

    results = evaluate(labels, ocr_results)

    # Sauvegarder les métriques JSON
    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"📊 Métriques sauvegardées : {metrics_path}")

    # Graphiques
    charts = generate_charts(results, output_dir)

    # Rapport HTML
    report_path = output_dir / "rapport_ocr.html"
    generate_html_report(results, charts, report_path)
    print(f"📋 Rapport HTML : {report_path}")

    # Affichage résumé
    print(f"\n{'═' * 50}")
    print(f"  CER global : {results['global']['cer_mean']:.4f}")
    print(f"  Précision  : {results['global']['field_accuracy']:.1%}")
    print(f"  Évalués    : {results['global']['documents_evaluated']} / {results['global']['documents_total']}")
    print(f"{'═' * 50}")


if __name__ == "__main__":
    main()
