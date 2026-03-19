"""
Patch generate.py: ajoute clean_image, cyclic scenarios, --types et --skip-existing
"""
import ast

SRC = "generate.py"

with open(SRC, encoding="utf-8") as f:
    src = f.read()

# 1. Import pdf_to_clean_image
src = src.replace(
    "from degrade import degrade_pdf_to_image",
    "from degrade import degrade_pdf_to_image, pdf_to_clean_image",
)

# 2. Remplacer le bloc "Degradation noisy" dans generate_document
OLD_NOISY = """    # Dégradation pour le scénario noisy
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
            noisy_path = None"""

NEW_NOISY = """    # Image propre (tous les documents)
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
            noisy_path = None"""

assert OLD_NOISY in src, "BLOC NOISY NON TROUVE"
src = src.replace(OLD_NOISY, NEW_NOISY)

# 3. Ajouter clean_image_path dans le dict result
OLD_RESULT = '''    result = {
        "document_id": doc_id,
        "file_path": f"raw/{doc_id}.pdf",
        "noisy_path": f"noisy/{Path(noisy_path).name}" if noisy_path else None,'''

NEW_RESULT = '''    result = {
        "document_id": doc_id,
        "file_path": f"raw/{doc_id}.pdf",
        "clean_image_path": f"images/{doc_id}_clean.jpg" if clean_image_path else None,
        "noisy_path": f"noisy/{Path(noisy_path).name}" if noisy_path else None,'''

assert OLD_RESULT in src, "DICT RESULT NON TROUVE"
src = src.replace(OLD_RESULT, NEW_RESULT)

# 4. Remplacer l'ancienne section main() depuis "args = parser.parse_args()"
OLD_MAIN_BODY = '''    args = parser.parse_args()

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
        print(f"\\n📄 {doc_type.upper()} ({args.n} documents)")

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
            label_path = labels_dir / f"{result[\'document_id\']}.json"
            with open(label_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

    # Sauvegarder le manifeste global
    manifest_path = output_dir / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # Résumé
    print(f"\\n═══════════════════════════════════════════")
    print(f"  ✅ {len(manifest)} documents générés")
    print(f"  📁 PDF bruts :   {output_dir / \'raw\'}")
    print(f"  📁 Dégradés :    {output_dir / \'noisy\'}")
    print(f"  📁 Labels :      {labels_dir}")
    print(f"  📋 Manifeste :   {manifest_path}")

    # Stats par scénario
    from collections import Counter
    scenario_counts = Counter(d["scenario"] for d in manifest)
    type_counts = Counter(d["type"] for d in manifest)
    print(f"\\n  Par scénario :")
    for s, count in scenario_counts.most_common():
        print(f"    {s:12s} : {count}")
    print(f"\\n  Par type :")
    for t, count in type_counts.most_common():
        print(f"    {t:20s} : {count}")
    print(f"═══════════════════════════════════════════")'''

NEW_MAIN_BODY = '''    parser.add_argument("--types", type=str, default=None,
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
        print(f"\\n[{doc_type.upper()}] ({args.n} documents)")

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

    print(f"\\n=== {len(manifest)} documents generes ===")
    from collections import Counter
    sc = Counter(d["scenario"] for d in manifest)
    tc = Counter(d["type"] for d in manifest)
    print("Par scenario:", dict(sc))
    print("Par type:", dict(tc))'''

# Trouver le marqueur juste avant args = parser.parse_args()
OLD_SEED_SECTION = '''    parser.add_argument(
        "--seed", type=int, default=42,
        help="Graine aléatoire pour la reproductibilité (défaut: 42)",
    )
    args = parser.parse_args()'''

NEW_SEED_SECTION = '''    parser.add_argument(
        "--seed", type=int, default=42,
        help="Graine aléatoire pour la reproductibilité (défaut: 42)",
    )
    PLACEHOLDER_ARGS'''

# Build the replacement by replacing the full main body
src = src.replace(OLD_SEED_SECTION + "\n\n" + OLD_MAIN_BODY.split("    args = parser.parse_args()")[0].rstrip(),
                  OLD_SEED_SECTION)

# Instead: do a targeted replacement of the portion after the seed argument
idx = src.find('    parser.add_argument(\n        "--seed"')
assert idx >= 0, "seed arg not found"
# Find the end of args = parser.parse_args() line
parse_idx = src.find("    args = parser.parse_args()", idx)
assert parse_idx >= 0, "parse_args not found"

# Now find the end of the whole main function
main_end = src.find("\n\nif __name__")
assert main_end >= 0, "main end not found"

# Replace section from after seed arg's closing paren to end of main
seed_end = src.find(")\n    args = parser.parse_args()", idx) + len(")\n")
new_src = src[:seed_end] + NEW_MAIN_BODY + "\n\n\nif __name__ == \"__main__\":\n    main()\n"

try:
    ast.parse(new_src)
    print("OK syntaxe valide")
except SyntaxError as e:
    print(f"ERREUR SYNTAXE: {e}")
    # Show context
    lines = new_src.split("\n")
    for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+3)):
        print(f"  {i+1}: {lines[i]}")
    raise

with open(SRC, "w", encoding="utf-8") as f:
    f.write(new_src)
print(f"OK fichier ecrit ({len(new_src.splitlines())} lignes)")
