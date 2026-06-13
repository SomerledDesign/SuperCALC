"""
SuperCalc.OG mp.lib (Phase 4+ reusable foundations)

This package provides hybrid (C-accelerated math + stats), solver, etc.

Prior code imports directly:
  from mp.lib.hybrid import ...
  from mp.lib.solver import find_root

Phase 5 packaging note: a future increment can add convenient re-exports here once circular-import hygiene (expr <-> lib) is resolved. For now the dir exists and direct imports remain the contract.
"""
# Intentionally minimal to avoid import cycles with mp.lang.expr (which imports hybrid).
# Do not "from . import solver" or "from . import hybrid" at top level here.
__all__ = []
