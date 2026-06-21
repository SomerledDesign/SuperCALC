"""
Phase 0 hardware smoke test — PicoCalc + Pico 2 W (LofiFren/zenodante base UF2).

Push this file plus the mp/ tree via dashboard or mpremote, then run from device REPL:

    import hw_smoke_phase0
    hw_smoke_phase0.run()

Or (if cwd is examples/):

    exec(open('hw_smoke_phase0.py').read())

On success, on the host run:

    ./tools/ralph.sh record-hardware-verification "Phase 0 smoke: dashboard+REPL+hybrid OK"

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
    """Run Phase 0 smoke checks. Returns True if all required checks pass."""
    passed = 0
    failed = 0
    print("SuperCalc.OG Phase 0 hardware smoke")
    print("---")

    # 1) Firmware / platform sanity
    try:
        impl = sys.implementation
        print("sys.implementation:", impl.name, getattr(impl, "version", ""))
        print("sys.platform:", sys.platform)
        passed += 1
    except Exception as e:
        failed += 1
        _fail("sys info: " + str(e))

    # 2) Memory (gc.mem_free on MicroPython; skip on host CPython for dev harness)
    try:
        import gc
        if not hasattr(gc, "mem_free"):
            print("SKIP: gc.mem_free unavailable (host CPython — OK for dev only)")
        else:
            free = gc.mem_free()
            alloc = gc.mem_alloc()
            print("gc mem_free:", free, "mem_alloc:", alloc)
            if free < 10000:
                failed += 1
                _fail("low free memory (<10KB)")
            else:
                passed += 1
                _ok("gc memory")
    except Exception as e:
        failed += 1
        _fail("gc: " + str(e))

    # 3) Hybrid boundary (required — push mp/ before running)
    try:
        from mp.lib import hybrid
        v = hybrid.version()
        s = hybrid.sin(0.5)
        r = hybrid.sqrt(9)
        print("hybrid.version():", v)
        print("hybrid.sin(0.5):", s)
        print("hybrid.sqrt(9):", r)
        if r != 3 and abs(r - 3) > 1e-6:
            failed += 1
            _fail("hybrid.sqrt(9) != 3")
        else:
            passed += 1
            _ok("hybrid fallback/native path")
        print("HAS_C_MATH:", hybrid.HAS_C_MATH)
    except Exception as e:
        failed += 1
        _fail("mp.lib.hybrid: " + str(e))
        print("Hint: push the mp/ directory to the device (dashboard sync).")

    # 4) Optional native C module (custom UF2 with USER_C_MODULES)
    try:
        import picocalc_math
        cv = picocalc_math.version()
        ca = picocalc_math.add(1.5, 2.5)
        print("picocalc_math.version():", cv)
        print("picocalc_math.add(1.5, 2.5):", ca)
        if ca != 4 and abs(ca - 4) > 1e-6:
            failed += 1
            _fail("picocalc_math.add mismatch")
        else:
            passed += 1
            _ok("picocalc_math C module (custom UF2)")
    except ImportError:
        print("SKIP: picocalc_math not present (stock LofiFren UF2 is OK for Phase 0 gate)")
    except Exception as e:
        failed += 1
        _fail("picocalc_math: " + str(e))

    # 5) Optional display module (base port)
    try:
        import picocalc
        print("picocalc module: present")
        passed += 1
        _ok("picocalc import")
    except ImportError:
        print("SKIP: picocalc not importable (some bases use different names)")
    except Exception as e:
        print("WARN: picocalc:", e)

    # 6) SD mount (common on PicoCalc ports)
    try:
        import os
        if "/sd" in os.listdir("/"):
            print("SD mount: /sd visible")
            passed += 1
            _ok("/sd mount")
        else:
            print("SKIP: /sd not in root list (card absent or different layout)")
    except Exception as e:
        print("SKIP: sd check:", e)

    print("---")
    print("passed:", passed, "failed:", failed)
    if failed == 0:
        print("PHASE 0 SMOKE: PASS")
        print("Host: ./tools/ralph.sh record-hardware-verification \"Phase 0 smoke OK on PicoCalc\"")
        return True
    print("PHASE 0 SMOKE: FAIL — fix issues above before recording HW verification")
    return False


if __name__ == "__main__":
    run()