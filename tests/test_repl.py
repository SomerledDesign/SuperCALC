#!/usr/bin/env python3
"""
Host-side tests for SuperCalc.OG Phase 5 inc1 — CalcREPL unified driver.

Exercises mp/ui/calc_repl.py + full integration with prior phases:
  expr (infix + rpn), prog (first-class + sto/run), solver (on prog), stats (via rpn list),
  plot (ascii + sample), hybrid.

All tests use batch_run (deterministic, no tty). run_demo() also exercised.

Run:
    python3 tests/test_repl.py
"""
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mp.ui.calc_repl import CalcREPL, run_demo, batch_run_demo_lines
from mp.lang.prog import is_program, make_prog
from mp.lib.solver import find_root
from mp.plot import cartesian_sample
from mp.apps.solver_app import SolverApp, solve_text
import math

EPS = 1e-9
def approx(a, b, eps=EPS):
    return abs(a - b) <= eps

def test_repl_basic_infix_and_rpn_mixed():
    r = CalcREPL()
    # infix alg (preferred path, exercises eval_infix + C when present)
    v = r.enter("2 + 3 * 4")
    assert approx(v, 14.0), v
    assert approx(r.stack[-1], 14.0)
    # rpn fallback for stack word (dup not valid infix var)
    r.enter("dup")
    assert len(r.stack) == 2
    assert approx(r.stack[-1], 14.0)
    # rpn sequence
    r.enter("5 6 +")
    assert approx(r.stack[-1], 11.0)
    # bare number via infix
    r.enter("42")
    assert approx(r.stack[-1], 42.0)
    # explicit compact infix "2+3" per Phase 5 NEEDS WORK (B-3 routing bug: previously could push
    # var token tuple or other non-scalar "wrong data" on stack for no-space alg like "2+3")
    r.enter("2+3")
    top = r.stack[-1]
    assert approx(top, 5.0), top
    assert isinstance(top, (int, float)) and not isinstance(top, (list, tuple, str)), f"compact infix pushed wrong data type: {top!r} (expected scalar)"
    print("OK basic infix + rpn mixed + stack growth")

def test_repl_vars_sto_rcl_and_side_effects():
    r = CalcREPL()
    r.enter("3.14159 sto pi")
    assert "pi" in r.env
    assert approx(r.env["pi"], 3.14159)
    v = r.enter("pi 2 *")  # infix using var
    assert approx(v, 6.28318, 1e-4)
    r.enter("rcl pi")  # rpn rcl path (rcl name  -- name follows the word)
    assert approx(r.stack[-1], 3.14159)
    print("OK vars + sto/rcl side effects visible in repl")

def test_repl_prog_first_class_and_run_from_repl():
    r = CalcREPL()
    # store prog via .prog cmd (text list literal not supported in rpn_str/to_rpn yet; .prog builds py list + make_prog+sto)
    r.enter(".prog dbl 2 *")
    assert "dbl" in r.env
    assert is_program(r.env["dbl"])
    # call via rcl + run (EVAL alias) after pushing arg; bare word "name" call for progs works in full rpn token lists from py but text rpn_str wraps unknowns as var (covered by other paths + .prog)
    r.enter("7 rcl dbl run")
    assert approx(r.stack[-1], 14.0)
    # another via rcl + run (side effect demo)
    r.enter("3 rcl dbl run")
    assert approx(r.stack[-1], 6.0)
    print("OK first-class prog sto + rcl+run from repl lines")

def test_repl_stats_via_rpn_list_and_len():
    r = CalcREPL()
    # list data is first-class py list token (pushed from caller / prog / rpn token list); text rpn has no [] literal yet (per Phase4/5 scope)
    # Prepend a list data value to visible stack then use "len"/"mean" (exercises direct manip path + hybrid stats)
    lst = [10.0, 20.0, 30.0, 40.0]
    r.stack.append(lst)
    r.enter("len")
    assert approx(r.stack[-1], 4.0)
    r.stack.append(lst)  # re-supply list for next stats word (len consumed the data item)
    r.enter("mean")
    assert approx(r.stack[-1], 25.0)
    r.stack.append(lst)
    r.enter("stdev")
    # sample stdev of [10,20,30,40]: mean=25, var=500/3, stdev~12.90994
    s = r.stack[-1]
    assert approx(s, 12.90994, 1e-4) or approx(s, math.sqrt(500.0/3), 1e-6)
    print("OK list data + len + stats_mean/stdev via repl (direct word path)")

def test_repl_solver_on_infix_and_on_prog_with_x_env():
    r = CalcREPL()
    # infix f
    root = r.enter(".solve x*x-2 1 2")
    assert root is not None
    assert approx(root, math.sqrt(2), 1e-8)
    # prog f with side effect observation (x left at last guess)
    p = r.env.get("quad")  # may not exist; create via make inside env
    from mp.lang.prog import make_prog
    p = make_prog("quad", [("var","x"), 2, "pow", 2, "-"], env=r.env)  # correct: var tok auto rcl; "rcl" word form would need explicit name tok after it
    root2 = find_root(p, 1, 2, env=r.env)
    assert approx(root2, math.sqrt(2), 1e-8)
    assert "x" in r.env  # set during solve
    print("OK .solve cmd + direct find_root(Program) + x-env side effect")

def test_repl_plot_cmd_and_cartesian_integration():
    r = CalcREPL()
    # .plot uses cartesian_sample + ascii_plot internally (small n)
    # We capture by calling enter and checking no exception + some output side
    # (ascii is printed; we just ensure it runs and sample path exercised)
    r.enter(".plot sin(x)")
    # also direct sample of a prog body
    from mp.lang.prog import make_prog
    p = make_prog(None, [("var","x"), 2, "*"])  # 2x (correct var ref, no stray rcl word)
    pts = cartesian_sample(p, -1, 1, n=5, env=r.env)
    assert len(pts) == 5
    assert approx(pts[0][1], -2.0)
    assert approx(pts[-1][1], 2.0)
    print("OK .plot cmd + cartesian_sample(Program) integration")

def test_repl_error_cases_clear_and_underflow():
    r = CalcREPL()
    try:
        r.enter("1 0 /")  # div0 via rpn
    except Exception as e:
        assert "zero" in str(e).lower() or "div" in str(e).lower() or "underflow" in str(e).lower()
    else:
        assert False, "expected exception for div0"
    try:
        r.enter("dup")  # underflow
    except Exception as e:
        assert "underflow" in str(e).lower() or "stack" in str(e).lower()
    else:
        assert False, "expected exception for stack underflow"
    # unknown var stays error (no silent NaN)
    try:
        r.enter("no_such_var 2 *")
    except Exception as e:
        assert "undefined" in str(e).lower() or "enter failed" in str(e).lower()
    else:
        assert False, "expected exception for undefined var"
    print("OK clear errors for div0 / underflow / undef var")

def test_repl_demo_and_batch_run_exercise_everything():
    # run_demo must not crash and must touch prog/solver/stats/plot paths
    run_demo()  # prints but exercises internally
    # batch a small scripted tour
    lines = [
        "2+3",           # infix
        "dup",           # rpn word (direct manip)
        "4 sto x",       # sto (val sto name)
        "rcl x 2 *",     # rcl + rpn (rcl name  -- name follows op)
        "1 2 3 sum",     # rpn that yields scalar via stats (note: sum here receives last scalar not list; covered by dedicated list test)
        "dup",           # manip again
        "drop",
        ".s",            # cmd
    ]
    r = CalcREPL()
    res = r.batch_run(lines)
    assert len(res) >= 6
    # final after drop etc; just assert no crash and stack has some result
    assert len(r.stack) >= 1
    # Per Phase 5 NEEDS WORK: assert actual scalar values (not just lengths)
    # "2+3" is first in the batch lines
    assert approx(res[0], 5.0), res[0]
    print("OK run_demo + batch_run exercise full prior stack (expr/prog/solver/stats/plot)")

def test_repl_demo_lines_helper():
    lines = ["pi 2 /", "sin", ".s"]
    outs = batch_run_demo_lines(lines, echo=False)
    assert len(outs) == 3
    # Per Phase 5 NEEDS WORK: assert actual values for pi/2 and sin(pi/2)
    assert approx(outs[0], 1.5707963267948966, 1e-8), outs[0]
    assert approx(outs[1], 1.0, 1e-8), outs[1]
    print("OK batch_run_demo_lines helper")

def test_repl_lastx_and_rpn_func_words():
    r = CalcREPL()
    # one-line rpn with func (tokenizer now classifies sin as op not var; full eval path)
    v = r.enter("pi 2 / sin")
    assert approx(v, 1.0, 1e-8)
    # lastx auto-stored for scalar result
    assert "lastx" in r.env
    assert approx(r.env["lastx"], 1.0, 1e-8)
    # rcl lastx / direct var resolve in infix/rpn
    r.enter("lastx 2 *")
    assert approx(r.stack[-1], 2.0, 1e-8)
    # stepwise unary also works via visible _execute (after prior result)
    r.enter("3")
    r.enter("sqrt")  # lone func word applies to repl stack top
    assert approx(r.stack[-1], 1.73205080757, 1e-8)
    # lastx updates on rpn scalar too
    assert approx(r.env.get("lastx", 0), 1.73205, 1e-4)
    # solve also updates lastx (via .solve path)
    r.enter(".solve x*x-3 1 2")
    assert approx(r.env.get("lastx", 0), 1.73205, 1e-4)
    print("OK lastx auto + rpn func words (one-line + stepwise) + resolve")

    # abs direct word (visible rpn path + pure manip)
    r2 = CalcREPL()
    r2.enter("7")
    r2.enter("-3 abs")
    assert approx(r2.stack[-1], 3.0)
    # atan2 now covered via delegation (was silent skip in old visible for stepwise "atan2" word)
    r4 = CalcREPL()
    r4.enter("1")
    r4.enter("2")
    r4.enter("atan2")  # direct visible path for lone func word after values on stack
    assert approx(r4.stack[-1], 0.4636476, 1e-5)
    # lastx lift on command entry (pre-op X captured before "abs" mutates)
    r3 = CalcREPL()
    r3.enter("42")
    # at this point lastx may be 0 or prior; entering next cmd that is "lastx" should lift 42 into lastx then push it
    r3.enter("lastx")
    # after "42" line, entering "lastx" line lifts the 42 as pre for the lastx cmd, pushes 42
    assert approx(r3.stack[-1], 42.0)
    # sto lastx special (via core rpn-text path): env updated; next "lastx" word pulls to dedicated + pushes
    r3.enter("99 sto lastx")
    assert approx(r3.env.get("lastx", 0), 99.0)
    r3.enter("lastx")
    assert approx(r3.stack[-1], 99.0)
    assert approx(r3.lastx, 99.0)
    r3.enter("lastx 2 *")
    assert approx(r3.stack[-1], 198.0)
    print("OK abs + lastx lift/sto semantics (pre-op capture + special sto via env pull)")

    # mp.apps surface (solver_app) import + use from repl harness (phase5 packaging)
    app = SolverApp(r3)
    rt = app.solve("x*x-8", 2, 3)
    assert approx(rt, 2.828427, 1e-5)
    assert approx(r3.stack[-1], rt)  # pushed by solve_text when repl bound
    # direct text solve helper (use bracket that contains the root)
    rt2 = solve_text("x*x-1", 0, 2, env={})
    assert approx(rt2, 1.0)
    print("OK mp.apps.solver_app import + SolverApp + solve_text integration")


def test_repl_micropython_typing_guard_and_compact_infix_robust():
    """Exercise the Phase 5 blocker fix + ensure compact infix never pushes wrong data (var tuple / list / str).
    The guard test uses __import__ patch to simulate firmware without "typing" module (common on MPy ports).
    Covers the early infix heuristic path for no-space alg and the last-fallback compact path indirectly
    via varied alg lines that must always yield scalar on stack.
    """
    import builtins as _bi
    _orig_imp = _bi.__import__
    def _block_typing(name, *a, **k):
        if isinstance(name, str) and (name == "typing" or name.startswith("typing.")):
            raise ImportError("No module named 'typing' (sim MPy)")
        return _orig_imp(name, *a, **k)
    _bi.__import__ = _block_typing
    try:
        # reimport under block to prove no hard dep on typing (the exact blocker)
        for m in list(sys.modules.keys()):
            if m.startswith("mp.lang") or m.startswith("mp.plot") or m.startswith("mp.lib.solver") or m.startswith("mp.ui.calc_repl") or m.startswith("mp.apps"):
                sys.modules.pop(m, None)
        from mp.ui.calc_repl import CalcREPL as _CR
        from mp.lib.solver import find_root as _fr
        from mp.plot import cartesian_sample as _cs
        print("  (guard) modules imported under blocked typing: OK")
        r = _CR()
        # compact infix cases (no spaces) -- must push scalar, never the ('var', '2+3') token or other
        for expr, expect in [("2+3", 5.0), ("1+2*3", 7.0), ("2^3", 8.0), ("(1+2)*3", 9.0)]:
            v = r.enter(expr)
            top = r.stack[-1]
            assert approx(top, expect), f"{expr} => {top}"
            assert isinstance(top, (int, float)) and not isinstance(top, (list, tuple, str)), \
                f"compact infix {expr} pushed wrong data type: {top!r}"
        # also with var (after sto) and func in compact alg form
        r.enter("3.5 sto a")
        v = r.enter("a+0.5")
        assert approx(v, 4.0)
        assert isinstance(r.stack[-1], (int, float))
        v = r.enter("sin(pi/2)+1")
        assert approx(v, 2.0)
        assert isinstance(r.stack[-1], (int, float))
        # bare predefs and bare user var (these hit the rpn visible path / data classification; must resolve to scalar not var-token or list(['var',..]))
        v = r.enter("pi")
        assert approx(v, 3.1415926535, 1e-9)
        assert isinstance(r.stack[-1], (int, float)) and not isinstance(r.stack[-1], (list, tuple))
        v = r.enter("e")
        assert approx(v, 2.718281828, 1e-9)
        assert isinstance(r.stack[-1], (int, float)) and not isinstance(r.stack[-1], (list, tuple))
        # bare var after sto (no alg op chars, so no early infix cue; must not push var marker)
        r.enter("42 sto b")
        v = r.enter("b")
        assert approx(v, 42.0)
        assert isinstance(r.stack[-1], (int, float)) and not isinstance(r.stack[-1], (list, tuple))
        # undef compact with + should error cleanly (no silent var-token data corruption on stack)
        try:
            r.enter("nope+1")
            assert False, "expected error for undef in compact"
        except Exception as e:
            assert "undefined" in str(e).lower() or "enter failed" in str(e).lower()
        print("  (guard+compact) multiple no-space infix alg + scalar type asserts: OK")
    finally:
        _bi.__import__ = _orig_imp
    print("OK micropython typing guard (imports+run under no-typing) + compact infix data integrity")


def test_repl_cas_surface_stub_and_rpn():
    """Phase 7 inc2: CAS thin surface (stub) + dispatch + Symbolic wrapper + RPN word coverage for all 3 ops."""
    from mp.ui.calc_repl import CalcREPL
    from mp.lib.cas import HAS_CAS as _has, simplify as _simp, solve as _csol, diff as _cdif, info as _cinfo, Symbolic
    r = CalcREPL()
    # direct cas via rpn-style on stack (str pushed as data, then cas word) — simplify
    r.stack.append("x+x")
    res = r.enter("simplify")
    assert isinstance(res, (str, Symbolic))
    assert "stub:simplify" in str(res) or (not _has and "x+x" in str(res))
    # diff via direct RPN word (auditor Minor: was untested)
    r.stack.append("x^2")
    dres = r.enter("diff")
    assert isinstance(dres, (str, Symbolic))
    assert "stub:diff" in str(dres)
    # solve via RPN word 2-arg (eq then var on stack) + 1-arg default
    r3 = CalcREPL()
    r3.stack.append("x^2-25")
    r3.stack.append("x")
    sres2 = r3.enter("solve")
    assert isinstance(sres2, (str, Symbolic))
    assert "stub:solve" in str(sres2)
    r3.stack.append("y^2-9")
    sres1 = r3.enter("solve")  # 1-arg, defaults var x but here eq has y (stub still exercises path)
    assert isinstance(sres1, (str, Symbolic))
    # .cas dot handler (implicit simplify and explicit)
    r2 = CalcREPL()
    c1 = r2.enter(".cas x^2 + 2*x + 1")
    assert isinstance(c1, (str, Symbolic)) and "stub:simplify" in str(c1)
    c2 = r2.enter(".cas solve x^2-2 x")
    assert isinstance(c2, (str, Symbolic)) and "stub:solve" in str(c2)
    c3 = r2.enter(".cas diff x^3 x")
    assert isinstance(c3, (str, Symbolic)) and "stub:diff" in str(c3)
    # info visible
    inf = _cinfo()
    assert "has_cas" in inf
    # Symbolic is str subclass (RPL first-class + future detectability)
    assert issubclass(Symbolic, str)
    print("OK cas surface (stub + Symbolic + all RPN words: simplify/diff/solve 2arg/1arg + .cas + delegation)")


if __name__ == "__main__":
    test_repl_basic_infix_and_rpn_mixed()
    test_repl_vars_sto_rcl_and_side_effects()
    test_repl_prog_first_class_and_run_from_repl()
    test_repl_stats_via_rpn_list_and_len()
    test_repl_solver_on_infix_and_on_prog_with_x_env()
    test_repl_plot_cmd_and_cartesian_integration()
    test_repl_error_cases_clear_and_underflow()
    test_repl_demo_and_batch_run_exercise_everything()
    test_repl_demo_lines_helper()
    test_repl_lastx_and_rpn_func_words()
    test_repl_micropython_typing_guard_and_compact_infix_robust()
    test_repl_cas_surface_stub_and_rpn()
    print("\nALL Phase 5+7 REPL tests PASSED")


