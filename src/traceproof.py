#!/usr/bin/env python3
"""
Traceproof
==========

Evidence-integrity and provenance engine for Tracehold.

Traceproof creates deterministic evidence snapshots, verifies current case
contents against those snapshots, detects missing/modified/unexpected files,
and emits structured reports suitable for both humans and automation.

Core design principles
----------------------

1. Observe before modifying.
2. Dry-run unless a write is explicitly authorized.
3. Represent important state with immutable dataclasses.
4. Resolve and validate paths before touching the filesystem.
5. Hash files incrementally so large evidence does not need to fit in memory.
6. Sort all filesystem-derived output for deterministic results.
7. Write manifests atomically to avoid partial evidence records.
8. Distinguish integrity failures from program failures.
9. Preserve enough context to explain every verdict.
10. Treat verification as an evidence-producing operation of its own.

Operator principle:

    Observe directly. Validate physically. Preserve the chain.
"""
# ======================================================================================
# ▶▶▶ S0. IMPORTS
# ======================================================================================

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import (
    Final, Any, Iterable, Sequence, TypeAlias, cast)
import sys, os
import datetime
import json
import time
import argparse
import logging

# ======================================================================================
# ▶▶▶ S1. Metadata, globals, classes
# ======================================================================================

# Script metadata
TIME_START_S: Final[float] = time.time()
RUN_ID: Final[str] = datetime.datetime.now(datetime.UTC).strftime("%d_%m_%Y_%H_%M_%S_UTC")
AUTHOR: Final[str] = "V Halcyon"
VERSION: Final[str] = "v0_1_0"

PATH_SCRIPT: Final[Path] = Path(__file__).resolve()
NAME_SCRIPT: Final[str] = PATH_SCRIPT.stem
TYPE_SCRIPT: Final[str] = PATH_SCRIPT.suffix
DIR_SCRIPT: Final[Path]  = PATH_SCRIPT.parent
DIR_OUTPUT: Path = DIR_SCRIPT / "output"

log = logging.getLogger(__name__)

# Classes
@dataclass(frozen=True)
class Metadata:
    time_start: float = TIME_START_S
    run_id: str = RUN_ID
    author: str = AUTHOR
    version: str = VERSION
    path_script: Path = PATH_SCRIPT
    name_script: str = NAME_SCRIPT
    type_script: str = TYPE_SCRIPT
    dir_script: Path = DIR_SCRIPT
    dir_output: Path = DIR_OUTPUT

@dataclass(frozen=True)
class Config:
    version: str = VERSION
    mode: str = "snapshot"
    verbose: bool = False
    quiet: bool = False
    level: str = "verbose"
    apply: bool = False
    force: bool = False
    output: Path = Path(DIR_SCRIPT / "output")
    case_id: str = ""
    run_id: str = RUN_ID

# Define JSONScalar & JSON Value
JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = (
    JSONScalar
    | list["JSONValue"]
    | dict[str, "JSONValue"]
)

# ======================================================================================
# ▶▶▶ S2. Build system config
# ======================================================================================

def build_config(args, level) -> Config:
    log.info("Building runtime configuration...")
    built_config = Config(
        version=VERSION,
        mode=args.mode,
        verbose=args.VERBOSE,
        apply=args.APPLY,
        force=args.FORCE,
        quiet = args.QUIET,
        level=level,
        case_id=args.CASE_ID,
        )
    return built_config

# ======================================================================================
# ▶▶▶ S2. Time utilities
# ======================================================================================

def utc_now() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%d_%m_%Y_%H_%M_%S_UTC")

# ======================================================================================
# ▶▶▶ S2. Path & file creation utilities
# ======================================================================================

def ensure_directory(path: Path) -> int:
    if path.exists():
        log.info(f"Path {path} already exists - skipping mkdir")
        return 0
    else:
        path.mkdir(parents=True, exist_ok=True)
        return 0

def ensure_file(file: Path, force) -> int:
    if file.exists():
        log.info(f"File {file} already exists - skipping mkdir")
        return 0
    else:
        log.info(f"Creating path {file}:")
        file.touch(exist_ok=True)
    return 0

# ======================================================================================
# ▶▶▶ S2. Logging and error utilities
# ======================================================================================

def setup_logging(config: Config) -> logging.Logger:
    time_now = utc_now()

    CONSOLE_LEVELS: dict[str, int] = {
                "verbose": logging.DEBUG,
                "quiet": logging.WARNING,
                "nominal": logging.INFO
    }

    if config.quiet:
            level = CONSOLE_LEVELS["quiet"]
    elif config.verbose:
            level = CONSOLE_LEVELS["verbose"]
    else:
            level = CONSOLE_LEVELS["nominal"]

    # Bootstrap filesystem prep w/o logging
    ensure_directory(DIR_OUTPUT)
    log_file = Path(DIR_OUTPUT / f"traceproof_{VERSION}_{Metadata.run_id}.log")
    ensure_file(log_file, config.force)

    formatter = logging.Formatter(
         fmt="%(asctime)s | %(levelname)-3s | %(name)s | %(message)s",
         datefmt="%Y-%m-%d: %H:%M:%S"
    )

    # Create file_handler & console_handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root_log = logging.getLogger()
    root_log.setLevel(CONSOLE_LEVELS["verbose"])

    for handler in root_log.handlers[:]:
        root_log.removeHandler(handler)
        print(f"Removed handler: {handler}")
        handler.close()

    root_log.addHandler(file_handler)
    root_log.addHandler(console_handler)

    log.debug(f"Logging initialized @{time_now}")
    log.debug("Log file: %s", log_file)
    log.debug("Console logging level: %i", level)

    return log

# ======================================================================================
# ▶▶▶ S_. Load and validate json files
# ======================================================================================

def load_json(path: Path) -> dict[str, JSONValue]:
    if not path.exists():
        log.warning(f"Path {path.parent} does not exist")
        raise ReferenceError
    elif path.is_dir():
        log.warning(f"Path {path} is a directory - must provide a file")
        raise IsADirectoryError
    elif path.suffix != ".json":
        log.warning("File suffix is not .json")
        raise TypeError
    else:
        try:
            with path.open('r', encoding='utf-8') as f:
                try:
                    payload = json.load(f)
                    if not isinstance(payload, dict):
                        raise TypeError(
                            "JSON root must be an object:"
                            f"  received {type(payload)}"
                            )
                    return cast(dict[str,JSONValue], payload)
                except json.JSONDecodeError as error:
                    log.warning(f"Unable to decode .json: {path}")
                    raise ValueError(
                                    f"Invalid .json in {path}: ",
                                    f"Line {error.lineno}, column {error.colno}"         )
        except UnicodeDecodeError:
            raise ValueError(f"Unable to read/open file: {path}")

def validate_json(raw_json: JSONValue) -> None:

    # JSON behaves like:
    # dictionary
    # ├── key → value
    # ├── key → list
    # │         ├── index → dictionary
    # │         │           ├── key → scalar
    # │         │           └── key → list
    # │         └── index → dictionary
    # └── key → scalar

    if isinstance(raw_json, dict):
        for key, value in raw_json.items():
            if isinstance(value, JSONScalar):
                log.debug(f"JSONScalar | {key} - {value}")
                continue
            elif isinstance(value, list):
                log.debug(f"JSON list detected, recursively reading values...")
                for idx, item in enumerate(value):
                    if isinstance(item, dict):
                        validate_json(item)
                    if isinstance(item, list):
                        log.debug(f"{idx}: {item}"
                                  "recursively running validate_json")
                        validate_json(item)
                    elif isinstance(item, JSONScalar):
                        log.debug(f"JSONScalar | {idx}: {item}")
            elif isinstance(value, dict):
                log.debug("JSON object detected at key %r:"
                          "recursively reading values", key)
                validate_json(value)
            else:
                log.debug(f"Values in file must be an object")
                raise TypeError(f"Value{value} in file must be an object;"
                            f"Received {type(value)}")
    elif isinstance(raw_json, list):
        for idx, item in enumerate(raw_json):
            log.debug(f"JSON list detected, recursively reading values..."
                      f"{idx}: {item}")
    elif isinstance(raw_json, JSONScalar):
                log.debug(f"JSONScalar | {raw_json}")


# ======================================================================================
# ▶▶▶ S-Parse.
# ======================================================================================

def parse_arguments(argv) -> argparse.Namespace:
    main_parser = argparse.ArgumentParser(prog=NAME_SCRIPT, description=f"Main {NAME_SCRIPT} parser")
    main_parser.add_argument("mode", choices=("snapshot", "verify", "inspect"))
    main_parser.add_argument("--verbose", "-v", action="store_true", dest="VERBOSE")
    main_parser.add_argument("--quiet", "-q", action="store_true", dest="QUIET")
    main_parser.add_argument("--apply", action="store_true", dest="APPLY")
    main_parser.add_argument("--force", action="store_true", dest="FORCE")
    main_parser.add_argument("--version", action="version", version=VERSION,)
    main_parser.add_argument("--case-id", dest="CASE_ID")
    return main_parser.parse_args()

# ======================================================================================
# ▶▶▶ S-Config.
# ======================================================================================

# ======================================================================================
# ▶▶▶ S-Main.
# ======================================================================================

def main(argv) -> int:
    # Script preflight
    args = parse_arguments(argv)

    temp_level=logging.DEBUG
    config = build_config(args, temp_level)
    log = setup_logging(config)
    log.debug("Arguments parsed...")
    log.debug("Runtime config built...")
    log.debug("Logging set up")

    log.info("Executing main workflow")
    # Script
    test_dict = load_json(path=Path(DIR_SCRIPT / ".vscode" / "launch.json"))
    valid_json = validate_json(test_dict)
    log.debug(f'file loaded successfully')

    return 0

argv = sys.argv[1:] if sys.argv is not None else None
if __name__ == "__main__":
    raise SystemExit(main(argv))
