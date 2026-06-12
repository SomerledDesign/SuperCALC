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

from mp.lib.hybrid import HAS_C_MATH, version, add, sub, mul, div, sin, cos, tan, sqrt, exp, log, pow as hpow, fabs, rpn_eval

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

def test_new_math():
    import math
    assert approx(sub(5, 2), 3.0)
    assert approx(mul(2, 3), 6.0)
    assert approx(div(10, 4), 2.5)
    assert approx(cos(0), 1.0)
    assert approx(tan(math.pi/4), 1.0, 1e-9)
    assert approx(exp(0), 1.0)
    assert approx(log(math.e), 1.0, 1e-9)
    assert approx(hpow(2, 3), 8.0)
    assert approx(fabs(-3.5), 3.5)
    # div0
    try:
        div(1, 0)
        assert False
    except ValueError:
        pass
    print("OK new math (sub/mul/div/trig/exp/log/pow/fabs)")

def test_rpn_eval():
    import math
    # basic
    assert approx(rpn_eval([2, 3, "+"]), 5.0)
    assert approx(rpn_eval([2, 3, "*"]), 6.0)
    assert approx(rpn_eval([10, 4, "/"]), 2.5)
    assert approx(rpn_eval([2, 3, "pow"]), 8.0)
    # trig etc
    assert approx(rpn_eval([0, "sin"]), 0.0)
    assert approx(rpn_eval([math.pi/2, "cos"]), 0.0, 1e-9)
    assert approx(rpn_eval([9, "sqrt"]), 3.0)
    # stack ops
    assert approx(rpn_eval([5, "dup", "+"]), 10.0)
    assert approx(rpn_eval([1, 2, "swap", "-"]), 1.0)  # 1 2 swap -> 2 1  => 2-1=1
    # chain expr e.g. 2 3 + 4 *  => (2+3)*4 =20
    assert approx(rpn_eval([2, 3, "+", 4, "*"]), 20.0)
    # error cases
    try:
        rpn_eval([1, "+"])
        assert False
    except ValueError:
        pass
    try:
        rpn_eval([1, 0, "/"])
        assert False
    except ValueError:
        pass
    print("OK rpn_eval (ops + stack manip + errors)")

def main():
    print("SuperCalc.OG hybrid test harness (host fallback path)")
    print("---")
    test_version()
    test_add()
    test_sin()
    test_sqrt()
    test_new_math()
    test_rpn_eval()
    test_has_c_math_note()
    print("---")
    print("ALL TESTS PASSED (host harness)")
    if not HAS_C_MATH:
        print("Note: To verify C path you must build+flash a UF2 with src/math")
        print("      and run equivalent smoke on real PicoCalc hardware.")
    return 0

if __name__ == "__main__":
    sys.exit(main())