#!/usr/bin/env python3
"""
Host-side tests for SuperCalc.OG Phase 7 CAS thin surface (mp/lib/cas.py).

Covers stub/eigen delegation, Symbolic wrapper, RPN dispatch, and prog-body
integration (RPL spirit: symbolic values on live stack, sto/rcl roundtrip).

Run:
    python3 tests/test_cas.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mp.lib.cas import HAS_CAS, info, version, simplify, solve, diff, Symbolic
from mp.lang.expr import execute_rpn_body, eval_rpn
from mp.lang.prog import make_prog


def test_symbolic_wrapper_and_stub_paths():
    assert issubclass(Symbolic, str)
    s = simplify("x+x")
    assert isinstance(s, Symbolic)
    if not HAS_CAS:
        assert "stub:simplify" in str(s)
    sol = solve("x^2-25", "x")
    d = diff("x^2", "x")
    assert isinstance(sol, Symbolic)
    assert isinstance(d, Symbolic)
    if not HAS_CAS:
        assert "stub:solve" in str(sol)
        assert "stub:diff" in str(d)
    inf = info()
    assert "has_cas" in inf and "backend" in inf
    assert isinstance(version(), str)
    print("OK Symbolic + stub paths + info/version")


def test_rpn_cas_words_all_three():
    stack = ["a+b"]
    execute_rpn_body(["simplify"], stack, {})
    assert isinstance(stack[-1], Symbolic)

    stack = ["x^2-9", "x"]
    execute_rpn_body(["solve"], stack, {})
    assert isinstance(stack[-1], Symbolic)

    stack = ["x^3"]
    execute_rpn_body(["diff"], stack, {})
    assert isinstance(stack[-1], Symbolic)
    print("OK RPN simplify/solve/diff via execute_rpn_body")


def test_prog_body_cas_rcl_simplify():
    env = {"eq": "x+x"}
    p = make_prog("simp", ["rcl", "eq", "simplify"], env)
    stack = []
    execute_rpn_body(p.body, stack, env)
    assert len(stack) == 1
    assert isinstance(stack[-1], Symbolic)
    assert "stub:simplify" in str(stack[-1]) or HAS_CAS
    print("OK prog body rcl+eq+simplify")


def test_symbolic_sto_rcl_roundtrip():
    env = {}
    stack = ["sin(x)^2+cos(x)^2"]
    execute_rpn_body(["simplify", "sto", "sym", "rcl", "sym"], stack, env)
    assert "sym" in env
    assert isinstance(env["sym"], Symbolic)
    assert stack[-1] == env["sym"]
    assert str(stack[-1]) == str(env["sym"])
    print("OK Symbolic sto/rcl roundtrip on stack+env")


def test_eval_rpn_cas_in_token_stream():
    env = {"eq": "x^2-25", "v": "x"}
    res = eval_rpn(["rcl", "eq", "rcl", "v", "solve"], env)
    assert isinstance(res, Symbolic)
    if not HAS_CAS:
        assert "stub:solve" in str(res)
    print("OK eval_rpn 2-arg solve via rcl+env")


def main():
    print("Phase 7 CAS host tests")
    print("---")
    test_symbolic_wrapper_and_stub_paths()
    test_rpn_cas_words_all_three()
    test_prog_body_cas_rcl_simplify()
    test_symbolic_sto_rcl_roundtrip()
    test_eval_rpn_cas_in_token_stream()
    print("---")
    print("ALL PHASE 7 CAS TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())