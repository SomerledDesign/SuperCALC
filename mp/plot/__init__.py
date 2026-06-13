"""
SuperCalc.OG — Phase 3 graphing (inc1: data sampling engine).

Public API:
  from mp.plot import cartesian_sample, linspace, ascii_plot
  pts = cartesian_sample("sin(x)", -3.14, 3.14, n=320)
  xs = linspace(-10, 10, 320)
  print(ascii_plot(pts, width=40, height=10, title="sin demo"))
  # -> multi-line ascii frame with * marks; usable on host REPL or device terminal.
  # 320 samples downsample to width for quick shape verification.

Re-uses Phase 1/2 expr + hybrid for evaluation (infix or RPN/Program bodies).
C (picocalc_plot) will accelerate later; this layer stays the contract.

Offline-first. 320x320 aware (default n matches screen width for direct mapping).
ascii_plot is a host-printable data renderer (no framebuffer, no pixels) — pure verification aid.
Real device graphing UI/raster in inc2+.
"""
from .plot import cartesian_sample, sample_expr, linspace, ascii_plot

__all__ = ["cartesian_sample", "sample_expr", "linspace", "ascii_plot"]
