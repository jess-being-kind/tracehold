from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from traceproof import load_json, validate_json

def test_load_json(path_in: Path) -> None:
    # Load valid json first
    path_json = path_in / "valid_manifest.json"

    expected: dict[str, Any] = {
        "schema_version": str,
        "case_id": str,
        "run_id": str,
        "created_utc": str,
    }

    actual = load_json(path_json)

test_load_json(Path("/home/jess/Vec/Engineering/projects/active/tracehold/src/traceproof/fixtures"))
