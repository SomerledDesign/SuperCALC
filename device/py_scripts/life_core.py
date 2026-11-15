# picocalc-hide
# (library for life.py; hidden from the menu, imported via sys.path /py_scripts)
"""
@file    life_core.py
@brief   Conway's Game of Life screensaver for the PicoCalc.

@details
  An 80 x 80 toroidal (wrap-around) Life board drawn as 4 x 4 px cells
  (3 x 3 lit, 1 px gutter) over the full 320 x 320 GS4 display.

  - Random seed at 25-35 % density from os.urandom (urandom fallback).
  - Age shading: newborn cells are brightest and fade as they survive.
  - Stall detection: reseeds when the board is empty, frozen (still life),
    or in a short cycle (period <= RING_LEN, via a ring of grid hashes),
    and after MAX_GENS generations so it never gets boring.  A stalled
    board stays up for LINGER_MS of wall-clock time (fix2: this used to be
    36 frames, which a slow frame rate could stretch to many seconds).
  - Reseed is viper (LCG fill + hash) seeded from 5 urandom bytes, so it
    makes no bignum garbage on the device's 31-bit small ints.
  - A frame slower than SLOW_MS shows "!<ms><phase>" in the status line.
  - Any key exits (the key is swallowed so the menu does not see it).

  Drawing: each frame is painted straight into picocalc.display.buffer
  between beginDraw() and show(), after an 8 ms pause so any in-flight
  Core 1 scan finishes (the tetris.py timing, minus the copy).  Every
  byte of the screen is rewritten each frame, so nothing needs clearing.
  stopRefresh()/recoverRefresh() are never used.  Keys are read from
  picocalc.keyboard (never the VT terminal).

  VT: detached with vtterminal.deinit() (SuperCalc firmware g/h, as
  sc_splash does), so no 51,200 B park buffer is needed; on older firmware
  it falls back to a park buffer, or just hides the cursor.  On exit the
  VT is re-attached to the live buffer and the cursor and dupterm restored.

  RAM: two 6,400 B generations + ~1.5 KB of small tables (~14 KB total).
  No 51 KB contiguous block is needed, so a fragmented heap is fine.
  Set USE_BACK_BUFFER = True to also try an offscreen buffer (+51,200 B);
  if that allocation fails it silently falls back to direct drawing.
  Every allocation runs gc.collect() first and retries once after another
  collect; if the grids still cannot be had, a message is shown and the
  app returns to the menu.

  The hot loops use @micropython.viper; a pure-Python fallback is used when
  the micropython module is missing (CPython unit tests).

  Launch: the menu runs the tiny life.py, which imports this module.  An
  import streams the source through the lexer instead of py_run's
  f.read() of the whole file, so no ~20 KB contiguous string is needed
  and nothing is held while the screensaver runs.

Colour (firmware g/h): GS4 levels 0-15 become RGB565 through Core 1's
  16-entry LUT (picocalcdisplay.setLUT).  Each new seed picks a base hue
  (or the classic VT colours) and loads a 16-level ramp: newborn cells are
  brightest and pale, older cells fade to a deeper floor of the same hue.
  The LUT is shared with the VT and the menu, so the firmware default
  is put back on every exit path (key, error, Ctrl-C).  Without setLUT the
  classic look is kept and nothing is changed.

Controls: any key exits.
"""

import gc

try:
    import micropython
    from micropython import const
    _MP = True
except ImportError:          # CPython (unit tests)
    micropython = None
    _MP = False

    def const(x):
        return x

try:
    from array import array
except ImportError:          # pragma: no cover
    from uarray import array

## @name Board geometry
## @{
GRID_W = const(80)           ##< cells across
GRID_H = const(80)           ##< cells down
CELL = const(4)              ##< pixels per cell edge (320 / 80)
## @}

## @name Behaviour tuning
## @{
RING_LEN = const(6)          ##< detect cycles with period <= 6
MAX_GENS = const(1500)       ##< forced reseed after this many generations
LINGER_MS = const(1400)      ##< wall-clock time a stalled board stays up
LINGER_EMPTY_MS = const(300) ##< wall-clock time an empty board stays up
SLOW_MS = const(1000)        ##< frames slower than this are flagged "!" in status
GC_EVERY = const(1024)       ##< frames between routine gc.collect() calls
FRAME_MS = const(40)         ##< target frame period (~25 fps)
DENSITY_LO = const(64)       ##< 25 % of 256
DENSITY_HI = const(90)       ##< 35 % of 256
STATUS_COLOR = const(4)      ##< dim grey for the gen/pop text
USE_BACK_BUFFER = False      ##< True = also try a 51 KB offscreen buffer
COLOR_PER_SEED = True        ##< new base colour with every new seed
## @}

## @name Colour (picocalcdisplay LUT)
## @{
LUT_SETTLE_MS = const(80)    ##< > one Core 1 push (320*320*2 B @ 25 MHz = 65.5 ms)
RAMP_FLOOR = const(6)        ##< LUT index of the oldest cells (newborn = 15)
STATUS_GREY = const(150)     ##< status-text grey (0-255) in hue palettes
## Firmware default LUT[0..15] (picocalcdisplay.c, also sc_splash): VT colours,
## stored byte-swapped RGB565, little-endian.
_DEFAULT_LUT16 = (0x0000, 0x0080, 0x0004, 0x0084, 0x1000, 0x1080, 0x1004, 0x18C6,
                  0x1084, 0x00F8, 0xE007, 0xE0FF, 0x1F00, 0x1FF8, 0xFF07, 0xFFFF)
## Base hues (degrees): red, orange, amber, gold, lime, green, teal, cyan,
## azure, violet, magenta, rose.  CLASSIC (-1) = the default VT colours.
HUES = (0, 20, 35, 48, 85, 120, 165, 185, 210, 270, 300, 330, -1)
CLASSIC = const(-1)
## @}

## @name step() result codes
## @{
ST_OK = const(0)
ST_EMPTY = const(1)
ST_STILL = const(2)
ST_CYCLE = const(3)
ST_MAXGEN = const(4)
## @}

REASON_TEXT = ("", "empty", "still", "cycle", "max gen")


def _shade(age):
    """@brief GS4 grey level for a cell of the given age (0 = dead).
    @details Newborn = 15, then fades by 2 per generation down to 5."""
    if age == 0:
        return 0
    s = 17 - 2 * age
    return s if s > 5 else 5


def _shade_ramp(age):
    """@brief LUT index for a hue palette: newborn 15, -1 per gen, floor 6."""
    if age == 0:
        return 0
    s = 16 - age
    return s if s > RAMP_FLOOR else RAMP_FLOOR


def _lut_bytes(vals):
    """@brief 16 stored LUT words -> 32 bytes for setLUT (little-endian)."""
    b = bytearray(32)
    for i in range(16):
        b[2 * i] = vals[i] & 0xFF
        b[2 * i + 1] = vals[i] >> 8
    return b


DEFAULT_LUT = bytes(_lut_bytes(_DEFAULT_LUT16))   ##< restore image (32 B)


def _hsv(h, s, v):
    """@brief Integer HSV -> RGB.  h 0-359, s/v 0-255; returns (r, g, b)."""
    if s == 0:
        return v, v, v
    region = h // 60
    rem = (h % 60) * 255 // 60
    p = v * (255 - s) // 255
    q = v * (255 - (s * rem) // 255) // 255
    t = v * (255 - (s * (255 - rem)) // 255) // 255
    if region == 0:
        return v, t, p
    if region == 1:
        return q, v, p
    if region == 2:
        return p, v, t
    if region == 3:
        return p, q, v
    if region == 4:
        return t, p, v
    return v, p, q


def _rgb565_stored(r, g, b):
    """@brief RGB -> RGB565 as the firmware stores it (byte-swapped)."""
    c = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)


def _put(out, i, w):
    out[2 * i] = w & 0xFF
    out[2 * i + 1] = w >> 8


def ramp_palette(hue, out=None):
    """@brief 16-entry LUT (32 bytes) for one base hue.
    @details 0 = black (dead), 4 = neutral grey (status text, readable on
             any hue), 15..6 = cells by age: newborn brightest and pale
             (s ~35 %), saturating by age 4, value fading to a floor that
             is raised for dark hues (blue/violet) so old cells never go
             near-black.  1-3 and 5 are unused and set to the floor colour.
             CLASSIC returns the firmware default."""
    if out is None:
        out = bytearray(32)
    if hue == CLASSIC:
        out[:] = DEFAULT_LUT
        return out
    r, g, b = _hsv(hue, 255, 255)
    lum = (2 * r + 5 * g + b) >> 3
    vf = 120 if lum >= 100 else 175
    for k in range(10):                      # index 15 - k
        v = 255 - k * (255 - vf) // 9
        sat = 90 + (k if k < 3 else 3) * 55
        r, g, b = _hsv(hue, sat, v)
        _put(out, 15 - k, _rgb565_stored(r, g, b))
    fl = out[2 * RAMP_FLOOR] | (out[2 * RAMP_FLOOR + 1] << 8)
    for i in (1, 2, 3, 5):
        _put(out, i, fl)
    _put(out, 0, 0)
    _put(out, STATUS_COLOR, _rgb565_stored(STATUS_GREY, STATUS_GREY, STATUS_GREY))
    return out


## True once this module has changed the LUT and not yet put it back.
_lut_dirty = False


def _set_lut(pcd, buf):
    """@brief Load a palette (marks the LUT dirty first, so a failure
    half-way still gets restored)."""
    global _lut_dirty
    _lut_dirty = True
    pcd.setLUT(buf)


def lut_dirty():
    return _lut_dirty


def restore_lut():
    """@brief Put the firmware default LUT back if we changed it.
    @return True if a restore was done.  Safe to call any number of times."""
    global _lut_dirty
    if not _lut_dirty:
        return False
    try:
        import picocalcdisplay
        picocalcdisplay.setLUT(DEFAULT_LUT)
        _lut_dirty = False
        return True
    except Exception:
        return False


def make_luts(shade=None):
    """@brief Build the age -> packed-byte lookup tables.
    @return (lut_full, lut_left): 256-byte tables.  lut_full packs the grey
            into both nibbles (2 lit pixels); lut_left only into the high
            nibble (GS4_HMSB: high nibble = left pixel), so the 4th pixel
            column of each cell is the dark gutter."""
    if shade is None:
        shade = _shade
    full = bytearray(256)
    left = bytearray(256)
    for a in range(256):
        s = shade(a)
        full[a] = (s << 4) | s
        left[a] = s << 4
    return full, left


# ---------------------------------------------------------------------------
# Hot loops: viper on MicroPython, plain Python elsewhere.  Both versions
# implement exactly the same arithmetic (hash uses only the low 30 bits, so
# it matches regardless of native word width).
# ---------------------------------------------------------------------------
if _MP:
    @micropython.viper
    def life_step(src: ptr8, dst: ptr8, out: ptr32, w: int, h: int):
        """@brief One B3/S23 generation from src into dst (torus).
        @param src  current ages (0 dead, 1..255 alive age), w*h bytes
        @param dst  next generation, written completely
        @param out  int32[3] <- population, 30-bit hash, state changes"""
        pop = 0
        hsh = 0
        chg = 0
        y = 0
        while y < h:
            yu = (y - 1) if y > 0 else (h - 1)
            yd = (y + 1) if y < h - 1 else 0
            ru = yu * w
            rc = y * w
            rd = yd * w
            x = 0
            while x < w:
                xl = (x - 1) if x > 0 else (w - 1)
                xr = (x + 1) if x < w - 1 else 0
                n = 0
                if src[ru + xl]:
                    n += 1
                if src[ru + x]:
                    n += 1
                if src[ru + xr]:
                    n += 1
                if src[rc + xl]:
                    n += 1
                if src[rc + xr]:
                    n += 1
                if src[rd + xl]:
                    n += 1
                if src[rd + x]:
                    n += 1
                if src[rd + xr]:
                    n += 1
                c = rc + x
                a = src[c]
                v = 0
                if a:
                    if n == 2 or n == 3:
                        v = a + 1 if a < 255 else 255
                    else:
                        chg += 1
                elif n == 3:
                    v = 1
                    chg += 1
                dst[c] = v
                if v:
                    pop += 1
                    hsh = (hsh * 31 + c + 1) & 0x3FFFFFFF
                x += 1
            y += 1
        out[0] = pop
        out[1] = hsh
        out[2] = chg

    @micropython.viper
    def life_render(g: ptr8, fb: ptr8, lf: ptr8, ll: ptr8,
                    w: int, h: int, stride: int):
        """@brief Paint the grid into a GS4_HMSB buffer, 4x4 px per cell.
        @details Rows 0-2 of each cell get lut_full|lut_left bytes, row 3 is
                 the dark gutter.  Every byte of the w*4 x h*4 area is
                 written, so no clear is needed."""
        y = 0
        while y < h:
            row = y * w
            base = y * 4 * stride
            x = 0
            while x < w:
                a = g[row + x]
                b0 = lf[a]
                b1 = ll[a]
                p = base + x * 2
                fb[p] = b0
                fb[p + 1] = b1
                p += stride
                fb[p] = b0
                fb[p + 1] = b1
                p += stride
                fb[p] = b0
                fb[p + 1] = b1
                p += stride
                fb[p] = 0
                fb[p + 1] = 0
                x += 1
            y += 1
else:
    def life_step(src, dst, out, w, h):
        """@brief Pure-Python twin of the viper life_step()."""
        pop = 0
        hsh = 0
        chg = 0
        for y in range(h):
            ru = ((y - 1) % h) * w
            rc = y * w
            rd = ((y + 1) % h) * w
            for x in range(w):
                xl = (x - 1) % w
                xr = (x + 1) % w
                n = ((src[ru + xl] != 0) + (src[ru + x] != 0) +
                     (src[ru + xr] != 0) + (src[rc + xl] != 0) +
                     (src[rc + xr] != 0) + (src[rd + xl] != 0) +
                     (src[rd + x] != 0) + (src[rd + xr] != 0))
                c = rc + x
                a = src[c]
                v = 0
                if a:
                    if n == 2 or n == 3:
                        v = a + 1 if a < 255 else 255
                    else:
                        chg += 1
                elif n == 3:
                    v = 1
                    chg += 1
                dst[c] = v
                if v:
                    pop += 1
                    hsh = (hsh * 31 + c + 1) & 0x3FFFFFFF
        out[0] = pop
        out[1] = hsh
        out[2] = chg

    def life_render(g, fb, lf, ll, w, h, stride):
        """@brief Pure-Python twin of the viper life_render()."""
        for y in range(h):
            row = y * w
            base = y * 4 * stride
            for x in range(w):
                a = g[row + x]
                b0 = lf[a]
                b1 = ll[a]
                p = base + x * 2
                for r in range(3):
                    fb[p] = b0
                    fb[p + 1] = b1
                    p += stride
                fb[p] = 0
                fb[p + 1] = 0


if _MP:
    @micropython.viper
    def life_seed(dst: ptr8, n: int, x: int, density: int) -> int:
        """@brief Fill n cells from a 30-bit LCG; returns the next LCG state.
        @details x = (x * 69069 + 1) mod 2**30; bits 16..23 are compared
                 with density (out of 256).  Only the low 30 bits are kept, so
                 the sequence is identical on 32- and 64-bit ports."""
        i = 0
        while i < n:
            x = (x * 69069 + 1) & 0x3FFFFFFF
            dst[i] = 1 if ((x >> 16) & 0xFF) < density else 0
            i += 1
        return x

    @micropython.viper
    def life_hash(src: ptr8, n: int, out: ptr32):
        """@brief out[0] = population, out[1] = hash (same formula as life_step)."""
        pop = 0
        hsh = 0
        i = 0
        while i < n:
            if src[i]:
                pop += 1
                hsh = (hsh * 31 + i + 1) & 0x3FFFFFFF
            i += 1
        out[0] = pop
        out[1] = hsh
else:
    def life_seed(dst, n, x, density):
        """@brief Pure-Python twin of the viper life_seed()."""
        for i in range(n):
            x = (x * 69069 + 1) & 0x3FFFFFFF
            dst[i] = 1 if ((x >> 16) & 0xFF) < density else 0
        return x

    def life_hash(src, n, out):
        """@brief Pure-Python twin of the viper life_hash()."""
        pop = 0
        hsh = 0
        for i in range(n):
            if src[i]:
                pop += 1
                hsh = (hsh * 31 + i + 1) & 0x3FFFFFFF
        out[0] = pop
        out[1] = hsh


def _random_bytes(n):
    """@brief n random bytes: os.urandom, else urandom/random fallback."""
    try:
        import os
        return os.urandom(n)
    except Exception:
        pass
    try:
        import urandom as _r
    except ImportError:
        import random as _r
    return bytes(_r.getrandbits(8) for _ in range(n))


class LifeEngine:
    """@brief Display-independent Life board with stall detection.

    @details Holds two generations as bytearrays (cell = age byte) and a
             small ring of (hash, population) pairs for the last RING_LEN
             generations.  step() advances one generation and reports why
             the board should be reseeded, if it should."""

    def __init__(self, w=GRID_W, h=GRID_H, alloc=bytearray):
        self.w = w
        self.h = h
        self.cur = alloc(w * h)          ##< generation being shown
        self.nxt = alloc(w * h)          ##< scratch for the next one
        self.stats = array('i', [0, 0, 0])   ##< pop, hash, changes
        self.ring_h = array('i', [-1] * RING_LEN)
        self.ring_p = array('i', [-1] * RING_LEN)
        self.ring_i = 0
        self.gen = 0
        self.pop = 0
        self.max_gens = MAX_GENS
        self.rng = 0                     ##< LCG state for seed()

    def clear(self):
        """@brief Empty the board and reset gen counter + history."""
        c = self.cur
        for i in range(len(c)):
            c[i] = 0
        self._reset_history()

    def _reset_history(self):
        for i in range(RING_LEN):
            self.ring_h[i] = -1
            self.ring_p[i] = -1
        self.ring_i = 0
        self.gen = 0
        # Record generation 0 in the ring so a period-p cycle is caught at
        # generation p.  Viper, so no bignum garbage on 31-bit small ints.
        life_hash(self.cur, self.w * self.h, self.stats)
        self.pop = self.stats[0]
        self.ring_h[0] = self.stats[1]
        self.ring_p[0] = self.stats[0]
        self.ring_i = 1 % RING_LEN

    def set_cells(self, cells):
        """@brief Clear, then set (x, y) cells alive (age 1). Test helper."""
        self.clear()
        for x, y in cells:
            self.cur[(y % self.h) * self.w + (x % self.w)] = 1
        self._reset_history()

    def alive_set(self):
        """@brief Set of alive (x, y). Test helper (allocates)."""
        w = self.w
        return {(i % w, i // w) for i, v in enumerate(self.cur) if v}

    def seed(self, density=None):
        """@brief Random fill: 5 bytes of real entropy, then a viper LCG.
        @details One short os.urandom() call per board (no per-row
                 allocations, no Python per-cell loop); ~1 ms of work.
        @param density threshold out of 256 (default: random 25-35 %)."""
        rnd = _random_bytes(5)
        if density is None:
            density = DENSITY_LO + (rnd[0] % (DENSITY_HI - DENSITY_LO + 1))
        x = ((rnd[1] << 21) ^ (rnd[2] << 13) ^ (rnd[3] << 5) ^ rnd[4] ^ self.rng)
        self.rng = life_seed(self.cur, self.w * self.h, x & 0x3FFFFFFF, density)
        self._reset_history()
        return density

    def step(self):
        """@brief Advance one generation.
        @return ST_OK, or ST_EMPTY / ST_STILL / ST_CYCLE / ST_MAXGEN when the
                caller should reseed."""
        life_step(self.cur, self.nxt, self.stats, self.w, self.h)
        self.cur, self.nxt = self.nxt, self.cur
        self.gen += 1
        pop = self.stats[0]
        hsh = self.stats[1]
        self.pop = pop
        if pop == 0:
            return ST_EMPTY
        if self.stats[2] == 0:
            return ST_STILL
        rh = self.ring_h
        rp = self.ring_p
        for i in range(RING_LEN):
            if rh[i] == hsh and rp[i] == pop:
                return ST_CYCLE
        j = self.ring_i
        rh[j] = hsh
        rp[j] = pop
        self.ring_i = (j + 1) % RING_LEN
        if self.gen >= self.max_gens:
            return ST_MAXGEN
        return ST_OK


# ---------------------------------------------------------------------------
# Device front end
# ---------------------------------------------------------------------------
def _collect():
    """@brief Two gc passes: the second frees what the first's finalisers released."""
    gc.collect()
    gc.collect()


def alloc(n):
    """@brief bytearray(n) with gc first and one retry after another gc.
    @exception MemoryError if the heap has no free run of n bytes."""
    _collect()
    try:
        return bytearray(n)
    except MemoryError:
        _collect()
        return bytearray(n)


def largest_block(hi=65536):
    """@brief Largest single bytearray the heap can give right now (B).
    @details Binary search; only used for the out-of-memory message."""
    lo = 0
    while hi - lo > 256:
        mid = (lo + hi) // 2
        try:
            b = bytearray(mid)
            b = None
            lo = mid
        except MemoryError:
            hi = mid
    gc.collect()
    return lo


def _drain(kb, buf, quiet_ms=120):
    """@brief Swallow keys until the keyboard is quiet for quiet_ms."""
    import utime
    t = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), t) < quiet_ms:
        try:
            if kb.readinto(buf):
                t = utime.ticks_ms()
        except Exception:
            return
        utime.sleep_ms(10)


def _show_message(lines, wait_ms=4000):
    """@brief Draw text on the live display; wait for a key or timeout."""
    import picocalc
    import utime
    d = picocalc.display
    d.beginDraw()
    utime.sleep_ms(8)
    d.fill(0)
    y = 140
    for s in lines:
        d.text(s, 8, y, 15)
        y += 12
    d.show()
    kb = picocalc.keyboard
    buf = bytearray(10)
    t = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), t) < wait_ms:
        try:
            if kb and kb.readinto(buf):
                break
        except Exception:
            break
        utime.sleep_ms(20)
    if kb:
        _drain(kb, buf)


class LifeSaver:
    """@brief Runs a LifeEngine on picocalc.display until a key is hit.

    @details Allocation order: optional back buffer first (largest), then
             the two 6.4 KB generations, then the small tables.  Only the
             generations are mandatory."""

    def __init__(self, use_back=None):
        import picocalc
        self.pc = picocalc
        self.display = picocalc.display
        self.kb = picocalc.keyboard
        self.stride = self.display.width // 2
        self.back = None            ##< offscreen buffer, or None = direct
        self.fb = self.display      ##< FrameBuffer that status text goes to
        if use_back is None:
            use_back = USE_BACK_BUFFER
        if use_back:
            try:
                self.back = alloc(len(self.display.buffer))
                import framebuf
                self.fb = framebuf.FrameBuffer(self.back, self.display.width,
                                               self.display.height,
                                               framebuf.GS4_HMSB)
            except MemoryError:
                self.back = None    # fragmented heap: draw direct instead
                self.fb = self.display
        self.engine = LifeEngine(alloc=alloc)       # may raise MemoryError
        self.key_buf = bytearray(10)
        self.luts_classic = make_luts()
        self.lut_full, self.lut_left = self.luts_classic
        self.luts_ramp = None
        self.pcd = None             ##< picocalcdisplay if it has setLUT
        self.hue = CLASSIC          ##< current base hue (CLASSIC = VT colours)
        self.hue_idx = -1
        self.lut_pending = False    ##< new palette waits for the next frame
        self.lut_sets = 0           ##< palettes loaded (diagnostics/tests)
        self.pal_buf = None
        if COLOR_PER_SEED:
            try:
                import picocalcdisplay
                if hasattr(picocalcdisplay, "setLUT"):
                    self.pcd = picocalcdisplay
            except ImportError:
                pass
        if self.pcd is not None:
            self.luts_ramp = make_luts(_shade_ramp)
            self.pal_buf = bytearray(32)
        self.status = ""
        self.slow_ms = SLOW_MS      ##< slowest frame seen (ms), > SLOW_MS
        self.slow_phase = ""        ##< which phase it spent its time in
        self.fps = 0                ##< measured frames per second
        self.vt_mode = None         ##< None, "deinit", "park" or "hidden"
        self.vt_park = None
        self.old_dup = None

    # -- VT: detach while running, re-attach on exit ----------------------
    def _park_vt(self):
        import os
        try:
            self.old_dup = os.dupterm(None)
        except Exception:
            pass
        try:
            import vtterminal
        except ImportError:
            return
        term = self.pc.terminal
        if term is not None:
            try:
                term.wr("\x1b[?25l")                 # cursor off
            except Exception:
                pass
        try:
            if hasattr(vtterminal, "deinit"):        # firmware g/h: no buffer
                vtterminal.deinit()
                self.vt_mode = "deinit"
                return
            park = self.back
            if park is None:
                try:
                    park = alloc(len(self.display.buffer))
                except MemoryError:
                    park = None
            if park is not None:
                self.vt_park = park
                vtterminal.init(park)
                self.vt_mode = "park"
            else:
                self.vt_mode = "hidden"              # cursor off is all we can do
        except Exception:
            self.vt_mode = "hidden"

    def _restore_vt(self):
        import os
        try:
            if self.vt_mode is not None:
                import vtterminal
                if self.vt_mode in ("deinit", "park"):
                    vtterminal.init(self.display.buffer)
                if self.pc.terminal is not None:
                    try:
                        self.pc.terminal.wr("\x1b[?25h")  # cursor on
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            if self.old_dup is not None:
                os.dupterm(self.old_dup)
            elif self.pc.terminal is not None:
                os.dupterm(self.pc.terminal)
        except Exception:
            pass
        self.vt_mode = None
        self.vt_park = None

    # -- frame ------------------------------------------------------------
    def _draw(self, note):
        import utime
        e = self.engine
        if (e.gen & 7) == 0 or note or not self.status:
            if self.slow_phase:
                self.status = "G%d P%d F%d %s !%d%s" % (
                    e.gen, e.pop, self.fps, note, self.slow_ms, self.slow_phase)
            else:
                self.status = "G%d P%d F%d %s" % (e.gen, e.pop, self.fps, note)
        live = self.display
        target = self.back
        if target is None:
            live.beginDraw()
            self._settle(utime)     # let an in-flight Core 1 scan finish
            target = live.buffer
        life_render(e.cur, target, self.lut_full, self.lut_left,
                    e.w, e.h, self.stride)
        fb = self.fb
        fb.fill_rect(0, 311, len(self.status) * 8 + 2, 9, 0)
        fb.text(self.status, 1, 312, STATUS_COLOR)
        if self.back is not None:
            live.beginDraw()
            self._settle(utime)
            live.buffer[:] = self.back
        live.show()

    def _settle(self, utime):
        """@brief Called right after beginDraw().  Normal frames wait 8 ms.
        @details A pending palette waits LUT_SETTLE_MS (longer than one full
                 Core 1 push) so no push is still reading the LUT, then loads
                 it before the new board is written: the first frame shown
                 with the new colours is the new board, never a torn mix."""
        if self.lut_pending:
            utime.sleep_ms(LUT_SETTLE_MS)
            self.lut_pending = False
            try:
                _set_lut(self.pcd, self.pal_buf)
                self.lut_sets += 1
            except Exception:
                pass
        else:
            utime.sleep_ms(8)

    def _pick_palette(self):
        """@brief Choose the next base hue (never the same one twice running)
        and prepare its LUT and age tables.  Loaded by the next _draw()."""
        n = len(HUES)
        r = _random_bytes(1)[0]
        if self.hue_idx < 0:
            i = r % n
        else:
            i = r % (n - 1)
            if i >= self.hue_idx:
                i += 1              # skip the current one
        self.hue_idx = i
        self.hue = HUES[i]
        ramp_palette(self.hue, self.pal_buf)
        if self.hue == CLASSIC:
            self.lut_full, self.lut_left = self.luts_classic
        else:
            self.lut_full, self.lut_left = self.luts_ramp
        self.lut_pending = True

    def _key_hit(self):
        kb = self.kb
        if not kb:
            return False
        try:
            return bool(kb.readinto(self.key_buf))
        except Exception:
            return False

    def _reseed(self):
        """@brief New random board, then a gc pass while nothing is animating.
        @details Bounded: ~1 ms of viper work, one 5-byte urandom call and one
                 gc.collect() (garbage is only a few hundred bytes per board)."""
        self.engine.seed()
        if self.pcd is not None:
            self._pick_palette()
        gc.collect()

    def _note_slow(self, ms, phase):
        """@brief Remember the slowest frame (> SLOW_MS) for the status line."""
        if ms > self.slow_ms:
            self.slow_ms = ms
            self.slow_phase = phase
            self.status = ""            # force a status rebuild next frame

    def run(self):
        """@brief Main loop.  Every pause is wall-clock bounded:
        @details - a stalled board stays up for LINGER_MS of real time (not a
                   frame count, so slow frames cannot stretch it);
                 - each frame sleeps at most FRAME_MS;
                 - reseed and gc happen once per board, not mid-animation.
                 The status line shows F<frames per second>, and a frame
                 slower than SLOW_MS is shown as "!<ms><phase>" in the
                 status line (k=key read, s=step, d=draw, r=reseed, w=sleep)
                 so an outside stall (I2C keyboard, USB, flash) can be traced."""
        import utime
        e = self.engine
        self.slow_ms = SLOW_MS
        self.slow_phase = ""
        self.fps = 0
        fps_t0 = utime.ticks_ms()
        fps_n = 0
        self._reseed()
        linger_t0 = 0
        linger_ms = 0
        note = ""
        frame = 0
        self._park_vt()
        try:
            while True:
                t0 = utime.ticks_ms()
                if self._key_hit():
                    break
                t1 = utime.ticks_ms()
                phase = "s"
                if linger_ms:
                    if utime.ticks_diff(t1, linger_t0) >= linger_ms:
                        linger_ms = 0
                        note = ""
                        phase = "r"
                        self._reseed()
                else:
                    r = e.step()
                    if r == ST_MAXGEN:
                        phase = "r"
                        self._reseed()
                    elif r != ST_OK:
                        note = REASON_TEXT[r]
                        linger_ms = LINGER_EMPTY_MS if r == ST_EMPTY else LINGER_MS
                        linger_t0 = t1
                t2 = utime.ticks_ms()
                self._draw(note)
                t3 = utime.ticks_ms()
                frame += 1
                if (frame % GC_EVERY) == 0:
                    gc.collect()
                d = FRAME_MS - utime.ticks_diff(utime.ticks_ms(), t0)
                utime.sleep_ms(d if d > 1 else 1)
                # Slow-frame bookkeeping (cheap: four ticks_ms per frame).
                t4 = utime.ticks_ms()
                fps_n += 1
                if utime.ticks_diff(t4, fps_t0) >= 1000:
                    self.fps = (fps_n * 1000) // utime.ticks_diff(t4, fps_t0)
                    fps_n = 0
                    fps_t0 = t4
                total = utime.ticks_diff(t4, t0)
                if total > self.slow_ms:
                    k = utime.ticks_diff(t1, t0)
                    st = utime.ticks_diff(t2, t1)
                    dr = utime.ticks_diff(t3, t2)
                    w = utime.ticks_diff(t4, t3)
                    m = k
                    ph = "k"
                    if st > m:
                        m = st
                        ph = phase
                    if dr > m:
                        m = dr
                        ph = "d"
                    if w > m:
                        ph = "w"
                    self._note_slow(total, ph)
        except KeyboardInterrupt:
            pass
        finally:
            if _lut_dirty:
                # Default colours back before the VT/menu draw again; done
                # under beginDraw on a cleared screen so nothing flashes.
                try:
                    d = self.display
                    d.beginDraw()
                    utime.sleep_ms(LUT_SETTLE_MS)
                    d.fill(0)
                except Exception:
                    pass
                restore_lut()
                try:
                    self.display.show()
                except Exception:
                    pass
            self.lut_pending = False
            self._restore_vt()
            if self.kb:
                _drain(self.kb, self.key_buf)
            d = self.display
            d.beginDraw()
            utime.sleep_ms(8)
            d.fill(0)
            d.show()


def main():
    """@brief Menu entry point (py_run exec()s us with __name__ == '__main__')."""
    _collect()
    saver = None
    try:
        saver = LifeSaver()
    except MemoryError:
        saver = None
        _collect()
        try:
            free = gc.mem_free()
        except Exception:
            free = -1
        _show_message(["Life: not enough memory.",
                       "Needs two 6,400 B blocks.",
                       "Free %d B, largest %d B." % (free, largest_block()),
                       "Press any key."])
        return
    try:
        saver.run()
    finally:
        restore_lut()               # no-op unless run() could not
        saver = None
        _collect()


if __name__ == "__main__":
    main()
