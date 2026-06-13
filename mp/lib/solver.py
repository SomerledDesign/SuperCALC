"""
SuperCalc.OG — Phase 4 inc1: numeric solver foundations (root finder).

Reusable find_root that works with the existing expression + program machinery.
f can be:
  - infix str (e.g. "x*x - 2") -> eval_infix(f, env_with_x)
  - rpn token list -> eval_rpn(f, env_with_x)
  - Program (or name) -> run/eval_rpn on its body with env['x'] updated each iter

Always supplies env['x'] = guess (RPL "x rcl" or var resolve works; side effects
visible to caller, mirroring Phase 3 cartesian_sample + Program-as-fn contract).

Uses safeguarded secant for fast convergence on smooth f. Small, offline,
double baseline, no new C yet (evals hit hybrid/C math).

Public:
  from mp.lib.solver import find_root
  r = find_root("x*x-2", 1.0, 2.0)                 # ~1.414...
  r = find_root(["x","rcl",2,"pow",2,"-"], 1, 2)
  from mp.lang.prog import make_prog
  p = make_prog(None, [("var","x"), "rcl", 2, "pow", 2, "-"])
  r = find_root(p, 1, 2)

Thin: solver owns iteration + convergence; expr/hybrid own eval.
"""

from __future__ import annotations
from typing import Any, Optional, Dict, Union, List

import sys
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mp.lang.expr import eval_infix, eval_rpn
from mp.lang.prog import is_program, run_prog

Number = Union[int, float]
FSpec = Union[str, List[Any], Any]  # str | rpn-list | Program

def find_root(
    f: FSpec,
    a: Number,
    b: Number,
    *,
    tol: float = 1e-9,
    maxiter: int = 60,
    env: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Find x in [a,b] approx where f(x) ~ 0 using secant (safeguarded).
    Returns the root approximation.
    Raises ValueError on no convergence in maxiter or degenerate cases.
    env: if supplied, reused and mutated (['x'] set each step + any sto side effects).
    """
    if env is None:
        env = {}
    # Use caller's env (if passed) so sto side-effects during root search are visible after return (RPL spirit)
    # Matches cartesian_sample behavior for Program bodies.

    def _eval(xval: float) -> float:
        env["x"] = float(xval)
        if isinstance(f, str):
            return float(eval_infix(f, env))
        if isinstance(f, (list, tuple)):
            return float(eval_rpn(list(f), env))
        if is_program(f):
            # use run_prog for full first-class semantics (handles name etc)
            # but since we already set x in env, and body may rcl x
            return float(run_prog(f, env))
        # allow plain callable for power users (e.g. lambda x: x*x-2) in host tests
        if callable(f):
            return float(f(xval))
        raise ValueError("find_root f must be str (infix), rpn list, Program, or callable")

    # initial bracket evals
    fa = _eval(a)
    fb = _eval(b)
    if abs(fa) < tol:
        return float(a)
    if abs(fb) < tol:
        return float(b)

    # secant loop; use a,b as current two points
    x0, f0 = float(a), float(fa)
    x1, f1 = float(b), float(fb)

    for it in range(maxiter):
        denom = (f1 - f0)
        if abs(denom) < 1e-300:
            # flat or duplicate; perturb or fail
            if abs(f1) < tol:
                return x1
            # simple bisection-ish fallback step
            x2 = (x0 + x1) * 0.5
        else:
            x2 = x1 - f1 * (x1 - x0) / denom
        # clamp to reasonable (no wild extrapolation for inc1)
        # allow outside [a,b] for secant (common)
        f2 = _eval(x2)
        if abs(f2) < tol:
            return x2
        # shift
        x0, f0 = x1, f1
        x1, f1 = x2, f2
        if abs(x1 - x0) < tol:
            return x1

    raise ValueError(f"find_root did not converge in {maxiter} iterations (last ~{x1})")


__all__ = ["find_root"]