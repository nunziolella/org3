# ORG3 Security Release Gate — v1 (fail closed)

## Purpose

ORG3 is the organizational policy authority, NOT an excuse to give developers
or AI agents production credentials. This module produces evidence for the
*exact Git commit* reviewed. It cannot certify that a product has no flaws.

## Enforcement boundary

```text
Untrusted contributor / AI
       -> feature branch / pull request (read-only CI; NO DEPLOY SECRETS)
       -> ORG3 release gate (mandatory: SAST, secrets, dependencies,
          tests, authorization negative tests, build)
       -> GitHub protected main/master (required status, no bypass)
       -> environment protection + human approval for production
       -> single dedicated deployment identity / artifact digest
       -> production
```

Always verify the exact commit/artifact deployed, not just the name of a branch.
Disable competing deployment routes (Cloudflare Git auto-deploys, manual
Wrangler with broad credentials, GCP Cloud Build triggers, other bots with
deploy credentials). Production access must be scoped to a trusted deploy
identity, with short-lived OIDC credentials where supported. An admin may
bypass some repository rules, so the environment and cloud IAM must be
configured separately. No client-side or browser-only access check qualifies
as API authorization.

## Required policy checks

The following checks are *all* mandatory. Missing policy, missing binary,
timeout, nonzero exit code, missing repository SHA, or absent evidence => BLOCK.
A policy cannot mark a mandatory check as skipped or advisory.

1. `static-analysis` — SAST, e.g. Bandit or Semgrep
2. `secrets` — secret scanning in the release checkout/history
3. `dependencies` — known vulnerable libraries
4. `tests` — unit/integration/regression tests
5. `authorization` — negative tests: anonymous, cross-user/tenant,
   expired or malformed tokens, privilege escalation, role changes
6. `build` — reproducible build for the release candidate

The policy at `policies/org3-release-gate.json` is the initial policy for
THIS repository, not a claim that the same commands work for every stack.
Each project requires an independently reviewed policy, protected from PR
authors. Never run submitted policy commands with cloud credentials.

To run locally with tools installed, from the repository root:

```bash
python -m org3.security.release_gate \
  --repository . \
  --policy policies/org3-release-gate.json \
  --report /tmp/org3-release-evidence.json
```

Outputs a JSON result with commit SHA, policy SHA256, check results, and overall
status. The report deliberately excludes command output to avoid secret leaks.
A PASS only means the configured checks completed successfully; coverage must
be reviewed separately.

## Known blockers at initialization (2026-11-19)

- Current ORG3 deployment workflow automatically deployed on `master`.
  This proposal changes it to manual-only, requires the security gate,
  and restricts production execution to `master`. It has **not** deployed
  anything. No claim is made that Cloudflare direct Git deployment is off.
- Current legacy `ZeroVulnerabilityGate` scans a limited subset of Python
  and swallows parse/file errors. It is NOT sufficient evidence for release.
- Several API routers expose operations that depend on the database without
  an explicit verified authentication dependency. The new negative API tests
  intentionally BLOCK until those routes are hardened and independently
  validated. Never reclassify the tests as expected failures to get green.
- Existing database integration tests skip when the database is unavailable.
  Skipped integration tests are not proof of secure behavior; supply a
  disposable integration database and explicit pass/fail isolation tests.
- As queried through the connected GitHub API, the public `org3` repo had
  no repository rulesets. Private `structura` and `surveyroom-app` ruleset
  reads returned an upgrade/public-repo restriction. No required-branch-check
  enforcement has been configured via this change.

## Required configuration after merge

1. Protect `master` in ORG3 and `main` in the other repos. Require the
   exact security gate check, PR review, stale-review dismissal, and prohibit
   force push/deletion. Avoid routine bypass allowances.
2. Set `production` GitHub Environment to require an independent human
   reviewer, restrict allowed deployment branches, and place deploy secrets
   only where they are needed. Prefer cloud workload identity/OIDC over keys.
3. Remove deploy credentials from contributor/AI identities; enumerate and
   disable every alternative publishing path (Cloudflare, GCP, CLI/manual).
4. For Structura, integrate its GCP Cloud Run deployment with an independent
   gate, and verify IAM auth, ingress, and tenant authorization. Its current
   GitHub deploy trigger is manual-only; that is not full enforcement.
5. For SurveyRoom, retain the no-production-deploy rule; add required gate
   checks, RLS isolation tests, and production credentials only after security
   review. No live DNS, billing, or database migrations here.
6. Validate the enforcement with two controlled tests: attempt merging a
   deliberately failing PR and attempt a direct push to the protected branch.
   Both must be rejected. Test an unauthorized deploy attempt as well.
7. Keep evidence, reviewer identity, artifact digest, policy revision and
   deployment ID in the release register. Re-run after any change.

A PR that modifies this workflow, policy, scanner, or authorization tests
requires independent expert review. ORG3 "God Mode" can authorize a human
business decision, but MUST NOT bypass mandatory technical security checks.
