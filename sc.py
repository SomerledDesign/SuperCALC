import sys

if '/' not in sys.path:
    sys.path.insert(0, '/')

def reload_sc():
    """Force reimport after pushing changes with mpremote or dashboard."""
    for name in list(sys.modules):
        if name.startswith('mp'):
            del sys.modules[name]
    from mp.ui.calc_repl import CalcREPL, run_demo
    return CalcREPL, run_demo

CalcREPL, run_demo = reload_sc()
print("SuperCalc.OG ready. Call run_demo() or r = CalcREPL()")
