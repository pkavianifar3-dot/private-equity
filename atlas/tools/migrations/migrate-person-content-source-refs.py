import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTENT = ROOT / "atlas" / "content" / "persons"
MAPPING = ROOT / "atlas" / "tools" / "migrations" / "mappings" / "person-content-source-refs-v1.json"


def load_mapping():
    data = json.loads(MAPPING.read_text(encoding="utf-8"))
    return data["mappings"]


def migrate_document(document, mapping):
    changed = False

    for section in document.get("sections", []):
        for paragraph in section.get("paragraphs", []):
            legacy_refs = paragraph.get("source_refs")

            if legacy_refs is None:
                continue

            canonical_refs = []
            for ref in legacy_refs:
                canonical = mapping.get(str(ref))
                if canonical is None:
                    raise ValueError(f"unmapped legacy source ref: {ref}")
                if canonical not in canonical_refs:
                    canonical_refs.append(canonical)

            paragraph["sourceRefs"] = canonical_refs
            del paragraph["source_refs"]
            changed = True

    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    mapping = load_mapping()
    changed = 0

    for path in sorted(CONTENT.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))

        if not migrate_document(document, mapping):
            continue

        changed += 1
        print("MIGRATE", path)

        if args.apply:
            backup = path.with_suffix(path.suffix + ".bak")
            if not backup.exists():
                backup.write_text(
                    path.read_text(encoding="utf-8"),
                    encoding="utf-8"
                )

            path.write_text(
                json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8"
            )

    print("Changed documents:", changed)
    print("Mode:", "APPLY" if args.apply else "DRY-RUN")


if __name__ == "__main__":
    main()
