# Recovery across workflow revisions

## Cause and correction

The first recovery dry-run after Stage 6 merge (run 38328509351, main d6d36034a118a62b87bce0b714c4cf7100c2f95d) rejected the healthy deployed Stage 5 bundle because its workflow bytes differed from today's workflow. Comparing the historical manifest to today's file prevented valid rollback after a workflow upgrade.

The verifier now checks that the source SHA is an ancestor of the approved checkout and compares the manifest hash to workflow bytes read with `git show SOURCE_SHA:.github/workflows/validate-atlas.yml`. The recovery job fetches complete history. Missing history, unknown SHA, a nonancestor or hash mismatch fails closed.

Repository, successful main run, workflow ID/path, artifact ID/digest, expiry, immutable SHA, file hashes, historical and current publication boundaries remain mandatory. No historical scripts are executed. Deployment still requires the explicit authorization input, release variable and protected github-pages environment.

## Evidence and limits

The real deployed bundle from run 38174945481 / artifact 11715492218 / SHA e9edde57303ad3de573da68a1ba29817b04b6936 was authenticated, downloaded and restored locally under the new verifier: 91 public files, 31 pages, 25 sitemap URLs, 998 link/runtime checks. Its public files were converted to a Pages tar; no deployment occurred.

Unit tests cover differing current workflow bytes, unknown/nonancestor SHA, tampered provenance, both bundle kinds, revoked publication, gate off and malicious package members. Full release verification and exact-commit remote CI must pass before merge. Local rehearsal does not prove hosted recovery; repeat the old-bundle dry-run on main after merging this correction, with release_authorized=false, recovery_dry_run=true and PAGES_RELEASE_ENABLED=false. Only then proceed to separately approved release through the existing manual environment review.

This restores the previous approved site, not Stage 6 search. Bundles expire after their configured retention; maintain a fresh verified rollback candidate before future releases. No public URLs, Entity states, Pages settings or release authorization rules change.
