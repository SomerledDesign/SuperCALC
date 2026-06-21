#!/usr/bin/env python3
"""
Host harness for Phase 0 hardware smoke script (examples/hw_smoke_phase0.py).

Validates the smoke script exists, is MicroPython-safe enough for device use,
and that the hybrid checks it relies on pass on host fallback (same code path
the device uses when picocalc_math is absent).

Usage:
    python3 tests/test_phase0_hw_smoke.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SMOKE_PATH = os.path.join(ROOT, "examples", "hw_smoke_phase0.py")


def test_smoke_file_exists():
    assert os.path.isfile(SMOKE_PATH), "examples/hw_smoke_phase0.py missing"
    print("OK smoke file exists")


def test_smoke_script_mpy_safe():
    with open(SMOKE_PATH, "r") as f:
        lines = f.readlines()
    # Check code lines only (skip comments/docstrings mentioning banned tokens).
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
    assert "hybrid.sin" in src
    assert "record-hardware-verification" in src
    print("OK smoke script structure + MPy-safe patterns")


def test_hybrid_checks_smoke_depends_on():
    from mp.lib.hybrid import version, sin, sqrt, HAS_C_MATH
    v = version()
    assert isinstance(v, str)
    assert abs(sin(0.5) - 0.479425538604203) < 1e-9
    assert abs(sqrt(9) - 3.0) < 1e-12
    print("OK hybrid deps for smoke (version/sin/sqrt)", "HAS_C_MATH=", HAS_C_MATH)


def test_smoke_run_on_host_via_exec():
    # Simulate device exec of the smoke module body (host cannot import as package from examples/)
    ns = {}
    with open(SMOKE_PATH, "r") as f:
        code = f.read()
    exec(compile(code, SMOKE_PATH, "exec"), ns)
    assert callable(ns["run"])
    # run() prints; on host hybrid fallback should pass all required checks
    ok = ns["run"]()
    assert ok is True, "smoke run() should PASS on host with hybrid fallback"
    print("OK smoke run() PASS on host fallback")


def main():
    print("Phase 0 hw smoke host harness")
    print("---")
    test_smoke_file_exists()
    test_smoke_script_mpy_safe()
    test_hybrid_checks_smoke_depends_on()
    test_smoke_run_on_host_via_exec()
    print("---")
    print("ALL PHASE 0 SMOKE HOST TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())