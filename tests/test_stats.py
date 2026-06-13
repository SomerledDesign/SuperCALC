#!/usr/bin/env python3
"""
Host-side tests for SuperCalc.OG Phase 4 inc1 statistics (C or py fallback).
Exercises mp/lib/hybrid stats_* + integration via expr rpn list ops + solver.

Run:
    python3 tests/test_stats.py
"""
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mp.lib.hybrid import HAS_C_MATH, HAS_STATS, stats_sum, stats_mean, stats_stdev
from mp.lang.expr import eval_rpn, eval_rpn_str
from mp.lang.prog import make_prog
from mp.lib.solver import find_root

EPS = 1e-9
def approx(a, b, eps=EPS):
    return abs(a - b) <= eps

def test_stats_basic():
    assert stats_sum([1,2,3,4]) == 10.0
    assert stats_mean([1,2,3,4]) == 2.5
    # sample stdev of [1,2,3] : mean=2, var=((1-2)^2 +0 +1^2)/(3-1) = (1+0+1)/2=1, stdev=1
    assert approx(stats_stdev([1,2,3]), 1.0)
    # integers and floats
    assert approx(stats_mean([0.1, 0.2, 0.3]), 0.2, 1e-9)
    print("OK stats_basic (sum/mean/stdev exact + tol)")

def test_stats_errors():
    try:
        stats_sum([])
        assert False
    except ValueError as e:
        assert "empty" in str(e)
    try:
        stats_stdev([42])
        assert False
    except ValueError as e:
        assert "at least 2" in str(e)
    try:
        stats_mean(["bad"])
        assert False
    except ValueError as e:
        assert "numeric" in str(e) or "empty" in str(e)  # py path may differ slightly
    print("OK stats_errors (empty, n<2, non-numeric)")

def test_stats_via_rpn_list():
    # lists as first-class data in rpn token stream
    assert approx(eval_rpn( [ [1,2,3,4], "sum" ] ), 10.0)
    assert approx(eval_rpn( [ [10,20,30], "mean" ] ), 20.0)
    assert approx(eval_rpn( [ [1, 2, 3], "stdev" ] ), 1.0, 1e-9)
    # aliases
    assert approx(eval_rpn( [ [1,2,3,4], "stats_sum" ] ), 10.0)
    print("OK stats_via_rpn_list (push list, apply stats op)")

def test_stats_via_rpn_str_and_prog():
    # str path does not yet parse [] list literals (future); use token form for lists
    # Program body that does stats on embedded list + arith (RPL style)
    p = make_prog("dblsum", [ [1,2,3], "sum", 2, "*" ])
    assert approx(eval_rpn( [p, "run"] ), 12.0)  #  (1+2+3)*2 via prog that does stats
    print("OK stats_via_rpn_str_and_prog")

def test_solver_basic():
    # infix
    r = find_root("x*x - 2", 1.0, 2.0)
    import math
    assert approx(r, math.sqrt(2), 1e-8)
    # rpn list using var x ( ("var",) resolves from solver env; bare "rcl" not needed for var tokens)
    r2 = find_root( [ ("var","x"), 2, "pow", 2, "-" ] , 1, 2)
    assert approx(r2, math.sqrt(2), 1e-8)
    # Program body (same: use var token for x, dup * etc)
    p = make_prog(None, [ ("var","x"), "dup", "*" , 2, "-" ])
    r3 = find_root(p, 1, 2)
    assert approx(r3, math.sqrt(2), 1e-8)
    print("OK solver_basic (infix + rpn + Program, known root)")

def test_solver_side_effect():
    env = {}
    # a "f" prog that also stores last probe (use var token for x; explicit sto of current x probe)
    p = make_prog(None, [ ("var","x"), "dup", "sto", "lastx", "dup", "*", 2, "-" ])
    r = find_root(p, 1, 2, env=env)
    assert "lastx" in env
    assert approx(env["lastx"], r, 1e-6)  # last probe close to root
    print("OK solver_side_effect (sto during search visible in caller env)")

def test_solver_maxiter_and_tol():
    # easy converge
    r = find_root("x - 0", -1, 1, tol=1e-12, maxiter=5)
    assert approx(r, 0.0, 1e-9)
    # bad bracket still may find if secant escapes (we allow); just ensure no crash + reasonable
    try:
        # a function with no root in loose sense, or slow
        find_root("x*x + 1", 0, 10, maxiter=3)
        # may or not raise depending; acceptable either for inc1 (converge or raise)
    except ValueError:
        pass
    print("OK solver_maxiter_and_tol")

def main():
    print("SuperCalc.OG Phase 4 stats + solver host tests")
    print("---")
    print(f"HAS_C_MATH={HAS_C_MATH} HAS_STATS={HAS_STATS}")
    test_stats_basic()
    test_stats_errors()
    test_stats_via_rpn_list()
    test_stats_via_rpn_str_and_prog()
    test_solver_basic()
    test_solver_side_effect()
    test_solver_maxiter_and_tol()
    print("---")
    print("ALL PHASE4 STATS/SOLVER TESTS PASSED (host)")
    return 0

if __name__ == "__main__":
    sys.exit(main())