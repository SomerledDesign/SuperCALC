"""
SuperCalc.OG Phase 5 inc1 — solver_app (mp.apps surface start)

Thin, reusable solver "app" demonstrating packaging of prior foundations (solver + expr/prog)
into a higher-level surface while keeping REPL primary.

- solve_text(fspec, a, b, repl=None, env=None): convenience that accepts infix str / Program / rpn list,
  delegates to find_root (which handles env['x'] side effects exactly as plot/solver did), optionally
  pushes result to a supplied CalcREPL's stack (for .solve cmd parity or app-in-repl use).
- SolverApp(repl=None): small stateful app object. .solve(...) sugar; can be sto'd/recalled like a
  first-class tool from RPL programs in future. 

RPL spirit: side effects (x updated during search) visible in env/repl; result usable immediately.
No new math, no UI pixels, offline, reuses public APIs only (thin).

Host demo:
  from mp.apps.solver_app import solve_text, SolverApp
  from mp.ui.calc_repl import CalcREPL
  r = CalcREPL()
  print(solve_text("x*x-2", 1, 2, repl=r))
  app = SolverApp(r)
  app.solve("sin(x)", 3, 4)

On device: same imports after UF2; callable from base REPL or CalcREPL lines via import.
"""
import sys
import os

# Host CPython has os.path; MicroPython does not — skip path bootstrap on device
# (package already lives under /mp on the PicoCalc filesystem).
if hasattr(os, "path"):
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)

from mp.lib.solver import find_root
from mp.lang.prog import is_program


def solve_text(fspec, a, b, repl=None, env=None, tol=1e-9, maxiter=60):
    """
    Text-friendly solve wrapper (Phase 5 apps example).

    fspec: infix str, pre-parsed rpn list, or Program (first-class).
    a, b: bracket (float).
    repl: optional CalcREPL; if given, result is appended to its stack (like .solve dot-cmd).
    env: optional env dict (for 'x' side effects and var refs in fspec); if repl given, uses repl.env.
    Returns the root approx (float) or raises on failure (passthrough from find_root).

    Mirrors the contract and side-effect visibility of mp.lib.solver + Phase3/4 sampling.
    """
    if env is None and repl is not None:
        env = repl.env
    root = find_root(fspec, float(a), float(b), tol=tol, maxiter=maxiter, env=env)
    if repl is not None:
        repl.stack.append(root)
        repl.last_result = root
        # also keep lastx in sync for the app-driven result
        if isinstance(root, (int, float)):
            repl.lastx = float(root)
            repl.env["lastx"] = repl.lastx
    return root


class SolverApp:
    """
    Minimal app object (example of mp.apps packaging).

    Can be instantiated with or without a bound CalcREPL.
    Stored in env / sto'd like any first-class value (RPL programs can hold tools).
    """

    def __init__(self, repl=None):
        self.repl = repl
        self.last_root = None

    def solve(self, fspec, lo, hi, **kw):
        """Bound solve that optionally mutates bound repl stack + lastx."""
        root = solve_text(fspec, lo, hi, repl=self.repl, **kw)
        self.last_root = root
        return root

    def __repr__(self):
        return f"<SolverApp repl={'yes' if self.repl else 'no'} last={self.last_root}>"
