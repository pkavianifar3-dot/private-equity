# Stage 5 — verified recovery and manual release safeguards

## Implemented contract

- `validate-atlas` remains the required PR check. It runs the existing complete
  validation/test/build/drift sequence, then independently rechecks publication.
- Only a public-eligible, clean-source candidate is archived. The retained bundle
  contains `site.zip` (public files only) and a **separate** `manifest.json`.
  Neither canonical inputs nor the manifest are deployed as part of the site.
- Manifest fields bind repository, workflow fingerprint, build SHA, CI run and
  attempt, event/ref, artifact name, individual file hashes/count, archive hash,
  publication result, and content/link checks.
- Archive retention is requested for 30 days, including feature/PR candidates
  while the deployment gate is off. These files must already be safe for public
  disclosure because this repository is public. Archival is not release approval.
  Feature/PR archives are **never** acceptable production recovery sources.
- Upload/storage failure fails validation. Recovery checks actual expiry and
  requested retention against GitHub metadata; quotas, settings, deletions and
  service availability can make an archive unavailable. There is no guarantee
  beyond actual GitHub retention, and no fallback to repository-root publication.

## Recovery source and preparation

The manual workflow takes a run ID, exact artifact ID and full source SHA. It
requires a completed successful source run from this repository's `main`, using
the approved `.github/workflows/validate-atlas.yml`, with a successful
`validate-atlas` job. PRs, forks, arbitrary workflow paths, mismatched identities,
different workflow implementations, expired/deleted artifacts and low retention
are rejected. GitHub's immutable artifact digest and both archive/per-file hashes
are checked. Safe extraction rejects traversal, symlinks, special files, duplicate
members and oversized inputs.

The verified historical checkout is used **only** to inspect the retained public
bytes. Current tools reapply the historical file/URL contract and current
publication boundaries, including revoked Entity/Research/Claim/Source approval.
It does not rebuild or deploy the historical checkout. A workflow change makes
older fingerprints fail closed; approving/migrating that compatibility requires
explicit review, rather than trusting any workflow with the same filename.

`recovery_dry_run=true` is the default. It downloads/verifies/prepares a public
directory and rehearses a file-only Pages tar, with no production upload or
deploy. A real recovery requires **all** of: execution on current `main`, Source
set to Actions, `PAGES_RELEASE_ENABLED=true`, `release_authorized=true`, and
`recovery_dry_run=false`. Official `upload-pages-artifact` converts only the
recovered public directory to the hosted Pages format. Normal release uses the
same explicit manual authorization; a push never automatically deploys.

Both paths share `github-pages` Environment and deployment concurrency. Source,
main HEAD and authorization are checked again after Environment approval. Turning
off the repository variable is not a cancellation mechanism for a queued/running
workflow; cancel outstanding publication runs explicitly when aborting. GitHub
variable contexts are not claimed to be an atomic, globally refreshed kill switch.
The gate additionally refuses deployment when main is not protected, Environment
review is missing, admin bypass is enabled, or selected branches include anything
other than main. The precise branch check/PR settings still need manual verification.

## Manual GitHub settings (not changed by this implementation)

1. Protect `main`: require PR; require GitHub Actions check **`validate-atlas`**;
   require up-to-date branch and resolved conversations; disable force pushes,
   deletion and bypass. Do not require `deploy` or `recover-prepare` for PRs.
2. Environment `github-pages`: selected branch **main only**, no tags; required
   reviewer; disallow admin bypass. With another reviewer, enable Prevent
   self-review and one PR approval. With only the owner, keep Environment review
   but disable Prevent self-review, and do not require an impossible PR approval.
3. Verify actual artifact retention supports at least 30 days and storage is
   available. Record artifact ID, source run/attempt/SHA and manifest hashes.
4. Keep release variable off, change Pages Source to Actions before merging,
   preserve domain/DNS/HTTPS, then check CI of the new main SHA.
5. Before any first deployment, run recovery **dry-run** on main using the
   successful main validation run's bundle. Do not authorize deploy in that run.
6. First deploy needs a separate authorization and live-site checks. Turn the
   variable off afterwards if releases remain manual; cancel extra runs.

## First cutover: limits and actual fallback

The old `main/root` site and prior deployment remain untouched by this work. A
switch of source must be followed by checking that the currently served version
remains accessible; zero downtime is not proven. Do not delete the domain or
change DNS/HTTPS. No live deployment or settings change is performed here.

The previously audited old site has legacy REVIEW/raw runtime data. It cannot be
retained **unchanged** as an ADR-004-compliant fallback. The first clean candidate
is recoverable after a successful main archive/dry-run, but it is not a previously
healthy Actions deployment. Republishing the same candidate cannot repair a bug
in that candidate. The code does not label candidate validation as production
health or imply retention creates a known-good prior release.

An independent four-file emergency fallback is now implemented and separately
archived/rehearsed through the same pipeline; see `stage-5-emergency-cutover.md`.
It restores only standalone Home/404 and deliberately omits normal features.
This is not restoration of the old full site or proof of production recovery.
A successful main-source emergency bundle and main recovery dry-run must exist
before the first deploy. Once a full clean deployment passes real-site checks,
record it as the full recovery baseline. Never return to main/root or waive gates.

## Verification boundary

Local tests exercise real public bytes, deterministic roundtrip, Pages tar,
negative provenance fixtures and a mocked GitHub download. Hosted feature/PR CI
can exercise create/rehearse/upload and retention, with the production gate off.
After upload it checks actual API expiry and downloads that same candidate using
the Actions token, checks the GitHub archive digest, restores its public files and
rehearses the Pages tar. This transport rehearsal does not approve feature sources
or substitute for a successful previous main run or Environment approval.
There is no eligible new main bundle before merge. Actual authenticated download
of a previous approved main bundle, historical checkout, hosted Pages conversion,
Environment approval and Pages deployment cannot all be proven before that stage.
Report these limits separately from successful local or feature CI results.

## Local final verification

Validator, all 203 Python tests (20 recovery tests), all 21 JavaScript test files,
JavaScript syntax checks, five builders, sitemap and drift passed. The unchanged
public package contains 91 files / 31 HTML pages / 25 sitemap URLs; 810 link/runtime
and 135 HTTP checks passed with zero transport retry and zero publication blocker.
Artifact SHA-256 remains `18bb57bb9ed7ba957f69056ab0f08a4335e0ad871bb342cbdc16817bef214696`.
Actionlint v1.7.12 and diff checks passed. Remote results for the submitted SHA
are reported separately; local success is not a claim of remote recovery or deploy.
