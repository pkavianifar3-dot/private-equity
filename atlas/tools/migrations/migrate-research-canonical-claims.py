import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTENT = ROOT / "research" / "content"
MAPPINGS = ROOT / "research" / "mappings"


def load_promotions():
    result = {}
    for path in MAPPINGS.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for claim in data.get("claims", []):
            if claim.get("status") == "PROMOTED":
                ref = claim.get("canonicalClaimRef")
                if ref:
                    result[claim["id"]] = ref
    return result

def migrate(document, promotions):
    candidates = document.get("candidateClaimRefs", [])
    claims = list(document.get("claimRefs", []))
    remaining = []

    for ref in candidates:
        canonical = promotions.get(ref)
        if canonical:
            if canonical not in claims:
                claims.append(canonical)
        else:
            remaining.append(ref)

    document["claimRefs"] = claims
    document["candidateClaimRefs"] = remaining
    return len(candidates) != len(remaining)


def replace_top_level_array(text,key,values):
    m=re.search(rf'(?m)^(?:  |)("{re.escape(key)}":\s*)',text)
    if not m: raise ValueError(f"missing top-level field: {key}")
    start=m.end();_,end=json.JSONDecoder().raw_decode(text[start:])
    value=json.dumps(values,ensure_ascii=False,indent=2)
    if values: value=value.replace("\n","\n  ")
    return text[:start]+value+text[start+end:]


def main():
    promotions = load_promotions()
    changed = 0

    for path in sorted(CONTENT.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if migrate(data, promotions):
            text = path.read_text(encoding="utf-8")
            text = replace_top_level_array(text, "claimRefs", data["claimRefs"])
            text = replace_top_level_array(text, "candidateClaimRefs", data["candidateClaimRefs"])
            json.loads(text)
            path.write_text(text, encoding="utf-8")
            changed += 1
            print("MIGRATED", path)

    print("Changed documents:", changed)

if __name__ == "__main__":
    main()
