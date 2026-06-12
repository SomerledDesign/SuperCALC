#!/usr/bin/env python3
"""
Host-side test harness for SuperCalc.OG hybrid boundary (Phase 0).

Runs on any Python 3 (no device needed). Exercises mp/lib/hybrid.py fallback path.
When the real C module is present in a flashed custom UF2, the same calls go
to native code and should produce bit-identical (or closer) results for the
same inputs.

Usage:
    python3 tests/test_hybrid.py
    # or
    python3 -m pytest tests/test_hybrid.py -q   (if pytest available)

This is the "host-side harness first" per PGR.md. On-device smoke test requires
human flashing the base + our modules and doing:
    import picocalc_math
    import mp.lib.hybrid as h
    print(h.version(), h.sin(0.5), h.sqrt(2))
"""

import sys
import os

# Make mp/ importable when running from project root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mp.lib.hybrid import HAS_C_MATH, version, add, sin, sqrt

EPS = 1e-12

def approx(a, b, eps=EPS):
    return abs(a - b) <= eps

def test_version():
    v = version()
    assert isinstance(v, str)
    assert "SuperCalc" in v or "fallback" in v
    print("OK version:", v)

def test_add():
    assert add(2, 3) == 5
    assert approx(add(0.1, 0.2), 0.3, 1e-9)  # floating point
    assert approx(add(-1.5, 2.5), 1.0)
    print("OK add (int+float)")

def test_sin():
    import math
    assert approx(sin(0), 0.0)
    assert approx(sin(math.pi/2), 1.0, 1e-9)
    assert approx(sin(0.5), math.sin(0.5))
    print("OK sin")

def test_sqrt():
    import math
    assert approx(sqrt(0), 0.0)
    assert approx(sqrt(2), math.sqrt(2))
    assert approx(sqrt(9), 3.0)
    try:
        sqrt(-1)
        assert False, "expected ValueError"
    except ValueError:
        pass
    print("OK sqrt (incl. domain error)")

def test_has_c_math_note():
    # On host dev machine this is False; documents the boundary.
    print(f"OK HAS_C_MATH={HAS_C_MATH} (expected False on host; True only in custom device build)")

def main():
    print("SuperCalc.OG hybrid test harness (host fallback path)")
    print("---")
    test_version()
    test_add()
    test_sin()
    test_sqrt()
    test_has_c_math_note()
    print("---")
    print("ALL TESTS PASSED (host harness)")
    if not HAS_C_MATH:
        print("Note: To verify C path you must build+flash a UF2 with src/math")
        print("      and run equivalent smoke on real PicoCalc hardware.")
    return 0

if __name__ == "__main__":
    sys.exit(main())