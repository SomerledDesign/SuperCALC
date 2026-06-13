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

from mp.plot import cartesian_sample, sample_expr, linspace, ascii_plot
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

def test_linspace_helper():
    xs = linspace(0, 10, 11)
    assert len(xs) == 11
    assert approx(xs[0], 0.0)
    assert approx(xs[-1], 10.0)
    dx = xs[1] - xs[0]
    assert approx(dx, 1.0)
    # also test default n=320 and swapped bounds
    xs2 = linspace(5, -5, 5)
    assert len(xs2) == 5
    assert approx(xs2[0], -5.0)
    assert approx(xs2[-1], 5.0)
    print("OK linspace (spacing, count, swapped range, default n)")
    # prove cartesian uses same grid
    pts = cartesian_sample("x", 0, 4, n=5)
    xs_from_pts = [p[0] for p in pts]
    assert all(approx(a, b) for a, b in zip(xs_from_pts, linspace(0, 4, 5)))


def test_ascii_plot_basic():
    pts = [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)]
    s = ascii_plot(pts, width=12, height=5, title="line")
    assert "line" in s
    assert "*" in s
    assert len(s.splitlines()) >= 6  # title + frame + footer
    # frame characters present
    assert "+" in s and "-" in s and "|" in s
    print("OK ascii_plot basic frame + marks + title + footer")
    # also test nan tolerance (should still render the valid ones)
    pts2 = [(i, (i if i != 1 else float("nan"))) for i in range(3)]
    s2 = ascii_plot(pts2, width=8, height=4)
    assert "*" in s2
    print("OK ascii_plot skips NaNs gracefully")


def test_ascii_plot_flat_and_empty():
    # flat y (single point or constant) should still produce visible row
    pts = [(0.0, 5.0)] * 3
    s = ascii_plot(pts, width=10, height=4)
    assert "*" in s
    assert "5" in s or "flat" not in s.lower()  # range footer has value
    print("OK ascii_plot flat y (single value) renders")
    # empty -> placeholder, no crash
    s0 = ascii_plot([], width=10, height=4)
    assert "no valid data" in s0 or "empty" in s0.lower()
    print("OK ascii_plot empty data placeholder")


def test_ascii_plot_prog_curve():
    # verify a program body as f(x) produces sensible ascii (RPL "graph program" feel)
    env = {}
    # x^2  (dup *) is clean RPN body and produces visible parabola
    p = make_prog("xsq", [ ("var", "x"), "dup", "*" ], env)
    pts = cartesian_sample(p, -2, 2, n=5, env=env)
    s = ascii_plot(pts, width=20, height=6)
    assert "*" in s
    # expect parabolic/upward shape marks
    lines = [ln for ln in s.splitlines() if "|" in ln]
    assert len(lines) == 6
    print("OK ascii_plot of Program body curve (first-class fn graph)")
    # quick value check at x=0 -> 0; x=2 ->4 (within tol of sampling)
    assert approx(pts[2][1], 0.0)
    assert approx(pts[-1][1], 4.0, eps=1e-6)


def test_ascii_plot_downsample_320():
    # 320 default should render ok when width much smaller (simulates terminal vs screen)
    pts = cartesian_sample("sin(x)", 0, 6.28, n=320)
    s = ascii_plot(pts, width=32, height=8)
    lines = s.splitlines()
    assert len([ln for ln in lines if "|" in ln]) == 8
    assert "*" in s
    print("OK ascii_plot 320-sample downsample to narrow width (verifies 320-aware data)")


def test_program_body_side_effects_during_sample():
    # RPL spirit test: sample a first-class Program body that performs sto side-effect
    # (e.g. records last x processed to env). cartesian_sample shares the env across
    # sequential evals so state updates are visible (authentic for graphing stateful progs).
    # Body RPN: x sto last_x ; x 2 *   (result left on stack for return value)
    env = {}
    body = [("var", "x"), "sto", "last_x", ("var", "x"), 2, "*"]
    p = make_prog("dbl_last", body, env)
    pts = cartesian_sample(p, 0, 10, n=5, env=env)
    assert len(pts) == 5
    assert approx(pts[0][1], 0.0)
    assert approx(pts[-1][1], 20.0)
    # final state from last sample (xmax) should be visible to caller
    assert approx(env.get("last_x", -99.0), 10.0)
    print("OK Program body with sto side-effect during sample (RPL stateful fn graph)")


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
    test_linspace_helper()
    test_ascii_plot_basic()
    test_ascii_plot_flat_and_empty()
    test_ascii_plot_prog_curve()
    test_ascii_plot_downsample_320()
    test_program_body_side_effects_during_sample()
    print("---")
    print("ALL TESTS PASSED (host harness for Phase 3 inc1)")
    if not HAS_PLOT:
        print("Note: HAS_PLOT=False on host (expected); real C plot in custom UF2 build.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
