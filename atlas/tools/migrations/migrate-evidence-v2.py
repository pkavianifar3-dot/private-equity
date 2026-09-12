import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = ROOT / "atlas" / "evidence"

LEGACY_TO_CANONICAL = {
    "claim": "claimRef",
    "source": "sourceRef",
    "evidence_type": "evidenceType",
}

def migrate_record(record):
    if "claimRef" in record:
        return record, False

    migrated = {}
    for key, value in record.items():
        migrated[LEGACY_TO_CANONICAL.get(key, key)] = value
    return migrated, True

def migrate_file(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    records = []

    for record in data["evidence"]:
        migrated, record_changed = migrate_record(record)
        records.append(migrated)
        changed = changed or record_changed

    if changed:
        data["version"] = "2.0"
        data["evidence"] = records

    return data, changed

def main():
    files = sorted(
        p for p in EVIDENCE_DIR.glob("*.json")
        if p.name != "index.json"
    )

    for path in files:
        data, changed = migrate_file(path)
        status = "MIGRATED" if changed else "ALREADY v2"
        if changed:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(status, path, "records=", len(data["evidence"]))

if __name__ == "__main__":
    main()
