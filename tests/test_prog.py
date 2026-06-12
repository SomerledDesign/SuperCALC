#!/usr/bin/env python3
"""
Host-side tests for SuperCalc.OG Phase 2 programmable language skeleton.
Programs as first-class objects (sto/rcl, run), inline shared-stack execution via
expr (RPL semantics), "run"/"eval" op, make/run helpers, error cases.

Exercises mp/lang/prog.py + integration in expr + hybrid glue (fallback path).
Run:
    python3 tests/test_prog.py
"""
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mp.lang.expr import eval_rpn, eval_rpn_str, to_rpn, eval_infix
from mp.lang.prog import Program, make_prog, run_prog, is_program, EVAL_ALIASES
from mp.lib.hybrid import HAS_VM, vm_version, vm_exec

EPS = 1e-10
def approx(a, b, eps=EPS):
    return abs(a - b) <= eps

def test_program_basics():
    p = Program([2, "*"], name="dbl")
    assert p.name == "dbl"
    assert p.body == [2, "*"]
    assert is_program(p)
    assert not is_program([2, "*"])
    assert "run" in EVAL_ALIASES
    print("OK Program basics + is_program + aliases")

def test_make_and_run_prog():
    env = {}
    # dbl: expects a value on stack, multiplies by 2, leaves result
    p = make_prog("dbl", [2, "*"], env)
    assert "dbl" in env
    assert env["dbl"] is p
    # To run a body that consumes stack, we use the rpn "run" op or run_prog
    # run_prog uses top-level eval_rpn which starts a fresh stack; for bodies
    # needing input we exercise via a calling expression that seeds then runs.
    # Seed 5, run the dbl prog object directly in token stream (supported).
    res = eval_rpn([5, "rcl", "dbl", "run"], env)  # rcl pushes prog object (no auto-exec), run pops+execs it (exercises EVAL_ALIASES handler)
    assert approx(res, 10.0)
    print("OK make_prog + store in env + run via rpn 'run' op (inline)")

def test_run_prog_api():
    env = {"x": 3.0}
    p = make_prog("triple", [3, "*"], env)
    # run_prog helper (direct)
    # Seed via a temp rpn that leaves value, but run_prog always fresh: use body that is self-contained or test result only
    # For API test use a body with literal:  [7, 3, "*"] -> 21
    p2 = make_prog("litmul", [7, 3, "*"])
    assert approx(run_prog(p2), 21.0)
    # name lookup
    env["litmul"] = p2
    assert approx(run_prog("litmul", env), 21.0)
    print("OK run_prog (object + by name) + result only bodies")

def test_first_class_store_recall_exec():
    env = {}
    p = make_prog("quad", [2, "pow"], env)  # x^2 , assumes x on stack
    # store under another name via sto in rpn (first-class value)
    res = eval_rpn([p, "sto", "q2", 99], env)  # dummy 99 leaves value for top-level eval_rpn non-empty contract; sto still happens
    assert "q2" in env
    assert is_program(env["q2"])
    # recall and run via explicit eval op (alias)
    res = eval_rpn([5, "rcl", "q2", "eval"], env)
    assert approx(res, 25.0)
    # direct name as word in stream also supported via var resolve -> exec path
    res2 = eval_rpn([4, "q2"], env)  # bare name resolves and since prog, inline exec
    assert approx(res2, 16.0)
    print("OK first-class: sto/rcl of Program + run via eval alias + bare name exec")

def test_prog_with_sto_inside():
    env = {}
    # prog that stores its result
    p = make_prog("savepi", [3.14159, "sto", "pi"], env)
    eval_rpn([p, "run", 0], env)  # run the storer (side-effect prog); dummy 0 satisfies top-level non-empty
    assert approx(env.get("pi", 0), 3.14159)
    print("OK program with internal sto side-effect visible to caller env")

def test_rpn_str_with_run():
    env = {}
    p = make_prog("inc", [1, "+"], env)
    env["inc"] = p
    # '5 inc run' form
    res = eval_rpn_str("5 rcl inc run", env)  # rcl pushes prog obj (data), run executes it against 5
    assert approx(res, 6.0)
    res2 = eval_rpn_str("9 rcl inc eval", env)
    assert approx(res2, 10.0)
    print("OK eval_rpn_str with run/eval ops on programs")

def test_vm_hybrid_glue():
    v = vm_version()
    assert isinstance(v, str) and ("vm" in v or "fallback" in v)
    assert HAS_VM in (True, False)  # documents the boundary
    # vm_exec on prog
    env = {}
    p = make_prog("five", [5], env)
    assert approx(vm_exec(p), 5.0)
    # vm_exec on plain rpn list
    assert approx(vm_exec([2, 3, "+"]), 5.0)
    print("OK vm_version + vm_exec (hybrid glue + py fallback)")

def test_errors():
    env = {}
    p = make_prog("under", ["+"], env)  # will underflow when run
    try:
        eval_rpn([p, "run"], env)
        assert False, "expected underflow"
    except ValueError as ex:
        assert "underflow" in str(ex)
    try:
        run_prog("no_such", env)
        assert False
    except ValueError:
        pass
    print("OK error cases (prog underflow, missing name)")

def test_program_ctor_string_first_arg():
    # N-2 hygiene from Phase 2 QA: explicitly test the rare string-first path
    # Program("name") treats str as name (body empty); documented as flexible but secondary to kw form.
    p = Program("myprog")
    assert p.name == "myprog"
    assert p.body == []
    assert is_program(p)
    # recommended/named+body form (avoids signature conflict on first 'body' param)
    p2 = Program(body=[1, 2, "+"], name="withbody")
    assert p2.name == "withbody"
    assert p2.body == [1, 2, "+"]
    # str-first path is intentionally "rare" (see ctor comments); we exercised pure name case above.
    # Mixed Program("name", body=...) collides because first positional binds to 'body' param.
    print("OK Program ctor string-first-arg path (documented behavior)")

def main():
    print("SuperCalc.OG Phase 2 prog skeleton host tests")
    print("---")
    test_program_basics()
    test_make_and_run_prog()
    test_run_prog_api()
    test_first_class_store_recall_exec()
    test_prog_with_sto_inside()
    test_rpn_str_with_run()
    test_vm_hybrid_glue()
    test_errors()
    test_program_ctor_string_first_arg()
    print("---")
    print("ALL TESTS PASSED (host harness for Phase 2 inc1)")
    if not HAS_VM:
        print("Note: HAS_VM=False on host (expected); real C vm in custom UF2 build.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
