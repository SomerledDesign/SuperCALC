"""
SuperCalc.OG — Phase 3 graphing (inc1: data sampling engine).

Public API:
  from mp.plot import cartesian_sample, linspace
  pts = cartesian_sample("sin(x)", -3.14, 3.14, n=320)
  xs = linspace(-10, 10, 320)
  # -> [(x0, y0), ...] ; xs is the matching grid

Re-uses Phase 1/2 expr + hybrid for evaluation (infix or RPN/Program bodies).
C (picocalc_plot) will accelerate later; this layer stays the contract.

Offline-first. 320x320 aware (default n matches screen width for direct mapping).
No pixels or UI here — pure data for inc1 (render + interaction = inc2+).
"""
from .plot import cartesian_sample, sample_expr, linspace

__all__ = ["cartesian_sample", "sample_expr", "linspace"]
