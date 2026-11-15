# picocalc-app: SuperCalc 12C | Apps | HP12C-style financial worksheets
"""Tiny launcher: the menu exec()s this file, so keep it small and import the big library."""
import sys
import gc
if "/py_scripts" not in sys.path:
    sys.path.insert(0, "/py_scripts")
try:   # SuperCALC splash (firmware 20261115g+): 6.4 s, any key dismisses, key swallowed
    import sc_splash
    sc_splash.show()
except Exception:
    pass
gc.collect()
try:
    import sheets
    sheets.main()
except Exception as e:
    try:
        with open("/sheets_log.txt", "a") as f:
            f.write("launcher error: " + repr(e) + "\n")
    except Exception:
        pass
    raise
