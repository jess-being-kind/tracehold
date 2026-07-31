# Traceproof JSON Test Fixtures

This fixture pack is designed around the current `load_json()` and
`validate_json()` behavior in Traceproof.

## Fast manual checks

```bash
python -m json.tool valid_manifest.json
python -m json.tool invalid_trailing_comma.json
```

The first command should succeed. The second should fail.

## Pytest use

1. Put this directory beside `traceproof.py`, or update the import/path.
2. Install pytest if needed.
3. Run:

```bash
pytest -q test_traceproof_json.py
```

## Important cases

- `valid_deep_nested.json` exercises recursive dictionaries and lists.
- `valid_scalar_mix.json` exercises all JSON scalar types.
- `invalid_root_array.json` is syntactically valid JSON but violates your
  requirement that the root be an object.
- `invalid_utf8.json` exercises your Unicode decode error branch.
- `duplicate_keys.json` demonstrates that Python's default JSON decoder silently
  keeps the last duplicate value.
- `missing.json` is intentionally not included.

See `expected_results.json` for the expected outcome of every fixture.
