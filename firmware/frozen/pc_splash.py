# PicoCalc boot splash (frozen into the SuperCalc.OG firmware since 20261115h).
#
#   import pc_splash; pc_splash.show()     # from main.py at power-up, before the menu
#
# Shows one of four amber "CRT" images, picked at random on every call, using the same
# engine as the SuperCALC launch splash (sc_splash): straight into the LofiFren
# framebuffer, pushed with picocalcdisplay.pushNow(), ~6.4 s, any PicoCalc key dismisses
# (the key and its release are swallowed), USB serial input ends it at once.
# No SuperCALC/Somerled branding: the PicoCalc is ClockworkPi's product.
# The images are frozen modules pc_splash_a..d (DATA = SCS1 bytes in XIP flash, made
# with tools/make_splash.py); /sd/splash.scs is NOT used here (that override belongs to
# the SuperCALC splash). Never raises (Ctrl-C still interrupts); any failure just skips.
#
# pc_splash.last: dict with the chosen image ("image"), why it ended ("reason") and
# sc_splash's diagnostics ("splash").

import gc

TIMEOUT_MS = 6400
IMAGES = ("pc_splash_a", "pc_splash_b", "pc_splash_c", "pc_splash_d")

last = None


def _pick(n):
    """Random index 0..n-1. os.urandom on rp2 comes from the ROSC hardware RNG, so it
    differs on every power-up (time-based seeds are nearly constant at boot)."""
    try:
        import os
        return os.urandom(1)[0] % n
    except Exception:
        pass
    try:
        import time
        return time.ticks_us() % n
    except Exception:
        return 0


def show(timeout_ms=None, image=None):
    """Show a random PicoCalc boot splash (or IMAGES[image] if image is 0..3).
    Returns why it ended ('key', 'timeout', 'usb', 'nodisplay', 'error')."""
    global last
    info = {"image": None, "reason": "error"}
    last = info
    name = None
    try:
        i = image if image is not None else _pick(len(IMAGES))
        name = IMAGES[i]
        info["image"] = name
        mod = __import__(name)
        import sc_splash
        reason = sc_splash.show(timeout_ms=TIMEOUT_MS if timeout_ms is None else timeout_ms,
                                sd=False, data=mod.DATA)
        mod = None
        info["reason"] = reason
        info["splash"] = sc_splash.last
    except Exception as e:
        info["error"] = repr(e)
    finally:
        if name:
            try:
                import sys
                sys.modules.pop(name, None)   # the image bytes stay in flash either way
            except Exception:
                pass
        gc.collect()
    return info["reason"]
