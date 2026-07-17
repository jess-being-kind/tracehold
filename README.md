# tracehold
> Turn ambiguous field failures into structured, timestamped, evidence-conscious engineering case files.

`ghostcase` is a Bash-based incident capture and triage tool for engineering problems where hardware, software, communications, configuration, environment, operator procedure, and telemetry may all be interacting.

It creates a consistent case structure for preserving evidence, documenting initial observations, separating raw data from derived analysis, and handing an investigation to another engineer without relying on verbal context.

```text
Observe directly.
Validate physically.
Debug iteratively.
Protect the evidence.
```

## Project status

**Current maturity: early alpha**

The core case-creation workflow is under active development.

| Command   | Purpose                                        | Status           |
| --------- | ---------------------------------------------- | ---------------- |
| `new`     | Create a new case and initial triage structure | Primary workflow |
| `add`     | Add evidence to an existing case               | Partial          |
| `collect` | Run collection profiles against a case         | Scaffolded       |
| `verify`  | Validate structure and evidence integrity      | Scaffolded       |
| `bundle`  | Create a portable case archive                 | Scaffolded       |

Interfaces, file layouts, and option names may change before the first stable release.

## Why Ghostcase exists

Field failures rarely arrive as clean engineering problems.

They arrive as:

* “The vehicle acted strange.”
* “The link dropped for a few seconds.”
* “This only happens at one site.”
* “It worked before the update.”
* “The logs do not agree with what the operator saw.”
* “We restarted it and the problem disappeared.”

The first challenge is often not solving the failure. It is preserving enough reliable context to determine what actually happened.

Ghostcase is designed to help establish:

* what was directly observed;
* what remains unknown;
* which assumptions require validation;
* which assets, sites, versions, and time windows are involved;
* where original evidence is stored;
* which artifacts are derived from that evidence;
* what containment has already occurred;
* who owns the next action;
* and what evidence would discriminate between competing hypotheses.

## Design principles

### Dry-run by default

Ghostcase previews filesystem and command operations unless `--apply` is explicitly supplied.

```bash
./ghostcase.sh new [options]
```

Preview the intended actions first:

```bash
./ghostcase.sh new \
    --title "intermittent_link_loss" \
    --description "Vehicle loses command link during climb" \
    --severity P1 \
    --asset AV-042
```

Apply them only when ready:

```bash
./ghostcase.sh new \
    --title "intermittent_link_loss" \
    --description "Vehicle loses command link during climb" \
    --severity P1 \
    --asset AV-042 \
    --apply
```

### Preserve raw evidence

Original evidence should remain distinguishable from:

* cleaned data;
* extracts;
* generated timelines;
* figures;
* summaries;
* transformed logs;
* and other analytical output.

### Preserve execution context

Each run receives a UTC-based run ID and produces execution metadata intended to capture:

* script version;
* run time;
* selected profile;
* output location;
* execution mode;
* and relevant configuration.

### Make handoff possible

A case should contain enough structured context for another engineer to continue the investigation without a lengthy verbal reconstruction.

### Treat hypotheses as hypotheses

Initial triage separates:

* known facts;
* reported behavior;
* assumptions;
* unknowns;
* working hypotheses;
* contradicting evidence;
* and planned discriminating tests.

## Requirements

Ghostcase is currently Linux-focused.

### Required

* Bash 4.3 or newer
* Standard GNU/Linux command-line utilities

### Used by the current environment collector

Depending on the selected workflow and host configuration:

* `realpath`
* `date`
* `uname`
* `uptime`
* `free`
* `df`
* `lsusb`
* `lspci`
* `dmesg`

Some commands may require additional packages or elevated permissions. For example, access to `dmesg` may be restricted by the operating system.

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd ghostcase
```

Make the script executable:

```bash
chmod +x ghostcase.sh
```

Verify that it launches:

```bash
./ghostcase.sh --version
./ghostcase.sh --help
```

Optionally, place the script somewhere already included in your `PATH`:

```bash
ln -s "$(pwd)/ghostcase.sh" "$HOME/.local/bin/ghostcase"
```

Then invoke it as:

```bash
ghostcase --help
```

## Quick start

Create a new investigation:

```bash
./ghostcase.sh new \
    --title "gps_quality_degradation" \
    --description "Position estimate becomes unstable near Site 04" \
    --severity P2 \
    --asset AV-017 \
    --site SITE-04 \
    --reported-by "Flight Operations" \
    --owner "V Halcyon" \
    --operational-impact "Mission aborted and asset temporarily grounded" \
    --affected-scope "One asset; fleet scope unknown" \
    --recent-change "Navigation firmware updated before first event" \
    --profile general \
    --apply
```

Run with diagnostic output:

```bash
./ghostcase.sh new \
    --title "gps_quality_degradation" \
    --description "Position estimate becomes unstable near Site 04" \
    --severity P2 \
    --asset AV-017 \
    --apply \
    --verbose
```

## Command model

```text
ghostcase COMMAND [options]
```

Available commands:

```text
new       Create a new investigation case
add       Add evidence to an existing case
collect   Collect data into an existing case
verify    Validate a case and its evidence
bundle    Package a case for transport or handoff
```

Exactly one primary command should be selected per invocation.

## Creating a case

```bash
./ghostcase.sh new [options]
```

A generated case ID follows this general pattern:

```text
GC_<UTC timestamp>_<title>
```

Example:

```text
GC_20260716_231530_UTC_intermediate_link_loss
```

### Core case fields

| Option                 | Description                                 |
| ---------------------- | ------------------------------------------- |
| `--title STRING`       | Short investigation title                   |
| `--description STRING` | Initial symptom or problem description      |
| `--severity LEVEL`     | Initial priority, such as `P0` through `P4` |
| `--asset ID`           | Affected asset, vehicle, device, or system  |
| `--site ID`            | Affected site or operating location         |
| `--case CASE_ID`       | Explicit case identifier where applicable   |
| `--profile NAME`       | Collection or analysis profile              |
| `--output-dir DIR`     | Override the default case root              |

### Ownership and time

| Option                 | Description                                                     |
| ---------------------- | --------------------------------------------------------------- |
| `--reported-by NAME`   | Person, team, customer, operator, or system reporting the issue |
| `--owner NAME`         | Current investigation owner                                     |
| `--first-observed UTC` | Earliest known observation time                                 |
| `--last-observed UTC`  | Most recent known observation time                              |

Use UTC where possible. Quote timestamps and values containing spaces:

```bash
--first-observed "2026-07-16T19:42:00Z"
```

### Triage state

| Option                        | Description                                                                            |
| ----------------------------- | -------------------------------------------------------------------------------------- |
| `--operational-impact STRING` | Actual consequence or credible operational risk                                        |
| `--affected-scope STRING`     | Known affected population, fleet, site, or version                                     |
| `--recent-change STRING`      | Relevant recent hardware, software, configuration, procedural, or environmental change |
| `--status STRING`             | Current investigation or operational state                                             |
| `--repro-status STRING`       | Current reproduction state                                                             |
| `--containment-status STRING` | Current containment or restriction                                                     |
| `--triage-confidence LEVEL`   | Confidence in the initial assessment                                                   |

Example reproduction states:

```text
not-attempted
not-reproduced
intermittent
reproduced
```

Example confidence levels:

```text
low
medium
high
```

## Adding evidence

```bash
./ghostcase.sh add \
    --case CASE_ID \
    --file PATH \
    --type TYPE \
    --apply
```

Example:

```bash
./ghostcase.sh add \
    --case GC_20260716_231530_UTC_link_loss \
    --file ./vehicle.log \
    --type log \
    --apply
```

Planned evidence types include:

```text
raw
photo
log
note
```

Evidence ingestion and routing are still under development.

## Collecting evidence

```bash
./ghostcase.sh collect \
    --case CASE_ID \
    --profile PROFILE \
    --apply
```

Collection profiles are intended to provide reusable sets of environment, software, repository, and system checks.

Planned profiles include:

```text
default
general
bash
python
git
```

Profile behavior is still being implemented.

## Verifying a case

```bash
./ghostcase.sh verify \
    --case CASE_ID
```

The verification workflow is intended to check:

* required directory structure;
* required manifests;
* missing or unexpected artifacts;
* checksum availability;
* evidence integrity;
* and consistency between case metadata and stored files.

Full verification behavior is not yet implemented.

## Bundling a case

```bash
./ghostcase.sh bundle \
    --case CASE_ID \
    --apply
```

The bundle workflow is intended to create a portable `.tar.gz` archive suitable for:

* engineering handoff;
* escalation;
* long-term storage;
* incident review;
* and controlled transfer.

Bundling is not yet fully implemented.

## Execution options

| Option            | Behavior                                           |
| ----------------- | -------------------------------------------------- |
| `--apply`         | Perform filesystem changes and commands            |
| `--dry-run`       | Preview operations without changing the filesystem |
| `--force`         | Replace generated files after preserving backups   |
| `-v`, `--verbose` | Enable diagnostic logging                          |
| `--self-test`     | Run the built-in smoke test                        |
| `--version`       | Print the current version                          |
| `-h`, `--help`    | Display command help                               |

Dry-run is the default.

## Generated case structure

A completed `new` workflow is intended to produce a structure similar to:

```text
cases/
├── logs/
│   ├── run_manifest_<run-id>.txt
│   └── summary_<run-id>.txt
│
└── GC_<timestamp>_<title>/
    ├── manifest/
    │   ├── case_manifest.txt
    │   ├── environment.txt
    │   ├── software_versions.txt
    │   └── checksums.sha256
    │
    ├── evidence/
    │   ├── raw/
    │   ├── photos/
    │   ├── logs/
    │   └── operator_notes/
    │
    ├── derived/
    │   ├── timelines/
    │   ├── extracts/
    │   └── figures/
    │
    ├── commands/
    │   ├── collection.log
    │   └── replay.sh
    │
    └── reports/
        ├── initial_triage.md
        └── handoff.md
```

### Directory intent

#### `manifest/`

Records case identity, host context, software information, and integrity metadata.

#### `evidence/`

Stores original material collected during the investigation.

Raw evidence should not be silently modified or overwritten.

#### `derived/`

Stores data generated from original evidence, including:

* filtered extracts;
* reconstructed timelines;
* plots;
* figures;
* and analytical output.

#### `commands/`

Records how evidence was collected, transformed, or reproduced.

The long-term goal is for another engineer to understand and replay the relevant analytical steps.

#### `reports/`

Stores human-readable investigation artifacts such as:

* initial triage;
* handoff notes;
* findings;
* and eventual closure or root-cause reports.

## Initial triage report

The generated initial-triage report is designed to capture:

1. Case control
2. Executive summary
3. Safety and containment
4. Affected scope
5. Event timeline
6. Reported behavior
7. Known facts
8. Evidence inventory
9. Evidence limitations
10. Unknowns
11. Assumptions
12. Initial hypotheses
13. Reproduction plan
14. Immediate actions
15. Escalation and handoff
16. Decision log
17. Initial-triage exit criteria

The report is intentionally a working document, not a final root-cause conclusion.

## Configuration

Ghostcase supports several environment-level defaults.

### `VEC_ROOT`

Base path for the default engineering workspace:

```bash
export VEC_ROOT="$HOME/Vec"
```

### `ENGINEERING_DIR`

Engineering workspace root:

```bash
export ENGINEERING_DIR="$VEC_ROOT/Engineering"
```

### `OUTPUT_DIR`

Override the default case-storage path:

```bash
export OUTPUT_DIR="$HOME/ghostcase-data"
```

A per-run override may also be supplied:

```bash
./ghostcase.sh new \
    --output-dir "$HOME/ghostcase-data" \
    [other options]
```

### `NO_COLOR`

Disable terminal color output:

```bash
export NO_COLOR=1
```

## Safety model

Ghostcase routes intended side effects through controlled command and file-writing helpers.

The safety model currently includes:

* dry-run by default;
* explicit `--apply`;
* quoted argument handling;
* array-oriented command execution;
* optional replacement through `--force`;
* timestamped backups before replacement;
* separation of raw and derived evidence;
* UTC run identifiers;
* centralized error reporting;
* and exit cleanup restricted to the root shell process.

These controls reduce accidental changes, but they do not replace operator review. Always inspect dry-run output before applying actions to important evidence.

## Self-test

Run the built-in smoke test:

```bash
./ghostcase.sh --self-test
```

Include diagnostic output:

```bash
./ghostcase.sh --self-test --verbose
```

The current self-test exercises the runtime skeleton, manifest generation, summary generation, and basic output assertions. It should not yet be treated as complete command-level test coverage.

## Troubleshooting

### Nothing was created

Ghostcase defaults to dry-run mode.

Add:

```bash
--apply
```

after reviewing the previewed operations.

### A command is unavailable

Some environment-collection commands may not be installed on minimal Linux distributions.

Check availability with:

```bash
command -v lsusb
command -v lspci
command -v free
```

### `dmesg` reports a permission error

Some systems restrict kernel-log access.

This does not necessarily indicate that the entire case workflow failed. Run the relevant collection with appropriate permissions only when justified by your environment and security policy.

### The output directory is unexpected

Inspect the active configuration:

```bash
printf '%s\n' "${OUTPUT_DIR:-unset}"
printf '%s\n' "${ENGINEERING_DIR:-unset}"
printf '%s\n' "${VEC_ROOT:-unset}"
```

You may override it with:

```bash
--output-dir /desired/path
```

### Values containing spaces are split

Quote multi-word CLI values:

```bash
--description "Link dropped during autonomous climb"
```

## Development priorities

Near-term work includes:

* completing evidence routing for `add`;
* defining collection-profile behavior;
* implementing checksum generation and verification;
* implementing portable case bundles;
* validating command-specific required arguments;
* validating enumerated fields such as severity and evidence type;
* recording collection commands and provenance;
* expanding self-test coverage;
* adding fixture-based tests;
* and stabilizing the case schema.

## Contributing

Contributions should preserve the project’s core principles:

1. Dry-run should remain the default for side-effecting operations.
2. Raw evidence should remain distinguishable from derived output.
3. Commands should use arrays rather than `eval`.
4. Variables should be quoted unless word splitting is intentional.
5. New workflows should provide useful failure messages.
6. New artifacts should have clear provenance.
7. Documentation should distinguish implemented behavior from planned behavior.
8. Tests should verify both successful and failed execution paths.

Before submitting changes:

```bash
bash -n ghostcase.sh
./ghostcase.sh --self-test --verbose
```

Recommended additional checks:

```bash
shellcheck ghostcase.sh
```

## Security and evidence handling

Ghostcase may collect system information, logs, identifiers, operational notes, and other potentially sensitive evidence.

Before sharing or bundling a case:

* review the included files;
* remove secrets and credentials;
* check logs for tokens or personal information;
* verify that export is authorized;
* preserve an unmodified internal copy where required;
* and follow the applicable data-retention and incident-handling policies.

Ghostcase does not currently provide automatic secret detection or redaction.

## License

No license has been selected yet.

Until a license is added, do not assume permission to copy, modify, or redistribute the project outside the rights provided by applicable law.

---

**Ghostcase**

Observe directly. Validate physically. Debug iteratively.
