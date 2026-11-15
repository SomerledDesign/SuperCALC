# picocalc-app: SuperCalc | Apps | Scientific / RPN / CAS calculator (Phase 7)
"""SuperCalc.OG launcher v2 - bc-style scrolling terminal + pixel graphing.

Keyboard-driven (picocalc.keyboard), draws straight to the 320x320 framebuffer.
Redraws only when a key arrives, so no flicker. History scrolls like bc.

Commands:
  <expr>               evaluate (infix or RPN), e.g. 2+2, sin(pi/2), 2 3 +
  plot <f> [xmin xmax] graph f(x) full screen, e.g. plot sin(x) -6.3 6.3
  hp12c / sheets       enter 12C mode (TVM, mortgage, options, ...)
  sheet <name>         jump to a 12C-mode sheet (tvm, mortgage, options, ...)
  simplify/expand/factor/d/int/solve/taylor <expr>   Eigenmath CAS
  eig <cmd>            raw Eigenmath;  cas  status + CAS help
  .s / .v              show stack / variables
  clear                clear the screen      help   this list
  ESC or quit          back to the menu
"""

import gc
import sys
import utime

COLS = 52          # 6 px font -> 53 cols on 320 px
ROWS = 31          # 10 px line pitch -> 32 rows; last row is the prompt
FG = 15
DIM = 9
RES = 12


def _park_vt():
    """Detach the VT terminal so its cursor timer stops drawing on our screen."""
    import os
    try:
        import picocalc
        import vtterminal
        try:
            os.dupterm(None)
        except Exception:
            pass
        if picocalc.terminal is not None:
            try:
                picocalc.terminal.wr("\x1b[?25l")
            except Exception:
                pass
        park = bytearray(len(picocalc.display.buffer))
        vtterminal.init(park)
        return park
    except Exception:
        return None


def _unpark_vt(park):
    import os
    try:
        import picocalc
        import vtterminal
        if park is not None:
            vtterminal.init(picocalc.display.buffer)
        if picocalc.terminal is not None:
            try:
                picocalc.terminal.wr("\x1b[?25h")
                os.dupterm(picocalc.terminal)
            except Exception:
                pass
    except Exception:
        pass


class Screen:
    """Scrollback buffer rendered bottom-up, bc style."""

    def __init__(self, d):
        self.d = d
        self.lines = []

    def add(self, text, color=FG):
        for raw in str(text).split("\n"):
            while len(raw) > COLS:
                self.lines.append((raw[:COLS], color))
                raw = "  " + raw[COLS:]
            self.lines.append((raw, color))
        if len(self.lines) > 200:
            self.lines = self.lines[-200:]

    def draw(self, prompt, buf):
        d = self.d
        d.beginDraw()
        d.fill(0)
        vis = self.lines[-(ROWS - 1):]
        y = 2
        for txt, col in vis:
            d.text(txt, 2, y, col)
            y += 10
        line = prompt + buf
        if len(line) > COLS - 1:
            line = line[-(COLS - 1):]
        d.text(line, 2, y, FG)
        cx = 2 + len(line) * 6
        d.fill_rect(cx, y, 6, 8, DIM)   # solid block cursor, no blink
        d.show()


def _getkey(kb, buf):
    """Block until one byte arrives from the keyboard."""
    while True:
        n = kb.readinto(buf) if kb else None
        if n:
            return buf[0]
        utime.sleep_ms(15)


def _fmt_num(v):
    if isinstance(v, float):
        if v != v:
            return "nan"
        if abs(v) < 1e-12:
            return "0"
        if abs(v) >= 1e10 or abs(v) < 1e-4:
            return "%.8e" % v
        s = "%.10g" % v
        return s
    return str(v)


def _plot(d, kb, expr, xmin, xmax):
    """Full-screen pixel plot of expr over [xmin, xmax]; any key returns."""
    from mp.plot import cartesian_sample
    W = H = 320
    top = 12
    ph = H - top
    pts = cartesian_sample(expr, xmin, xmax, n=W)
    ys = [p[1] for p in pts if p[1] == p[1] and abs(p[1]) < 1e12]
    if not ys:
        return "plot: no finite points"
    ymin, ymax = min(ys), max(ys)
    if ymax - ymin < 1e-9:
        ymin -= 1.0
        ymax += 1.0
    pad = (ymax - ymin) * 0.05
    ymin -= pad
    ymax += pad

    def sy(y):
        return top + int((ymax - y) / (ymax - ymin) * (ph - 1))

    def sx(x):
        return int((x - xmin) / (xmax - xmin) * (W - 1))

    d.beginDraw()
    d.fill(0)
    # axes
    if ymin <= 0 <= ymax:
        d.hline(0, sy(0), W, 5)
    if xmin <= 0 <= xmax:
        d.vline(sx(0), top, ph, 5)
    # curve
    prev = None
    for i, (x, y) in enumerate(pts):
        if y == y and abs(y) < 1e12:
            py = sy(y)
            if prev is not None and abs(py - prev) < ph:
                d.line(i - 1, prev, i, py, FG)
            else:
                d.pixel(i, py, FG)
            prev = py
        else:
            prev = None
    title = ("y=" + expr)[:30]
    d.fill_rect(0, 0, W, 11, 2)
    d.text(title, 2, 2, FG)
    d.text("x[%g,%g]" % (xmin, xmax), 190, 2, DIM)
    d.text("y %.3g..%.3g" % (ymin, ymax), 2, H - 10, DIM)
    d.text("any key", 270, H - 10, DIM)
    d.show()
    b1 = bytearray(1)
    # Drain leftover bytes (Enter sends CR+LF) and ignore keys for a moment
    t0 = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), t0) < 600:
        kb.readinto(b1)
        utime.sleep_ms(20)
    while True:
        k = _getkey(kb, b1)
        if k not in (0x0a, 0x0d) or True:
            break
    return "plotted y=%s on [%g, %g], y %.4g..%.4g" % (expr, xmin, xmax, ymin, ymax)


def _parse_plot(args):
    """'sin(x) -6 6' -> ('sin(x)', -6.0, 6.0). Range is the last two numbers if present."""
    parts = args.split()
    xmin, xmax = -10.0, 10.0
    if len(parts) >= 3:
        try:
            a, b = float(parts[-2]), float(parts[-1])
            parts = parts[:-2]
            xmin, xmax = (a, b) if a < b else (b, a)
        except ValueError:
            pass
    return " ".join(parts), xmin, xmax


HELP = (
    "SuperCalc.OG  (ESC/quit = menu)\n"
    "  2+2   sin(pi/2)   2 3 +   x=5 via: 5 'x' sto\n"
    "  plot sin(x)        plot x^2-4 -5 5\n"
    "  hp12c   12C mode (TVM, mortgage, options)\n"
    "  sheet tvm|mortgage|loan|savings|npv|dates|options\n"
    "  CAS: simplify E  expand E  factor E  d E[,x]\n"
    "       int E[,x,a,b]  solve E=F[,x]  eig  cas\n"
    "  .s stack  .v vars  clear  help\n"
    "  Up arrow / ` recalls the last line"
)


def _free_cas(cas_mod):
    """Give the CAS engine's RAM back (12C sheets, plot and other apps need it)."""
    if cas_mod is not None:
        try:
            cas_mod.release()
        except Exception:
            pass


def main():
    _cas = None
    gc.collect()
    park = _park_vt()
    try:   # SuperCALC splash (firmware 20261115g+): 6.4 s, any key dismisses, key swallowed
        import sc_splash
        sc_splash.show()
    except Exception:
        pass
    gc.collect()
    try:
        import picocalc
        d = picocalc.display
        kb = picocalc.keyboard
        if "/" not in sys.path:
            sys.path.insert(0, "/")
        if "/py_scripts" not in sys.path:
            sys.path.insert(0, "/py_scripts")
        scr = Screen(d)
        scr.add("SuperCalc.OG - loading...", DIM)
        scr.draw("", "")
        from mp.ui.calc_repl import CalcREPL
        r = CalcREPL()
        try:
            from mp.lib import cas as _cas
        except Exception:
            _cas = None
        scr.lines = []
        scr.add(HELP, DIM)
        hist = []
        buf = bytearray(1)
        chars = []
        while True:
            scr.draw("> ", "".join(chars))
            b = _getkey(kb, buf)
            if b == 0x1b:
                # ESC alone quits; ESC [ A style arrows: peek briefly
                utime.sleep_ms(20)
                n = kb.readinto(buf)
                if not n:
                    break
                if buf[0] == 0x1b:
                    break
                if buf[0] == ord("["):
                    n = kb.readinto(buf)
                    if n and buf[0] == ord("A") and hist:
                        chars = list(hist[-1])
                continue
            if b in (0xb5,) or b == ord("`"):   # PicoCalc up-arrow code / backtick
                if hist:
                    chars = list(hist[-1])
                continue
            if b in (0x08, 0x7f):
                if chars:
                    chars.pop()
                continue
            if b == 0x0a and not chars:
                continue
            if b not in (0x0d, 0x0a):
                if 32 <= b <= 126 and len(chars) < 120:
                    chars.append(chr(b))
                continue
            s = "".join(chars).strip()
            chars = []
            if not s:
                continue
            hist.append(s)
            scr.add("> " + s, FG)
            low = s.lower()
            if low in ("quit", "exit", "q", ".quit"):
                break
            if low in ("help", "?", ".help"):
                scr.add(HELP, DIM)
                continue
            if low in ("clear", ".clear", "cls"):
                scr.lines = []
                continue
            try:
                if low in ("hp12c", "12c", "sheets", "hp") or low.startswith("sheet ") or low.startswith("hp12c ") or low.startswith("12c "):
                    start = None
                    _free_cas(_cas)
                    if " " in s.strip():
                        start = s.split(None, 1)[1]
                    try:
                        import sheets as _sheets
                    except ImportError:
                        if "/py_scripts" not in sys.path:
                            sys.path.insert(0, "/py_scripts")
                        import sheets as _sheets
                    try:
                        _sheets.run(d, kb, start=start)
                    finally:
                        # drop the 12C module (~50K) so algebra has room again
                        _sheets = None
                        sys.modules.pop("sheets", None)
                        gc.collect()
                    scr.add("12C mode closed", DIM)
                elif low.startswith("plot ") or low.startswith(".plot "):
                    expr, a, z = _parse_plot(s.split(None, 1)[1])
                    _free_cas(_cas)
                    scr.add(_plot(d, kb, expr, a, z), DIM)
                elif _cas is not None and _cas.is_command(s):
                    scr.add("  ...", DIM)
                    scr.draw("", "")
                    scr.lines.pop()
                    out = _cas.command(s)
                    scr.add(out, 6 if out.startswith("!") else RES)
                elif low in (".s", ".stack"):
                    scr.add(r.show_stack(), RES)
                elif low in (".v", ".vars"):
                    scr.add(r.show_vars(), RES)
                else:
                    out = r.enter(s)
                    if out is None:
                        scr.add("ok", DIM)
                    elif isinstance(out, (int, float)):
                        scr.add(_fmt_num(out), RES)
                    else:
                        scr.add(r._fmt(out), RES)
            except Exception as e:
                scr.add("! " + str(e)[:100], 6)
            gc.collect()
    except Exception as e:
        try:
            import picocalc
            d = picocalc.display
            d.beginDraw()
            d.fill(0)
            d.text("SuperCalc ERROR", 4, 8, FG)
            d.text(str(e)[:52], 4, 24, FG)
            d.text("press ESC", 4, 44, DIM)
            d.show()
            buf = bytearray(1)
            for _ in range(400):
                n = picocalc.keyboard.readinto(buf)
                if n and buf[0] == 0x1b:
                    break
                utime.sleep_ms(25)
        except Exception:
            utime.sleep_ms(3000)
    finally:
        try:
            _free_cas(_cas)
        except Exception:
            pass
        _unpark_vt(park)
        gc.collect()


if __name__ == "__main__":
    main()
