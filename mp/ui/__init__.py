"""
SuperCalc.OG — mp.ui package (Phase 5+)

UI layer: interactive REPL driver, future menus, graph view, program editor.

Inc1: CalcREPL (text, unified algebraic + RPN entry, dot-commands for solver/plot/demo)
      that ties together all prior foundations (expr, prog, solver, stats via hybrid, plot ascii).

Usage (host or on-device after UF2):
    from mp.ui import CalcREPL, run_demo
    r = CalcREPL()
    r.enter("2 + 3 * sin(pi/2)")   # infix path (C accelerated when present)
    r.enter("dup")                 # rpn stack word (fallback path)
    print(r.stack)
    r.enter(".s")                  # show stack
    r.enter(".plot sin(x)")
    run_demo()                     # scripted tour of progs + solver + stats + plot

See calc_repl.py for the driver and batch_run (for tests).
Thin: pure consumer of mp.lang.* and mp.lib.* public APIs.
Offline-first. RPL spirit preserved (visible stack, first-class progs, side effects).

Future incs: richer ui/ (graph viewport using base picocalcdisplay), mp/apps/ implementations,
SD persistence for progs/vars, keyboard macros, etc.
"""
from .calc_repl import CalcREPL, run_demo, batch_run_demo_lines

__all__ = ["CalcREPL", "run_demo", "batch_run_demo_lines"]
