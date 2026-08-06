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
from time import sleep
from enum import Enum, auto
from dataclasses import dataclass, asdict
from typing import (
    Final, Any, Iterable, Sequence, NoReturn, TypeAlias, cast)
import sys, os
import datetime
import json
import time
import argparse
import logging
import math

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

# Globals
separator = "\u27E1"
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

@dataclass(frozen=True)
class Processed:
    status: Status
    message: str
    raw_path: Path
    processed_path: Path

class Status(Enum):
    OK = auto()
    SKIPPED = auto()
    INVALID = auto()
    RECOVERABLE = auto()
    FATAL = auto()

class ProcessingAnomaly(Exception):
    def __init__(self, status: Status, message: str, path: Path | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.path = path

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

def ensure_directory(path: Path) -> None:
    if path.exists():
        log.info(f"Path {path} already exists - skipping mkdir")
    else:
        log.info(f"Path {path} does not exist - creating directory")
        path.mkdir(parents=True, exist_ok=True)

def ensure_file(file: Path, force) -> Path:
    if not isinstance(file, Path):
        raise TypeError("ensure_file requires a file Path object;" \
        f"received: {file}")
    ensure_directory(file.parent)

    if file.exists():
        log.info(f"File {file} already exists")
        if force:
            log.info(f"--force selected - overwriting file {file}")
            file.rename(file.name + ".bak" + RUN_ID)
            file.touch(exist_ok=False)
            return file
        else:
            log.info("skipping create file - use --force to backup & overwrite")
    else:
        log.info(f"Creating file {file}:")
        file.touch(exist_ok=True)
    return file

# ======================================================================================
# ▶▶▶ S2. Logging and error utilities
# ======================================================================================

def setup_logging(config: Config) -> logging.Logger:
    time_now = utc_now()

    CONSOLE_LEVELS: dict[str, int] = {
                "verbose": logging.DEBUG,
                "quiet": logging.WARNING,
                "nominal": logging.INFO,
                "error": logging.ERROR
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

    LOG_FORMAT = (
    "%(asctime)s ⟡ "
    "%(levelname)-7s ⟡ "
    "%(name)s ⟡ "
    "%(message)s"
    )
    formatter = logging.Formatter(
        LOG_FORMAT,
        datefmt="%H:%M:%S",
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
# ▶▶▶ S_. Matrix/dict/list utilities
# ======================================================================================


# ======================================================================================
# ▶▶▶ S_. Internal Error Management
# ======================================================================================

def handle_anomaly(
        status: Status,
        message: str,
        path: Path | None = None
        ) -> NoReturn:
# Function contract:
#   Inputs:
#       - status | enum option from class Status(Enum)
#       - message | string w/ output message
#       - path | Path object
#
#   Outputs:
#       - routing | int w/ possible values:
#           - 0 | returns when Status.OK or Status.RECOVERABLE
#           - 1 | returns when Status.FATAL
#           - 2 | returns when Status.SKIPPED
#           - 3 | returns when Status. INVALID

    log.debug(f"handle_anomaly invoked {separator} status: {status.name} {separator} path {path}")


    match status:
        case Status.OK:
            raise ValueError("handle_anomaly should not be called w/ Status.OK")
        case Status.SKIPPED:
            log.info(f"Skipped {separator} {message}")

        case Status.INVALID:
            log.warning(f"Invalid {separator} {message}")

        case Status.RECOVERABLE:
            log.info(f"Recoverable {separator} {message}")

        case Status.FATAL:
            log.error(f"Fatal {separator} {message}")

    raise ProcessingAnomaly(status=status, message=message, path=path)


# ======================================================================================
# ▶▶▶ S_. Load and validate json files
# ======================================================================================

def load_json(path: Path) -> dict[str, JSONValue]:

    # Maximum JSON file size == 10 MiB
    MAX_JSON_BYTES = 10
    size_bytes: float = path.stat().st_size/10**6
    if size_bytes > MAX_JSON_BYTES:
        handle_anomaly(Status.SKIPPED,f"Maximum JSON file size set to: {MAX_JSON_BYTES}"
                f"File size: {size_bytes}")

    # Disqualifier gates
    if not path.exists():
        handle_anomaly(Status.SKIPPED, f"path does not exist: {path}")
    elif path.is_dir():
        handle_anomaly(Status.INVALID, f"path {path} is a directory - must provide a file" )
    elif not path.is_file():
        handle_anomaly(Status.SKIPPED, f"input {path} is not a file")
    elif path.suffix.lower() != ".json":
        handle_anomaly(Status.INVALID, f"Expected .json file: {path}")
    elif path.is_symlink():
        handle_anomaly(Status.INVALID, f"JSON path may not be a symblik: {path}")
    elif size_bytes > MAX_JSON_BYTES:
        handle_anomaly(Status.INVALID, f"JSON file exceeds {MAX_JSON_BYTES} bytes: "
            f"{path} contains {size_bytes} bytes")
    elif path.stat().st_size == 0:
        handle_anomaly(Status.SKIPPED, f"JSON file is empty: {path}")
    else:
        try:
            with path.open('r', encoding='utf-8') as f:
                try:
                    payload = json.load(f)
                    if not isinstance(payload, dict):
                        handle_anomaly(Status.INVALID, "JSON root must be an object:"
                                    f"  received {type(payload)}")
                #### Sole return path
                    return cast(dict[str,JSONValue], payload)
                ####
                except json.JSONDecodeError as error:
                    handle_anomaly(Status.SKIPPED,
                                    f"Invalid .json in {path}: "
                                    f"Line {error.lineno}, column {error.colno}")
        except PermissionError as error:
            handle_anomaly(Status.SKIPPED, f"Permission denied while reading JSON file: {path}")
        except OSError as error:
            handle_anomaly(Status.SKIPPED, f"Unable to read JSON file {path}: {error}")
        except UnicodeDecodeError as error:
            handle_anomaly(Status.INVALID, f"JSON file is not valid utf-8: {path}"
                             f"Error position {error.start}")


def validate_json(file: Path, raw_json: JSONValue) -> bool:

    # JSON behaves like:
    # dictionary
    # ├── key → value
    # ├── key → list
    # │         ├── index → dictionary
    # │         │           ├── key → scalar
    # │         │           └── key → list
    # │         └── index → dictionary
    # └── key → scalar

    validity: bool = True

    # Immediate error-out conditions

    # Determine validity
    if isinstance(raw_json, dict):
        for key, value in raw_json.items():
            if not validate_json(file, value):
                validity = False

    elif isinstance(raw_json, list):
        for idx, item in enumerate(raw_json):
            if not validate_json(file, item):
                validity = False
    elif isinstance(raw_json, JSONScalar):
            validity = True
    else:
        raise ValueError(f"Invalid object {raw_json}"
                         f"received type: {type(raw_json)}")
    return validity


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
    args = parse_arguments(argv=argv)

    temp_level=logging.DEBUG
    config = build_config(args, temp_level)
    log = setup_logging(config)
    log.debug("Arguments parsed...")
    log.debug("Runtime config built...")
    log.debug("Logging set up")

    log.info("Executing main workflow")
    # Script

    # JSON loading/validation
    fixture_dir = Path(DIR_SCRIPT / "fixtures")



    for file in fixture_dir.glob("*.json",case_sensitive=False):
        try:
            payload = load_json(file)
            log.debug(f"Validating {file}")
            validity = validate_json(file, payload)
        except ProcessingAnomaly as anomaly:
            if anomaly.status is Status.FATAL:
                log.critical(f"Fatal batch anomaly {separator} {anomaly.message}")
                return 1
            log.debug(f"Skipping remaining processing for {file}")
            continue
        log.info(f"Processed {separator} {file} {separator} Validity {separator} {validity}")

    return 0

argv = sys.argv[1:]
if __name__ == "__main__":
    raise SystemExit(main(argv))
