"""
SuperCalc.OG mp.apps (Phase 5 foundations)

Built-in apps surface begins here (text/REPL driven for inc1; richer UI + menu integration later).

This package provides higher-level "apps" built on the core (expr, prog, solver, stats, plot).
Apps are first-class importable modules/objects, usable from CalcREPL, user programs, or scripts.
REPL remains the primary interactive surface; apps are callable helpers or light interactive facades.

Inc1 (phase5 next slice): solver_app (thin SolverApp + solve_text) demonstrating reuse of find_root
with optional REPL stack integration and env side-effect visibility (RPL spirit).

See solver_app.py for the example. Future: stats_app, constants browser, program library, etc.

Offline, thin, no new C, no framebuffer.
"""
# Package marker. Import submodules explicitly: from mp.apps.solver_app import SolverApp
__all__ = []  # populated by submodules when imported
