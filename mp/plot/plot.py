"""
SuperCalc.OG Phase 3 inc1 — Cartesian (and expr) sampling engine.

cartesian_sample: evaluate f(x) over [xmin, xmax] producing list of (x, y) points.
  expr: infix string (e.g. "sin(x)+x/2"), or RPN token list, or Program (uses .body)
  n: number of samples (default 320 to match PicoCalc 320x320 column density)
  env: optional dict for extra vars + side effects (sto inside sampled exprs visible to caller)

linspace(xmin, xmax, n=320): helper returning the x-grid (320x320-aware default).
Exposed so host scripts and future render layers can share the exact sampling grid.

Implementation re-uses mp.lang.expr (to_rpn + eval_rpn) + mp.lib.hybrid (C math when present).
This gives correct precedence, all Phase1/2 functions, first-class program support, and
sto/rcl side effects for RPL-style "graph a program that mutates state".

For pure math graphs, exprs should avoid side effects; sampling is sequential left-to-right.

320x320: default n=320 yields one sample per column in a full-width plot (no x-resample needed
for simple line renders later). ymin/ymax auto or supplied in future viewport wrapper.

Error handling: individual sample errors -> y=nan (keeps plot continuous for later render).
"""
from __future__ import annotations
from typing import Any, List, Tuple, Optional, Dict, Union
import math as _py_m

from mp.lang.expr import to_rpn, eval_rpn
from mp.lang.prog import is_program

Point = Tuple[float, float]

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
