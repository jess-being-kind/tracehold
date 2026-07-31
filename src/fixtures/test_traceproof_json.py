from pathlib import Path

import pytest

# Adjust this import if your module has a different filename.
from traceproof import load_json, validate_json


FIXTURES = Path(__file__).parent


@pytest.mark.parametrize(
    "filename",
    [
        "valid_minimal.json",
        "valid_traceproof_config.json",
        "valid_manifest.json",
        "valid_deep_nested.json",
        "valid_scalar_mix.json",
        "valid_unicode.json",
        "duplicate_keys.json",
    ],
)
def test_valid_json_files(filename: str) -> None:
    payload = load_json(FIXTURES / filename)
    validate_json(payload)


@pytest.mark.parametrize(
    "filename",
    [
        "invalid_root_array.json",
        "invalid_root_scalar.json",
    ],
)
def test_non_object_roots_are_rejected(filename: str) -> None:
    with pytest.raises(TypeError):
        load_json(FIXTURES / filename)


@pytest.mark.parametrize(
    "filename",
    [
        "invalid_empty.json",
        "invalid_trailing_comma.json",
        "invalid_unclosed_object.json",
        "invalid_comment.json",
        "invalid_utf8.json",
    ],
)
def test_unreadable_or_malformed_json_is_rejected(filename: str) -> None:
    with pytest.raises(ValueError):
        load_json(FIXTURES / filename)


def test_wrong_extension_is_rejected() -> None:
    with pytest.raises(TypeError):
        load_json(FIXTURES / "wrong_extension.txt")


def test_missing_file_is_rejected() -> None:
    # Your current implementation raises ReferenceError.
    # FileNotFoundError would be the more conventional target.
    with pytest.raises((ReferenceError, FileNotFoundError)):
        load_json(FIXTURES / "missing.json")


def test_duplicate_key_behavior() -> None:
    payload = load_json(FIXTURES / "duplicate_keys.json")
    assert payload["case_id"] == "CASE-OVERWRITTEN"
