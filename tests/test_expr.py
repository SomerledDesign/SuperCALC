#!/usr/bin/env python3
"""
Host-side tests for SuperCalc.OG Phase 1 expression system (infix + RPN + stack + vars)
+ Phase 2 programmable language skeleton (programs as first-class, inline execution).

Exercises mp/lang/expr.py + mp/lang/prog.py which use hybrid (C or py fallback).

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
from mp.lang.prog import make_prog  # Phase 4 tests use it directly

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
    # unary + handling (Phase 2 hygiene)
    assert to_rpn("+3") == [3.0], to_rpn("+3")
    assert to_rpn("+ 3.5") == [3.5], to_rpn("+ 3.5")
    assert to_rpn("1 + +2") == [1.0, 2.0, "+"], to_rpn("1 + +2")  # second + ignored as unary
    print("OK to_rpn basic + prec + parens + unary+")

def test_eval_infix_numeric():
    assert approx(eval_infix("2+3"), 5.0)
    assert approx(eval_infix("2+3*4"), 14.0)
    assert approx(eval_infix("(2+3)*4"), 20.0)
    assert approx(eval_infix("2^3 + 1"), 9.0)
    assert approx(eval_infix("sin(0)"), 0.0)
    assert approx(eval_infix("cos(pi/2)"), 0.0, 1e-9)
    assert approx(eval_infix("sqrt(9) + log(e)"), 4.0, 1e-9)
    assert approx(eval_infix("log10(100)"), 2.0)
    assert approx(eval_infix("asin(0) + acos(1)"), 0.0)
    assert approx(eval_infix("2 * pi"), 2 * math.pi)
    assert approx(eval_infix("+5"), 5.0)
    assert approx(eval_infix("1 + +2"), 3.0)
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

# --- Phase 2 program skeleton tests (first-class + inline shared-stack execution) ---

def test_program_basic():
    from mp.lang.prog import Program, store_program, is_program
    env = {}
    # double top of stack
    dbl = Program(["dup", "*"], name="dbl")
    assert is_program(dbl)
    store_program("dbl", dbl, env)
    # direct python run
    res = eval_rpn([4, "dbl"], env)
    assert approx(res, 16.0)
    # name as word in rpn text triggers auto-exec (RPL word call)
    res2 = eval_rpn_str("5 dbl", env)
    assert approx(res2, 25.0)
    # stored under name
    assert "dbl" in env and is_program(env["dbl"])
    print("OK Phase2 Program define + name-as-call + store")

def test_program_sto_rcl_eval():
    from mp.lang.prog import Program, store_program
    env = {}
    # program that squares then adds 1: x -- x^2+1
    sq1 = Program([ "dup", "*", 1, "+" ], name="sq1")
    store_program("sq1", sq1, env)
    env2 = {}
    store_program("sq1", sq1, env2)
    # 3 sq1  (name call)
    assert approx(eval_rpn([3, "sq1"], env2), 10.0)
    # push prog via rcl then eval (first-class: recall the program object on stack, eval executes it against the arg left below)
    assert approx(eval_rpn([3, "rcl", "sq1", "eval"], env2), 10.0)
    print("OK Phase2 rcl program + explicit eval + mixed call")

def test_program_side_effects_and_nesting():
    from mp.lang.prog import Program, store_program
    env = {}
    # inner program: increments a var 'c' and leaves it
    inc = Program([ "rcl", "c", 1, "+", "sto", "c" ], name="inc")
    store_program("inc", inc, env)
    env["c"] = 0.0
    # run twice via name
    eval_rpn(["inc", "inc", 0], env)  # dummy value left so top-level eval_rpn contract (non-empty) is satisfied; side effects still applied
    assert approx(env["c"], 2.0)
    # a caller program that calls inc
    caller = Program([ 10, "sto", "c", "inc", "rcl", "c" ], name="caller")
    store_program("caller", caller, env)
    res = eval_rpn(["caller"], env)
    assert approx(res, 11.0)
    print("OK Phase2 programs with sto/rcl side effects + 'calling' other programs")

def test_program_first_class():
    from mp.lang.prog import Program, store_program
    env = {}
    dbl = Program(["dup", "*"])
    store_program("dbl", dbl, env)
    # store the program itself under another name (first-class)
    env["alias"] = env["dbl"]
    assert approx(eval_rpn([7, "alias"], env), 49.0)
    print("OK Phase2 first-class: program values storable and invocable under aliases")

# --- Phase 4 inc1: list data + stats ops in rpn + solver integration ---
def test_phase4_list_data_in_rpn():
    # lists pushed and round-tripped as data (parallel to Program)
    res = eval_rpn( [ [1, 2, 3], "dup", "drop" ] )  # push list, dup it (as data), drop one, return the list
    assert res == [1, 2, 3]
    # sto a list (sto is side-effect only; follow with rcl of name to leave value + satisfy non-empty top-level)
    env = {}
    res = eval_rpn( [ [10,20], "sto", "data", "rcl", "data" ], env)
    assert env["data"] == [10, 20]
    assert res == [10, 20]
    print("OK phase4 list_data_in_rpn (push, dup/drop, sto/rcl as data)")

def test_phase4_stats_rpn_ops():
    assert approx( eval_rpn( [ [2, 4, 6], "sum" ] ), 12.0 )
    assert approx( eval_rpn( [ [1, 2, 3], "mean" ] ), 2.0 )
    assert approx( eval_rpn( [ [1, 2, 3], "stdev" ] ), 1.0, 1e-9 )
    # inside program body
    p = make_prog("sum3", [ [1,2,3], "sum" ])
    assert approx( eval_rpn( [p, "run"] ), 6.0 )
    print("OK phase4 stats_rpn_ops (list + sum/mean/stdev, in prog)")

def test_phase4_solver_integration():
    from mp.lib.solver import find_root
    import math
    # infix via solver (re-uses expr)
    assert approx( find_root("x*x-2", 1, 2), math.sqrt(2), 1e-8 )
    # rpn list f (var token)
    assert approx( find_root( [ ("var","x"), 2, "pow", 2, "-" ], 1, 2), math.sqrt(2), 1e-8 )
    # program as f (x-env contract)
    p = make_prog(None, [ ("var","x"), "dup", "*", 2, "-" ])
    assert approx( find_root(p, 1, 2), math.sqrt(2), 1e-8 )
    print("OK phase4 solver_integration (infix/rpn/prog roots)")

def main():
    print("SuperCalc.OG expr test harness (Phase 1 + Phase 2 prog skeleton) — host fallback path")
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
    test_program_basic()
    test_program_sto_rcl_eval()
    test_program_side_effects_and_nesting()
    test_program_first_class()
    test_phase4_list_data_in_rpn()
    test_phase4_stats_rpn_ops()
    test_phase4_solver_integration()
    print("---")
    print("ALL EXPR + PROG TESTS PASSED")
    if not HAS_C_MATH:
        print("Note: C rpn_eval + leafs verified only via hybrid fallback on host.")
        print("      Flash custom UF2 (src/math + our mp/lang) and re-run for native path.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
