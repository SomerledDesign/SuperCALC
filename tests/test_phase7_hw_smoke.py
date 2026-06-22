#!/usr/bin/env python3
"""
Host harness for Phase 7 hardware smoke script (examples/hw_smoke_phase7.py).

Validates the smoke script exists, is MicroPython-safe, and that CAS checks
pass on host fallback (stub path).

Usage:
    python3 tests/test_phase7_hw_smoke.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SMOKE_PATH = os.path.join(ROOT, "examples", "hw_smoke_phase7.py")


def test_smoke_file_exists():
    assert os.path.isfile(SMOKE_PATH), "examples/hw_smoke_phase7.py missing"
    print("OK smoke file exists")


def test_smoke_script_mpy_safe():
    with open(SMOKE_PATH, "r") as f:
        lines = f.readlines()
    code_lines = []
    for line in lines:
        s = line.strip()
        if s.startswith("#") or not s:
            continue
        code_lines.append(line)
    code = "".join(code_lines)
    banned = ["os.path", "from typing", "__future__", "import typing"]
    for b in banned:
        assert b not in code, f"smoke script must not use {b} in code (MPy compat)"
    with open(SMOKE_PATH, "r") as f:
        src = f.read()
    assert "def run(" in src
    assert "mp.lib.cas" in src
    assert "record-hardware-verification" in src
    print("OK smoke script structure + MPy-safe patterns")


def test_cas_deps_for_smoke():
    from mp.lib.cas import HAS_CAS, info, simplify, Symbolic
    inf = info()
    assert "has_cas" in inf
    s = simplify("x+x")
    assert isinstance(s, Symbolic)
    assert "stub:simplify" in str(s) or HAS_CAS
    print("OK cas deps for smoke (info/simplify/Symbolic)", "HAS_CAS=", HAS_CAS)


def test_smoke_run_on_host_via_exec():
    ns = {}
    with open(SMOKE_PATH, "r") as f:
        code = f.read()
    exec(compile(code, SMOKE_PATH, "exec"), ns)
    assert callable(ns["run"])
    ok = ns["run"]()
    assert ok is True, "smoke run() should PASS on host with CAS stub"
    print("OK smoke run() PASS on host fallback")


def main():
    print("Phase 7 hw smoke host harness")
    print("---")
    test_smoke_file_exists()
    test_smoke_script_mpy_safe()
    test_cas_deps_for_smoke()
    test_smoke_run_on_host_via_exec()
    print("---")
    print("ALL PHASE 7 SMOKE HOST TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())