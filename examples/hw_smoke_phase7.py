"""
Phase 7 hardware smoke test — CAS surface on PicoCalc + Pico 2 W.

Push mp/ and this file via dashboard or mpremote, then from device REPL:

    import hw_smoke_phase7
    hw_smoke_phase7.run()

On success, on the host run:

    ./tools/ralph.sh record-hardware-verification "Phase 7 CAS smoke OK (eigenmath or stub)"

MicroPython-safe: no path helpers from os, no typing, minimal imports.
"""

import sys


def _ok(msg):
    print("OK:", msg)
    return True


def _fail(msg):
    print("FAIL:", msg)
    return False


def run():
    """Run Phase 7 CAS smoke checks. Returns True if all required checks pass."""
    passed = 0
    failed = 0
    print("SuperCalc.OG Phase 7 hardware smoke (CAS)")
    print("---")

    # 1) Thin CAS module import + backend info
    try:
        from mp.lib.cas import HAS_CAS, info, version, simplify, solve, diff, Symbolic
        inf = info()
        print("cas.info():", inf)
        print("cas.version():", version())
        print("HAS_CAS:", HAS_CAS)
        s = simplify("x+x")
        print("simplify('x+x'):", s)
        if not isinstance(s, Symbolic):
            failed += 1
            _fail("simplify must return Symbolic")
        elif HAS_CAS:
            passed += 1
            _ok("eigenmath CAS path")
        elif "stub:simplify" in str(s):
            passed += 1
            _ok("CAS stub path (no eigenmath)")
        else:
            failed += 1
            _fail("unexpected simplify result: " + str(s))
    except Exception as e:
        failed += 1
        _fail("mp.lib.cas: " + str(e))
        print("Hint: push the mp/ directory to the device.")

    # 2) solve + diff stub/eigen paths
    try:
        from mp.lib.cas import solve, diff, Symbolic
        sol = solve("x^2-4", "x")
        d = diff("x^3", "x")
        print("solve('x^2-4','x'):", sol)
        print("diff('x^3','x'):", d)
        if not isinstance(sol, Symbolic) or not isinstance(d, Symbolic):
            failed += 1
            _fail("solve/diff must return Symbolic")
        else:
            passed += 1
            _ok("solve + diff")
    except Exception as e:
        failed += 1
        _fail("solve/diff: " + str(e))

    # 3) RPN CAS word via expr (shared dispatch)
    try:
        from mp.lang.expr import execute_rpn_body
        from mp.lib.cas import Symbolic
        stack = ["sin(x)^2+cos(x)^2"]
        execute_rpn_body(["simplify"], stack, {})
        if not stack:
            failed += 1
            _fail("CAS rpn left empty stack")
        elif not isinstance(stack[-1], Symbolic):
            failed += 1
            _fail("CAS rpn result not Symbolic")
        else:
            print("rpn simplify result:", stack[-1])
            passed += 1
            _ok("expr execute_rpn_body CAS word")
    except Exception as e:
        failed += 1
        _fail("expr CAS rpn: " + str(e))

    # 4) Program body with CAS (RPL spirit)
    try:
        from mp.lang.prog import make_prog, run_prog
        from mp.lib.cas import Symbolic
        env = {"eq": "x+x"}
        p = make_prog("simp", ["rcl", "eq", "simplify"], env)
        stack = []
        from mp.lang.expr import execute_rpn_body
        execute_rpn_body(p.body, stack, env)
        if not stack or not isinstance(stack[-1], Symbolic):
            failed += 1
            _fail("prog body CAS")
        else:
            print("prog simp result:", stack[-1])
            passed += 1
            _ok("prog body CAS via rcl+simplify")
    except Exception as e:
        failed += 1
        _fail("prog CAS: " + str(e))

    # 5) CalcREPL .cas dot (optional but valuable on device)
    try:
        from mp.ui.calc_repl import CalcREPL
        from mp.lib.cas import HAS_CAS as _has_cas, Symbolic as _Sym
        r = CalcREPL()
        res = r.enter(".cas simplify x^2+2*x+1")
        print("repl .cas:", res)
        if res is None:
            failed += 1
            _fail("repl .cas returned None")
        elif isinstance(res, _Sym) or (_has_cas or "stub:simplify" in str(res)):
            passed += 1
            _ok("CalcREPL .cas")
        else:
            failed += 1
            _fail("repl .cas unexpected result: " + str(res))
    except Exception as e:
        failed += 1
        _fail("CalcREPL .cas: " + str(e))

    # 6) Optional eigenmath direct import (zenodante/LofiFren builds)
    try:
        import eigenmath
        print("eigenmath: present (", getattr(eigenmath, "version", "no version"), ")")
        passed += 1
        _ok("eigenmath module import")
    except ImportError:
        print("SKIP: eigenmath not importable (stub CAS is OK for Phase 7 gate)")
    except Exception as e:
        print("WARN: eigenmath:", e)

    print("---")
    print("passed:", passed, "failed:", failed)
    if failed == 0:
        print("PHASE 7 SMOKE: PASS")
        print('Host: ./tools/ralph.sh record-hardware-verification "Phase 7 CAS smoke OK on PicoCalc"')
        return True
    print("PHASE 7 SMOKE: FAIL — fix issues above before recording HW verification")
    return False


if __name__ == "__main__":
    run()