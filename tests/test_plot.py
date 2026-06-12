#!/usr/bin/env python3
"""
Host-side tests for SuperCalc.OG Phase 3 inc1 graphing data engine.

Exercises mp/plot (cartesian_sample + helpers) + integration with expr/prog/hybrid.
C picocalc_plot is skeleton only (HAS_PLOT=False on host); py path is the verifiable slice.

Run:
    python3 tests/test_plot.py
"""
import sys
import os
import math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mp.plot import cartesian_sample, sample_expr
from mp.lib.hybrid import HAS_PLOT, plot_version
from mp.lang.prog import make_prog
from mp.lang.expr import eval_infix

EPS = 1e-9
def approx(a, b, eps=EPS):
    return abs(a - b) <= eps

def test_basic_cartesian_y_equals_x():
    pts = cartesian_sample("x", -2, 2, n=5)
    assert len(pts) == 5
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    assert approx(xs[0], -2.0)
    assert approx(xs[-1], 2.0)
    for x, y in pts:
        assert approx(x, y), (x, y)
    print("OK cartesian y=x (5 pts, range, identity)")

def test_sin_sampling():
    pts = cartesian_sample("sin(x)", 0, math.pi/2, n=3)
    assert len(pts) == 3
    # sin(0) ~0, sin(pi/4)~0.707, sin(pi/2)=1
    assert approx(pts[0][1], 0.0, 1e-9)
    assert approx(pts[1][1], math.sin(math.pi/4), 1e-9)
    assert approx(pts[2][1], 1.0, 1e-9)
    print("OK sin(x) sampling at known points")

def test_log10_and_count():
    pts = cartesian_sample("log10(x)", 1, 100, n=100)
    assert len(pts) == 100
    # log10(1)=0, log10(10)=1, log10(100)=2
    # find closest to 10
    near10 = min(pts, key=lambda p: abs(p[0]-10))
    assert approx(near10[1], 1.0, 1e-6)
    print("OK log10 sampling, n=100 count, value at 10")

def test_range_and_spacing():
    pts = cartesian_sample("x", 0, 10, n=11)
    assert len(pts) == 11
    assert approx(pts[0][0], 0.0)
    assert approx(pts[-1][0], 10.0)
    dx = pts[1][0] - pts[0][0]
    assert approx(dx, 1.0)
    print("OK uniform spacing + bounds for n=11")

def test_error_tolerant_nan():
    # log of negative region should produce nans but not crash the whole sample
    pts = cartesian_sample("log(x)", -1, 1, n=5)
    assert len(pts) == 5
    # at least one should be nan (x<=0)
    nans = [p for p in pts if math.isnan(p[1])]
    assert len(nans) >= 1
    print("OK domain error yields nan without abort (log over negative)")

def test_rpn_and_program_body():
    # RPN form must use the internal var token (same as to_rpn produces)
    pts_r = cartesian_sample([ ("var", "x"), 2, "*" ], -1, 1, n=3)
    assert approx(pts_r[0][1], -2.0)
    assert approx(pts_r[2][1], 2.0)
    # Program body (first-class fn) — bodies that ref vars use the tuple form
    env = {}
    p = make_prog("dbl", [ ("var", "x"), 2, "*" ], env)
    pts_p = cartesian_sample(p, 0, 3, n=4, env=env)
    assert approx(pts_p[0][1], 0.0)
    assert approx(pts_p[-1][1], 6.0)
    print("OK RPN list + Program.body sampling (RPL first-class fn graph)")

def test_vars_and_side_effect_env():
    env = {"a": 3.0}
    pts = cartesian_sample("x + a", 0, 1, n=2, env=env)
    assert approx(pts[0][1], 3.0)
    assert approx(pts[1][1], 4.0)
    # a still visible after
    assert approx(env.get("a", 0), 3.0)
    print("OK extra vars in env during sample + persistence")

def test_has_plot_and_version():
    v = plot_version()
    assert isinstance(v, str) and ("plot" in v or "fallback" in v)
    assert HAS_PLOT in (True, False)
    print(f"OK HAS_PLOT={HAS_PLOT} plot_version={v}")

def test_sample_expr_helper():
    y = sample_expr("x*x + 1", 3.0)
    assert approx(y, 10.0)
    print("OK sample_expr single point helper")

def main():
    print("SuperCalc.OG Phase 3 plot data engine host tests")
    print("---")
    test_basic_cartesian_y_equals_x()
    test_sin_sampling()
    test_log10_and_count()
    test_range_and_spacing()
    test_error_tolerant_nan()
    test_rpn_and_program_body()
    test_vars_and_side_effect_env()
    test_has_plot_and_version()
    test_sample_expr_helper()
    print("---")
    print("ALL TESTS PASSED (host harness for Phase 3 inc1)")
    if not HAS_PLOT:
        print("Note: HAS_PLOT=False on host (expected); real C plot in custom UF2 build.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
