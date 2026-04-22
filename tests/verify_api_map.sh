#!/usr/bin/env bash
# tests/verify_api_map.sh — T6.5: B.1 API signature verification (Appendix G)
set -e
python3 - <<'PY'
import inspect, sys
sys.path.insert(0, "scripts")
from honne_py import scan, extract, detect_recurrence, evidence, io

expected = {
    "scan.run_scan":              {"scope", "since", "cache", "index_ref", "redact_secrets"},
    "extract.extract_lexicon":    {"input_path", "out_path", "top", "min_sessions"},
    "extract.extract_reaction":   {"input_path", "out_path"},
    "extract.extract_workflow":   {"input_path", "out_path"},
    "extract.extract_obsession":  {"input_path", "out_path"},
    "extract.extract_ritual":     {"input_path", "out_path"},
    "extract.extract_antipattern":{"input_path", "out_path"},
    "detect_recurrence.detect":   {"input_path", "out_path", "min_sessions"},
    "evidence.gather":            {"input_path", "claim", "out_path", "max_"},
}
fail = 0
mods = {
    "scan": scan, "extract": extract,
    "detect_recurrence": detect_recurrence,
    "evidence": evidence, "io": io,
}
for path, required in expected.items():
    mod_name, fn_name = path.split(".")
    obj = getattr(mods[mod_name], fn_name)
    params = set(inspect.signature(obj).parameters.keys())
    missing = required - params
    if missing:
        print(f"FAIL {path}: missing params {missing}"); fail = 1
    else:
        print(f"OK   {path}")
sys.exit(fail)
PY
