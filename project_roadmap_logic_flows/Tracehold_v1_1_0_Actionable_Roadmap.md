# Tracehold v1.1.0 — Actionable Development Roadmap

> P0–P4 here are development priorities, not case-severity classifications.
>
> Dependency path: P0 Stabilize → P1 Prove Integrity → P2 Complete Workflows → P3 Productize → P4 Integrate

## P0 — Evidence Safety and Core Correctness
**Target release:** v1.1.1

- [ ] Define evidence-collision policy: default `fail`; optionally `skip-identical` and `rename`.
  - **Reason:** Two unrelated files can share a basename; evidence must never be silently replaced.
- [ ] Preflight the entire `add` batch before the first copy.
  - **Reason:** Prevents half-completed multi-file ingestion.
- [ ] Confine canonicalized case, manifest, evidence, temp, and bundle paths beneath `OUTPUT_DIR`.
  - **Reason:** Prevents traversal and symlink escape.
- [ ] Add a command/option legality matrix.
  - **Reason:** Irrelevant options should fail rather than be silently ignored.
- [ ] Emit valid standalone JSON artifacts with `.json` extensions.
  - **Reason:** Self-test appending and mixed formats undermine automation.
- [ ] Isolate self-test state and use unique run IDs/directories.
  - **Reason:** Shared globals can hide command-specific bugs.
- [ ] Make summaries truthful: `dry_run`, `completed`, `validated_only`, `not_implemented`, `partial`, `failed`.
  - **Reason:** A successful no-op is not a completed workflow.
- [ ] Make evidence copies atomic: temp copy → verify → rename → cleanup on failure.
  - **Reason:** Partial files must not appear valid.
- [ ] Add P0 regression tests: dry-run no mutation, spaces/leading dashes, duplicate source, duplicate basename, read-only destination, path escape, interrupted copy.

### P0 exit gate
- [ ] I would trust `tracehold add` with evidence I cannot reacquire.

## P1 — Provenance, Hashes, and Real Verification
**Target release:** v1.2.0

- [ ] Create a canonical evidence index (`evidence_index.json` or append-only `events.jsonl`).
  - **Record:** evidence ID, original/resolved source, destination, type, size, timestamps, hash, ingest run, operator, result.
- [ ] Hash source and destination with SHA-256 before/after ingest.
  - **Reason:** Proves copied bytes match the selected source.
- [ ] Implement `verify`: structure, required manifests, JSON/schema, indexed-file existence, hashes, path confinement, extra/unindexed files.
- [ ] Preserve assets/sites/owners/files/recent changes as JSON arrays.
  - **Reason:** Automation should not reverse comma-joined presentation strings.
- [ ] Separate invocation intent from operation outcome.
  - **Reason:** “Requested” and “completed” are different facts.
- [ ] Standardize the case manifest as versioned JSON.
- [ ] Add append-only audit events: case created, evidence added, verification run, collection run, bundle created, operator decision.
- [ ] Define and test symlink policy.

### P1 exit gate
- [ ] `tracehold verify CASE` distinguishes intact, modified, missing, extra, malformed, and unverifiable evidence.

## P2 — Complete the Operational Workflows
**Target release:** v1.3.0

- [ ] Implement collection profiles: `default`, `general`, `environment`.
- [ ] Harden environment collection with command checks, timeouts, stderr capture, permissions handling, and partial-result status.
- [ ] Implement software/config snapshots with allowlists and redaction.
- [ ] Generate a real, safely quoted `commands/replay.sh` that operates only on copied evidence.
- [ ] Generate a real `handoff.md` from case state, integrity status, unknowns, hypotheses, actions, owners, and next decision.
- [ ] Implement `bundle`: verify first, deterministic layout, bundle manifest, archive hash, safe output path.
- [ ] Model case lifecycle states and legal transitions.
- [ ] Record outcome metrics: files attempted/copied/skipped/failed, bytes, hashes, warnings, duration.

### P2 exit gate
- [ ] Full lifecycle passes: `new → add/collect → verify → handoff → bundle → verify extracted bundle`.

## P3 — Testing, Packaging, and Operator UX
**Target release:** v1.4.0

- [ ] Move tests into Bats or equivalent.
- [ ] Add CI: `bash -n`, ShellCheck, `shfmt -d`, unit/integration tests, schema validation, bundle round-trip.
- [ ] Create stable fixture cases for clean, modified, missing, duplicate, malformed, and partial scenarios.
- [ ] Add install/uninstall workflow and configurable prefix.
- [ ] Add Bash completion; optionally Zsh/Fish later.
- [ ] Publish README quick start, man page, schema reference, exit-code reference, profile-authoring guide, and examples.
- [ ] Add `--json` machine-readable output for summaries/errors.
- [ ] Define Bash/platform compatibility policy.
- [ ] Test large-file behavior without loading evidence into shell variables.

### P3 exit gate
- [ ] A new operator can install, create, ingest, verify, and bundle a case using only published documentation.

## P4 — Traceview and Ecosystem Integrations
**Target release:** v2.x

- [ ] Integrate Traceview for case browsing, schema validation, timelines, run comparison, evidence lineage, and reports.
- [ ] Add plugin-based collection profiles: UAS/PX4, RF/network, Linux host, embedded target, CAN, power/thermal bench.
- [ ] Add domain importers for `.ulg`, `.tlog`, PCAP, CAN logs, ROS bags, CSV/JSONL, journalctl, and oscilloscope captures.
- [ ] Build cross-case search by asset, site, version, error code, subsystem, hash, and symptom taxonomy.
- [ ] Integrate GitHub Issues/Discussions first; Jira/Linear later.
- [ ] Add content-addressed remote/object storage with resumable transfer and offline queueing.
- [ ] Add manifest/bundle signing and optional encryption.
- [ ] Generate reliability outputs: recurring-failure reports, asset health, version/site comparisons, regression cemetery.
- [ ] Add redaction/export profiles for internal, vendor-safe, customer-safe, and public bundles.
- [ ] Add reusable case templates for RF degradation, reboot, estimator divergence, actuator authority loss, thermal fault, and docking failure.

### P4 exit gate
- [ ] Cases move from field capture to analysis, fleet learning, corrective action, and regression evidence without losing lineage.

## Suggested Version Sequence

| Version | Objective | Release test |
|---|---|---|
| v1.1.1 | P0 stabilization | Safe multi-file ingest with no silent overwrite or invalid artifacts |
| v1.2.0 | P1 provenance + verify | Every indexed artifact is hash-verifiable and schema-valid |
| v1.3.0 | P2 workflow completion | Full lifecycle through a portable verified bundle |
| v1.4.0 | P3 productization | CI, tests, install, docs, completions, machine output |
| v2.0.0 | P4 Traceview ecosystem | Capture, inspect, correlate, and report across cases |

## Recommended Immediate Sprint

- [ ] Remove self-test manifest appending; give every test run a valid standalone manifest.
- [ ] Add `resolve_evidence_destination`.
- [ ] Add batch-wide `preflight_add`.
- [ ] Reject duplicate source paths and duplicate basenames.
- [ ] Refuse existing destinations by default.
- [ ] Record source and destination SHA-256.
- [ ] Add `evidence_index.json`.
- [ ] Implement the first real `verify` pass.
- [ ] Add tests for dry-run, collisions, hash mismatch, path escape, and interrupted copy.
- [ ] Bump to v1.1.1 only when those tests pass.

### Immediate sprint definition of done

```text
NEW creates a valid case
ADD preflights the whole batch
ADD copies atomically
ADD records provenance and hashes
VERIFY proves the copy and case structure
DRY-RUN mutates nothing
SELF-TEST produces only valid artifacts
```
