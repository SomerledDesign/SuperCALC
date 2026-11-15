# eigenmath cycles, display + VT live (Donna's failing case)
# Self-contained: mpremote run firmware/diag/diag_2_eigen.py
LOG = True
import sys
# Never import from the SD card: boot.py puts /sd and /sd/py_scripts first on sys.path,
# and a failing card makes every import probe raise OSError(EIO) from sdcard.py.
# Drop the SD entries for this run (restored at the end) so imports come from flash.
_SAVED_PATH = list(sys.path)
for _p in _SAVED_PATH:
    if _p == "/sd" or _p.startswith("/sd/"):
        sys.path.remove(_p)
for _p in ("/modules", "/lib", ""):          # flash locations first, '' at the front
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

import gc, time

def _log(msg):
    line = "%7d ms %s" % (time.ticks_ms(), msg)
    print(line)
    if LOG:
        try:
            with open("/diag_log.txt", "a") as f:
                f.write(line + "\n")
        except Exception:
            pass

# Fixed canary set: CANARY_N blocks of CANARY_K bytes (8 KB total), never more.
# Each step drops the previous set (after checking it) and gc.collect()s BEFORE the
# next big allocation, so canaries never pile up and fragment the heap (the old
# version added 16 KB per size step, 48 KB per cycle, and hit MemoryError at 112K).
CANARY_N = 8
CANARY_K = 1024
canaries = []

def _check(tag):
    for i, b in enumerate(canaries):
        if b.count(b"\xa5") != len(b):
            j = 0
            while b[j] == 0xA5:
                j += 1
            _log("CORRUPTION %s canary %d (len %d) at offset %d: %s" %
                 (tag, i, len(b), j, bytes(b[j:j + 16]).hex()))
            return False
    return True

def _release(tag):
    ok = _check(tag)
    canaries.clear()
    gc.collect()
    return ok

def _fill():
    # land a fixed set of canaries in the memory just freed
    canaries.clear()
    for i in range(CANARY_N):
        canaries.append(bytearray(b"\xa5" * CANARY_K))

def run(mode, cycles=6, idle_s=300):
    _log("start mode=%s free=%d sys.path=%r" % (mode, gc.mem_free(), sys.path))
    park = None
    if mode == "eigen_parked":
        # take the display/VT out of the picture: VT cursor timer writes into a held
        # buffer and core1 stops pushing frames
        import picocalc, vtterminal
        try:
            picocalc.terminal.wr("\x1b[?25l")
        except Exception:
            pass
        park = bytearray(len(picocalc.display.buffer))
        vtterminal.init(park)
        try:
            picocalc.display.stopRefresh()
        except Exception:
            pass
    sizes = (96 * 1024, 112 * 1024, 128 * 1024)
    for c in range(cycles):
        for n in sizes:
            tag = "cycle %d size %d" % (c, n)
            if not _release("before " + tag):   # free canaries before the big block
                return
            if mode == "no_eigen":
                b = bytearray(n)          # same heap churn, no eigenmath
                for i in range(0, n, 4096):
                    b[i] = 1
                del b
            else:
                import eigenmath
                e = eigenmath.EigenMath(n)
                for cmd in ("d(sin(x),x)", "integral(x^2,x)", "simplify(sin(x)^2+cos(x)^2)",
                            "integral(1/(1+x^2),x)", "integral(sin(x)*exp(x),x)"):
                    try:
                        e.run(cmd, True)
                    except MemoryError:
                        pass
                e.deinit()
                del e
            gc.collect()
            _fill()
            if not _check(tag):
                return
        _log("cycle %d done free=%d" % (c, gc.mem_free()))
    _log("idle phase %d s (do not touch the keyboard)" % idle_s)
    t0 = time.ticks_ms()
    k = 0
    while time.ticks_diff(time.ticks_ms(), t0) < idle_s * 1000:
        time.sleep(5)
        gc.collect()
        ok = _check("idle %d" % k)
        _log("idle t=%ds free=%d canaries=%s" % (time.ticks_diff(time.ticks_ms(), t0) // 1000,
                                                 gc.mem_free(), "ok" if ok else "BAD"))
        if not ok:
            break
        k += 1
    if park is not None:
        import picocalc, vtterminal
        vtterminal.init(picocalc.display.buffer)
        try:
            picocalc.display.recoverRefresh()
            picocalc.terminal.wr("\x1b[?25h")
        except Exception:
            pass
    _log("DONE mode=%s (board survived)" % mode)

def main(mode):
    try:
        run(mode)
    finally:
        canaries.clear()
        sys.path.clear()
        sys.path.extend(_SAVED_PATH)
        gc.collect()

main('eigen')
