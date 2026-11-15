# SuperCalc.OG startup splash (frozen into the firmware since 20261114f; 20261115g push fix;
# 20261115h data= for other splash images, e.g. the PicoCalc boot splash pc_splash.py).
#
#   import sc_splash; sc_splash.show()            # from main.py, before the menu
#   sc_splash.show(timeout_ms=5000, sd=False)     # options
#   sc_splash.show(data=some_module.DATA)          # another SCS1 image (no SD override)
#
# Draws a 320x320 16-colour SCS1 image (see tools/make_splash.py for the format)
# straight into the LofiFren display framebuffer: the zlib stream is inflated row-chunk
# by row-chunk into picocalc.display.buffer, so there is no second framebuffer. The
# built-in image is frozen bytes in XIP flash, read through a zero-copy io.BytesIO.
# Extra RAM while showing: a ~1 KB inflate window plus a few small objects.
#
# /sd/splash.scs (SCS1, raw or zlib) replaces the built-in image when the SD card is
# mounted. Anything wrong with it (no card, CMD0 failure, read error, bad header, bad
# data) silently falls back to the built-in image.
#
# Dismiss: any PicoCalc key (the key press, and its release, are swallowed so they do
# not reach the menu/REPL) or timeout_ms. USB serial input (mpremote, a terminal)
# ends it at once without consuming anything. Ctrl-C over USB still interrupts.
# The VT terminal is detached while the splash is up (its cursor timer would draw on
# it) and re-attached afterwards; os.dupterm is never touched.
#
# 20261115g: frames are pushed with picocalcdisplay.pushNow() when the firmware has it:
# a synchronous push from core 0 that leaves core 1 auto-refresh running (core 1 is
# never stopped or reset). At cold boot the core 1 refresh alone did not get the splash
# onto the LCD. Older firmware falls back to display.show(). show() always ends with
# auto-refresh running (skipUpdate cleared), so the menu and the VT terminal draw
# normally afterwards. last["push"] / last["push_end"] record whether pushNow pushed,
# last["c1_frames"] how many frames core 1 pushed while the splash was up.

import gc
import io
import struct
import time

TIMEOUT_MS = 6400            # Kevin 2026-11-15: ~6.4 s; any key dismisses
SD_PATH = "/sd/splash.scs"

_W = 320
_H = 320
_ROW = 160                 # bytes per row, 4 bpp
_CHUNK = 8 * _ROW          # inflate 8 rows per readinto
_WBITS = 10
# LofiFren picocalcdisplay default LUT entries 0-15 (byte-swapped RGB565), restored after.
_DEFAULT_LUT = struct.pack("<16H", 0x0000, 0x0080, 0x0004, 0x0084, 0x1000, 0x1080, 0x1004, 0x18C6,
                           0x1084, 0x00F8, 0xE007, 0xE0FF, 0x1F00, 0x1FF8, 0xFF07, 0xFFFF)

last = None                # diagnostics: dict filled by show()


def _header(f):
    h = f.read(12)
    if len(h) != 12 or h[:4] != b"SCS1":
        raise ValueError("splash: bad magic")
    w, hh, bpp, enc, n, _r = struct.unpack("<HHBBBB", h[4:])
    if w != _W or hh != _H or bpp != 4 or enc > 1 or not 1 <= n <= 16:
        raise ValueError("splash: unsupported header")
    pal = f.read(2 * n)
    if len(pal) != 2 * n:
        raise ValueError("splash: short palette")
    return enc, pal


def _draw(f, fb):
    """Decode an SCS1 stream into fb (a 51200-byte buffer). Returns the palette bytes."""
    enc, pal = _header(f)
    mv = memoryview(fb)
    if enc == 1:
        import deflate
        pos = f.tell()
        cmf = f.read(1)
        if not cmf or (cmf[0] & 15) != 8 or (cmf[0] >> 4) + 8 > _WBITS:
            raise ValueError("splash: zlib window too large")
        f.seek(pos)
        d = deflate.DeflateIO(f, deflate.ZLIB, _WBITS)
    else:
        d = f
    off = 0
    total = _ROW * _H
    while off < total:
        n = d.readinto(mv[off:off + _CHUNK])
        if not n:
            raise ValueError("splash: short pixel data")
        off += n
    if enc == 1:
        if d.read(1):                # also makes uzlib check the zlib checksum
            raise ValueError("splash: trailing pixel data")
    return pal


def _builtin():
    import sc_splash_data
    return io.BytesIO(sc_splash_data.DATA)     # zero-copy view of the frozen bytes


def _usb_waiting(poller):
    try:
        return bool(poller and poller.poll(0))
    except Exception:
        return False


def _key_event(kb):
    """Return the next raw keyboard FIFO event (state, key) or None. Never raises."""
    try:
        if kb.keyCount():
            e = kb.keyEvent()
            if e:
                return e[0], e[1]
    except Exception:
        pass
    return None


def _swallow(kb, ms=600):
    """Eat the dismissing key's remaining events until its release (bounded)."""
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < ms:
        e = _key_event(kb)
        if e and e[0] == 3:          # _StateRelease: the dismissing key is fully eaten
            return
        time.sleep_ms(10)


def _push(d, info, key):
    """Push the framebuffer now (pushNow, core 0) or fall back to d.show(). Never raises
    for pushNow problems; afterwards auto-refresh is running again."""
    try:
        import picocalcdisplay
        f = getattr(picocalcdisplay, "pushNow", None)
        if f is not None:
            ok = bool(f())
            info[key] = ok
            if ok:
                return
    except Exception as e:
        info[key + "_error"] = repr(e)
    d.show()                         # update(): clears skipUpdate (auto) or pushes (manual)


def _frames():
    try:
        import picocalcdisplay
        f = getattr(picocalcdisplay, "frames", None)
        return f() if f is not None else None
    except Exception:
        return None


def show(timeout_ms=None, sd=True, sd_path=None, display=None, keyboard=None, data=None):
    """Show the splash. Returns why it ended: 'key', 'timeout', 'usb', 'nodisplay' or 'error'.

    data: SCS1 bytes (e.g. a frozen module's DATA) to show instead of the built-in
    SuperCALC image; the /sd override is not used then. Default None: unchanged."""
    global last
    import picocalc
    import picocalcdisplay
    if timeout_ms is None:
        timeout_ms = TIMEOUT_MS
    d = display if display is not None else picocalc.display
    kb = keyboard if keyboard is not None else picocalc.keyboard
    info = {"source": None, "reason": None, "free_before": gc.mem_free()}
    last = info
    if d is None or len(d.buffer) != _ROW * _H:
        info["reason"] = "nodisplay"
        return "nodisplay"
    poller = None
    try:
        import select
        import sys
        poller = select.poll()
        poller.register(sys.stdin, select.POLLIN)
    except Exception:
        poller = None
    if _usb_waiting(poller):
        info["reason"] = "usb"
        return "usb"

    vt_detached = False
    lut_set = False
    reason = "error"
    try:
        try:
            import vtterminal
            if picocalc.terminal is not None and hasattr(vtterminal, "deinit"):
                vtterminal.deinit()
                vt_detached = True
        except Exception:
            pass
        d.beginDraw()
        pal = None
        if data is not None:
            pal = _draw(io.BytesIO(data), d.buffer)
            info["source"] = "data"
        elif sd and getattr(picocalc, "sd", None):
            f = None
            try:
                f = open(sd_path or SD_PATH, "rb")
                pal = _draw(f, d.buffer)
                info["source"] = "sd"
            except Exception as e:      # missing file, EIO, garbage: use the built-in image
                info["sd_error"] = repr(e)
                pal = None
            finally:
                if f:
                    try:
                        f.close()
                    except Exception:
                        pass
        if pal is None:
            pal = _draw(_builtin(), d.buffer)
            info["source"] = "builtin"
        info["free_during"] = gc.mem_free()
        picocalcdisplay.setLUT(pal)
        lut_set = True
        _push(d, info, "push")
        f0 = _frames()

        # wait for a key, USB input or the timeout
        t0 = time.ticks_ms()
        reason = "timeout"
        while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
            if _usb_waiting(poller):
                reason = "usb"
                break
            e = _key_event(kb) if kb is not None else None
            if e:
                if e[0] in (1, 2):           # press / long press: dismiss, swallow the rest
                    _swallow(kb)
                    reason = "key"
                    break
                continue                     # stray release from before the splash
            time.sleep_ms(20)
        f1 = _frames()
        if f0 is not None and f1 is not None:
            info["c1_frames"] = (f1 - f0) & 0x3FFFFFFF
        return reason
    except Exception as e:
        info["error"] = repr(e)
        reason = "error"
        return reason
    finally:
        info["reason"] = reason
        try:
            d.beginDraw()
            d.fill(0)
            if lut_set:
                picocalcdisplay.setLUT(_DEFAULT_LUT)
            if vt_detached:
                import vtterminal
                vtterminal.init(d.buffer)
            _push(d, info, "push_end")
        except Exception:
            try:
                d.show()             # whatever failed above, never leave refresh held off
            except Exception:
                pass
        gc.collect()
        info["free_after"] = gc.mem_free()
