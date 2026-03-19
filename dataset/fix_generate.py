import ast, json

with open("generate.py", "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

head = lines[:174]

new_main = """
def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Generateur de dataset.")
    parser.add_argument("--n", type=int, default=N_DOCS)
    parser.add_argument("--output", type=str, default="./output")
    parser.add_argument("--scenarios", type=str, default="all",
        choices=["all", "coherent", "mismatch", "expired", "noisy"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--types", type=str, default=None)
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()

    random.seed(args.seed)
    output_dir = Path(args.output)
    labels_dir = output_dir / "labels"
    labels_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 43)
    print(f"  Generation: {args.n} docs/type -> {output_dir.resolve()}")
    print("=" * 43)

    factory = CompanyFactory()
    manifest = []
    doc_counter = 0

    active_types = DOC_TYPES
    if args.types:
        requested = [t.strip().lower() for t in args.types.split(",")]
        active_types = [t for t in DOC_TYPES if t in requested]
        for t in DOC_TYPES:
            if t not in active_types:
                doc_counter += args.n

    all_scenarios = list(SCENARIOS.keys())

    for doc_type in active_types:
        print(f"[{doc_type.upper()}]")
        for i in tqdm(range(1, args.n + 1), desc=f"  {doc_type}", ncols=70):
            company = factory.generate()
            if args.scenarios == "all":
                scenario = all_scenarios[(i - 1) % len(all_scenarios)]
            else:
                scenario = args.scenarios
            doc_counter += 1
            prefix = PREFIXES[doc_type]
            doc_id = f"{prefix}_{doc_counter:03d}"
            label_path = labels_dir / f"{doc_id}.json"
            if args.skip_existing and label_path.exists():
                with open(label_path, encoding="utf-8") as lf:
                    manifest.append(json.load(lf))
                continue
            result = generate_document(
                doc_type=doc_type, company=company,
                output_dir=output_dir, doc_index=doc_counter, scenario=scenario,
            )
            manifest.append(result)
            with open(label_path, "w", encoding="utf-8") as lf:
                json.dump(result, lf, ensure_ascii=False, indent=2)

    manifest_path = output_dir / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, ensure_ascii=False, indent=2)

    print(f"\\n=== OK {len(manifest)} documents generes ===")
    from collections import Counter
    sc = Counter(d["scenario"] for d in manifest)
    tc = Counter(d["type"] for d in manifest)
    print("Par scenario:", dict(sc))
    print("Par type:", dict(tc))


if __name__ == "__main__":
    main()
"""

with open("generate.py", "w", encoding="utf-8") as f:
    f.writelines(head)
    f.write(new_main)

with open("generate.py", encoding="utf-8") as f:
    ast.parse(f.read())
print("OK syntaxe valide")
