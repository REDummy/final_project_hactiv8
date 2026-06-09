# Penetration Testing Guide

This project includes an automated penetration test suite in:
- `tests/test_penetration.py`

## Scope

The suite validates common API and LLM-layer attack paths:
- prompt injection (instruction override and secret-exfiltration prompts)
- data poisoning (malicious retrieved context docs attempting behavior override)
- model extraction (attempts to dump hidden prompts, weights, or training artifacts)
- excessive AI abuse (prompt stuffing and over-sized generation requests)
- malformed JSON and input fuzzing on POST endpoints
- unsupported HTTP method abuse
- monitoring endpoint limit abuse (`/api/monitoring/recent?limit=...`)
- authentication-error response hardening (no secret leakage in API response)

## Run

Install dev dependencies:

```bash
pip install -r requirements-dev.txt
```

Run only penetration tests:

```bash
pytest -m pentest -q
```

Run host-based penetration checks (local host):

```bash
python evaluation/run_pentest_host.py --base-url http://localhost:8501
```

Run host-based penetration checks (verbose):

```bash
python evaluation/run_pentest_host.py --base-url http://localhost:8501 --verbose
```

Run host-based penetration checks (deployed host):

```bash
python evaluation/run_pentest_host.py --base-url https://your-deployed-host --verbose
```

Run full test suite:

```bash
pytest
```

## Notes

- These tests are safe-by-default and run locally with mocked model clients.
- Host-based runs produce a report at `evaluation/reports/pentest_latest.json`.
- They are designed as a regression safety net for OWASP-style API and LLM prompt abuse scenarios.




