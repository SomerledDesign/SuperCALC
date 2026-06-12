#!/usr/bin/env python3
"""
Host-side tests for SuperCalc.OG Phase 1 expression system (infix + RPN + stack + vars).
Exercises mp/lang/expr.py which uses hybrid (C or py fallback).

Run:
    python3 tests/test_expr.py
"""

import sys
import os
import math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mp.lang.expr import to_rpn, eval_infix, eval_rpn, eval_rpn_str, HAS_C_MATH

EPS = 1e-10

def approx(a, b, eps=EPS):
    return abs(a - b) <= eps

def test_to_rpn_basic():
    r = to_rpn("2+3")
    assert r == [2.0, 3.0, "+"], r
    r = to_rpn("2 + 3 * 4")
    # 2 3 4 * +   (prec)
    assert r == [2.0, 3.0, 4.0, "*", "+"], r
    r = to_rpn("(2+3)*4")
    assert r == [2.0, 3.0, "+", 4.0, "*"], r
    print("OK to_rpn basic + prec + parens")

def test_eval_infix_numeric():
    assert approx(eval_infix("2+3"), 5.0)
    assert approx(eval_infix("2+3*4"), 14.0)
    assert approx(eval_infix("(2+3)*4"), 20.0)
    assert approx(eval_infix("2^3 + 1"), 9.0)
    assert approx(eval_infix("sin(0)"), 0.0)
    assert approx(eval_infix("cos(pi/2)"), 0.0, 1e-9)
    assert approx(eval_infix("sqrt(9) + log(e)"), 4.0, 1e-9)
    assert approx(eval_infix("2 * pi"), 2 * math.pi)
    print("OK eval_infix numeric + funcs + pi")

def test_eval_infix_vars():
    env = {"x": 3.0, "y": 4.0}
    assert approx(eval_infix("x + y * 2", env), 3 + 8)
    assert approx(eval_infix("sin(x)", {"x": math.pi/2}), 1.0, 1e-9)
    # predef pi even without env
    assert approx(eval_infix("pi * 2"), 2 * math.pi)
    print("OK eval_infix with vars + predefs")

def test_eval_rpn_core():
    assert approx(eval_rpn([2, 3, "+"]), 5)
    assert approx(eval_rpn([2, 3, 4, "*", "+"]), 14)
    assert approx(eval_rpn([9, "sqrt", 2, "pow"]), 3**2)  # sqrt9 ^2 =9? wait 3^2=9
    assert approx(eval_rpn([2, 3, "pow"]), 8)
    print("OK eval_rpn core numeric")

def test_rpn_stack_manip():
    assert approx(eval_rpn([5, "dup", "+"]), 10)
    assert approx(eval_rpn([1, 2, "swap", "-"]), 1.0)  # 2-1 after swap
    # 1 2 3 over +  => push 1,2,3 ; over pushes copy of 2nd=2 ; + => 3+2=5 ; top=5 (1 still below)
    res = eval_rpn([1, 2, 3, "over", "+"])
    assert approx(res, 5.0)
    # drop test: 10 20 drop 3 +  => stack after drop=[10]; + 10+3 ->13
    assert approx(eval_rpn([10, 20, "drop", 3, "+"]), 13)
    print("OK eval_rpn stack manip (dup/swap/over/drop)")

def test_rpn_with_vars():
    env = {}
    # 3.14 sto pi   rcl pi  2 *
    val = eval_rpn([3.14159, "sto", "pi", "rcl", "pi", 2, "*"], env)
    assert approx(val, 3.14159 * 2)
    assert approx(env.get("pi", 0), 3.14159)
    # rcl via predef if not set
    env2 = {}
    val2 = eval_rpn(["rcl", "e", 2, "*"], env2)
    assert approx(val2, math.e * 2)
    print("OK eval_rpn sto/rcl + env mutation + predefs")

def test_eval_rpn_str():
    assert approx(eval_rpn_str("2 3 + 4 *"), 20.0)
    env = {}
    val = eval_rpn_str("3.14 sto pi rcl pi 2 *", env)
    assert approx(val, 6.28)
    assert "pi" in env
    print("OK eval_rpn_str (space form) + sto")

def test_errors():
    try:
        eval_infix("2 + )")
        assert False
    except ValueError:
        pass
    try:
        eval_rpn([1, "+"])
        assert False
    except ValueError:
        pass
    try:
        eval_rpn([1, 0, "/"])
        assert False
    except ValueError:
        pass
    try:
        eval_infix("foo + 1")  # unknown var
        assert False
    except ValueError:
        pass
    print("OK error cases (mismatch, underflow, div0, undef var)")

def test_precedence_associativity():
    # M-1 / M-2 fixes: HP-standard and math convention
    # -2^2 must be -(2^2) == -4 (not (-2)^2 == 4)
    assert approx(eval_infix("-2^2"), -4.0)
    # 2^2^3 must be 2^(2^3) == 256 (not (2^2)^3 == 64)
    assert approx(eval_infix("2^2^3"), 256.0)
    # also 2^3^2 == 2^9 == 512 for extra
    assert approx(eval_infix("2^3^2"), 512.0)
    # mixed to confirm unary vs mul etc still correct
    assert approx(eval_infix("-2*3"), -6.0)
    assert approx(eval_infix("-2+3"), 1.0)
    print("OK precedence: unary- < ^ (right-assoc), > * / + -")

def test_rpn_str_aliases():
    # m-2: op name aliases must work in the convenience str API
    assert approx(eval_rpn_str("2 3 add"), 5.0)
    assert approx(eval_rpn_str("2 3 pow"), 8.0)
    assert approx(eval_rpn_str("2 3 mul 4 add"), 10.0)
    assert approx(eval_rpn_str("9 sqrt 2 pow"), 9.0)  # (sqrt9)^2
    print("OK eval_rpn_str op aliases (add sub mul div pow)")

def main():
    print("SuperCalc.OG expr test harness (Phase 1) — host fallback path")
    print(f"HAS_C_MATH={HAS_C_MATH} (C rpn_eval used only on device)")
    print("---")
    test_to_rpn_basic()
    test_eval_infix_numeric()
    test_eval_infix_vars()
    test_eval_rpn_core()
    test_rpn_stack_manip()
    test_rpn_with_vars()
    test_eval_rpn_str()
    test_errors()
    test_precedence_associativity()
    test_rpn_str_aliases()
    print("---")
    print("ALL EXPR TESTS PASSED")
    if not HAS_C_MATH:
        print("Note: C rpn_eval + leafs verified only via hybrid fallback on host.")
        print("      Flash custom UF2 (src/math + our mp/lang) and re-run for native path.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
