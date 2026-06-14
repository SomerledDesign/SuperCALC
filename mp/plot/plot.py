"""
SuperCalc.OG Phase 3 inc1 — Cartesian (and expr) sampling engine.

cartesian_sample: evaluate f(x) over [xmin, xmax] producing list of (x, y) points.
  expr: infix string (e.g. "sin(x)+x/2"), or RPN token list, or Program (uses .body)
  n: number of samples (default 320 to match PicoCalc 320x320 column density)
  env: optional dict for extra vars + side effects (sto inside sampled exprs visible to caller)

linspace(xmin, xmax, n=320): helper returning the x-grid (320x320-aware default).
Exposed so host scripts and future render layers can share the exact sampling grid.

ascii_plot(points, width=64, height=16, title=""): host/device friendly text renderer for
sampled point data. Produces a multi-line ascii frame with '*' marks. Ignores NaNs, auto-scales
to data range (or flat-line sentinel). Small, zero-dep, useful for immediate host verification
of sampling correctness and curve shape before real pixels (inc2). 320 samples downsample cleanly
to terminal width.

Implementation re-uses mp.lang.expr (to_rpn + eval_rpn) + mp.lib.hybrid (C math when present).
This gives correct precedence, all Phase1/2 functions, first-class program support, and
sto/rcl side effects for RPL-style "graph a program that mutates state".

For pure math graphs, exprs should avoid side effects; sampling is sequential left-to-right.

320x320: default n=320 yields one sample per column in a full-width plot (no x-resample needed
for simple line renders later). ymin/ymax auto or supplied in future viewport wrapper.

Error handling: individual sample errors -> y=nan (keeps plot continuous for later render).
"""
from __future__ import annotations
try:
    from typing import Any, List, Tuple, Optional, Dict, Union
    Point = Tuple[float, float]
except ImportError:
    # MicroPython compatibility (no typing module). from __future__ annotations
    # (above) makes all : annotations and -> returns unevaluated (string form),
    # so runtime names for types are not required except for this top-level alias.
    # Dummies allow the alias line and any annotation strings that reference them.
    # Fixes transitive import of calc_repl (which does "from mp.plot import ...")
    # and solver (pulls prog) on device. Addresses Phase 5 QA blocker.
    Any = List = Tuple = Optional = Dict = Union = object
    Point = tuple

import math as _py_m

from mp.lang.expr import to_rpn, eval_rpn
from mp.lang.prog import is_program

def linspace(xmin: float, xmax: float, n: int = 320) -> List[float]:
    """Return n evenly spaced floats from xmin to xmax (inclusive).
    Default n=320 matches PicoCalc 320x320 screen columns for direct 1:1 sampling.
    Used internally by cartesian_sample; exposed for host tooling / custom x-grids.
    """
    if n < 2:
        n = 2
    if xmax < xmin:
        xmin, xmax = xmax, xmin
    dx = (xmax - xmin) / (n - 1) if n > 1 else 0.0
    return [xmin + i * dx for i in range(n)]


def sample_expr(
    expr: Union[str, List[Any], Any],
    x: float,
    env: Optional[Dict[str, Any]] = None
) -> float:
    """Evaluate expr at a single x (helper; sets 'x' in env for this call)."""
    if env is None:
        env = {}
    env["x"] = float(x)
    if isinstance(expr, str):
        tokens = to_rpn(expr)
    elif isinstance(expr, (list, tuple)):
        tokens = list(expr)
    elif is_program(expr):
        tokens = list(getattr(expr, "body", []))
    else:
        tokens = list(expr) if hasattr(expr, "__iter__") else []
    val = eval_rpn(tokens, env)
    if isinstance(val, (int, float)):
        return float(val)
    return float("nan")

def cartesian_sample(
    expr: Union[str, List[Any], Any],
    xmin: float = -10.0,
    xmax: float = 10.0,
    n: int = 320,
    env: Optional[Dict[str, Any]] = None
) -> List[Point]:
    """
    Sample expr over [xmin, xmax] with n points. Returns list of (x, y) in order.

    n=320 is deliberate for 320x320 square screen (future 1:1 column mapping).
    Supports the same expr forms as the rest of the language (infix, rpn, stored programs).

    The supplied env (if any) is mutated in place for 'x' on each sample and for any
    sto side-effects the expression body performs (authentic RPL behavior for
    programs used as functions).

    On host: always Python path (hybrid C math for the leaf ops inside eval).
    On device with picocalc_plot: future versions may delegate inner loop to C.
    """
    if env is None:
        env = {}
    if n < 2:
        n = 2
    if xmax < xmin:
        xmin, xmax = xmax, xmin

    xs = linspace(xmin, xmax, n)

    # Prepare tokens / body once (RPN form is efficient for repeated eval)
    if isinstance(expr, str):
        tokens = to_rpn(expr)
    elif isinstance(expr, (list, tuple)):
        tokens = list(expr)
    elif is_program(expr):
        tokens = list(getattr(expr, "body", []))
    else:
        # last resort: assume iterable of tokens
        tokens = list(expr) if hasattr(expr, "__iter__") else []

    points: List[Point] = []
    for x in xs:
        env["x"] = float(x)
        try:
            y = eval_rpn(tokens, env)
            if not isinstance(y, (int, float)):
                y = float("nan")
            points.append((float(x), float(y)))
        except Exception:
            # keep plot "runnable" even if some points domain-error (e.g. log(x) for x<=0)
            points.append((float(x), float("nan")))
    return points


def ascii_plot(points: List[Point], width: int = 64, height: int = 16, title: str = "") -> str:
    """
    Render sampled (x,y) points as a compact ascii plot (multi-line string).
    Pure Python, zero deps, works on host REPL and on-device terminal.
    Intended for Phase 3 inc1 data verification and quick visual checks.
    Downsamples naturally when width < len(points) (e.g. 320 samples -> 64 cols).

    - Skips NaN/Inf y values (domain errors during sample stay non-fatal).
    - Auto y-range from data; if flat or no points, emits a clear placeholder.
    - Frame uses + - | with * for data marks.
    - Title (if given) appears above the plot frame.
    - Returns the text; caller does print(...) for display.
    """
    if width < 4:
        width = 4
    if height < 3:
        height = 3

    # Filter valid finite points only (preserve order for x, but we bucket by col)
    valid = [(float(px), float(py)) for (px, py) in points
             if isinstance(py, (int, float)) and _py_m.isfinite(py) and isinstance(px, (int, float)) and _py_m.isfinite(px)]

    if not valid:
        lines = []
        if title:
            lines.append(title)
        lines.append("+" + "-" * (width - 2) + "+")
        msg = "(no valid data)"
        pad = (width - 2 - len(msg)) // 2
        mid = "|" + " " * pad + msg + " " * (width - 2 - pad - len(msg)) + "|"
        for _ in range(height - 2):
            lines.append(mid)
        lines.append("+" + "-" * (width - 2) + "+")
        return "\n".join(lines)

    xs = [p[0] for p in valid]
    ys = [p[1] for p in valid]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    # Handle flat y (or single point)
    if ymax == ymin:
        # make a visible band so flat lines still render as horizontal
        delta = abs(xmax - xmin) * 0.01 if xmax != xmin else 1.0
        ymin -= delta
        ymax += delta

    def to_col(x: float) -> int:
        if xmax == xmin:
            return width // 2
        t = (x - xmin) / (xmax - xmin)
        return max(0, min(width - 1, int(round(t * (width - 1)))))

    def to_row(y: float) -> int:
        # screen row 0 = top = high y
        if ymax == ymin:
            return height // 2
        t = (y - ymin) / (ymax - ymin)
        row = int(round((1.0 - t) * (height - 1)))
        return max(0, min(height - 1, row))

    # Build empty grid (list of lists for mutability)
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    # Plot marks (last-wins on column collision is acceptable for ascii verify)
    for px, py in valid:
        c = to_col(px)
        r = to_row(py)
        grid[r][c] = '*'

    # Assemble frame
    lines: List[str] = []
    if title:
        lines.append(title[:width])

    top = "+" + "-" * (width - 2) + "+"
    bot = top
    lines.append(top)

    for r in range(height):
        row_chars = ''.join(grid[r])
        lines.append("|" + row_chars + "|")

    lines.append(bot)

    # Tiny range footer (keeps it tiny and verifiable)
    footer = f"[{xmin:.3g},{xmax:.3g}] x [{ymin:.3g},{ymax:.3g}] n={len(points)}"
    if len(footer) > width:
        footer = footer[:width]
    lines.append(footer)

    return "\n".join(lines)
