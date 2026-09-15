const assert = require("assert");
const fs = require("fs");
const path = require("path");

const claimsDir = path.join(__dirname, "..", "atlas", "claims");
const evidenceDir = path.join(__dirname, "..", "atlas", "evidence");
const sourceDir = path.join(__dirname, "..", "atlas", "sources");

function readJson(file) {
    return JSON.parse(fs.readFileSync(file, "utf8"));
}

function collectRecords(dir, collectionKey) {
    const records = new Map();

    for (const file of fs.readdirSync(dir).filter(
        name => name.endsWith(".json") && name !== "index.json"
    )) {
        const data = readJson(path.join(dir, file));

        for (const record of data[collectionKey] || []) {
            assert.ok(
                record.id,
                `${file}: ${collectionKey} record must have id`
            );

            assert.ok(
                !records.has(record.id),
                `Duplicate ${collectionKey} id: ${record.id}`
            );

            records.set(record.id, record);
        }
    }

    return records;
}

const claimIndex = collectRecords(
    claimsDir,
    "claims"
);

const evidenceIndex = collectRecords(
    evidenceDir,
    "evidence"
);

const sourceIndex = collectRecords(
    sourceDir,
    "sources"
);

/*
 * Evidence → Claim → Source
 */
for (const evidence of evidenceIndex.values()) {
    assert.ok(
        evidence.claimRef,
        `${evidence.id}: claimRef is required`
    );

    assert.ok(
        claimIndex.has(evidence.claimRef),
        `${evidence.id}: claimRef must resolve to an existing Claim`
    );

    assert.ok(
        evidence.sourceRef,
        `${evidence.id}: sourceRef is required`
    );

    assert.ok(
        sourceIndex.has(evidence.sourceRef),
        `${evidence.id}: sourceRef must resolve to an existing Source`
    );
}

/*
 * Claim → Evidence
 */
for (const claim of claimIndex.values()) {
    for (const evidenceRef of claim.evidenceRefs || []) {
        assert.ok(
            evidenceIndex.has(evidenceRef),
            `${claim.id}: evidenceRef must resolve to an existing Evidence`
        );

        const evidence =
            evidenceIndex.get(evidenceRef);

        assert.strictEqual(
            evidence.claimRef,
            claim.id,
            `${claim.id}: ${evidenceRef} must point back to its Claim`
        );
    }
}

/*
 * Canonical Claim index coverage
 */
const claimsIndex = readJson(
    path.join(claimsDir, "index.json")
);

for (const [claimId, filename] of Object.entries(
    claimsIndex.claims || {}
)) {
    assert.ok(
        claimIndex.has(claimId),
        `${claimId}: claims index must resolve to an existing Claim`
    );

    assert.ok(
        fs.existsSync(
            path.join(claimsDir, filename)
        ),
        `${claimId}: claims index file must exist`
    );
}

console.log(
    `Claim → Evidence → Source integration contract PASSED (${claimIndex.size} claims, ${evidenceIndex.size} evidence, ${sourceIndex.size} sources)`
);