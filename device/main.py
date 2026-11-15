# main.py — PicoCalc program menu (SuperCalc + flash/SD apps; SD optional)
import sys
import gc

for _p in ("/modules", "/py_scripts", "/sd/py_scripts", "/sd"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# PicoCalc boot splash (frozen in firmware 20261115h+): one of four amber images at
# random, ~6.4 s, any key dismisses (the key is swallowed). Any failure just skips it.
try:
    import pc_splash
    pc_splash.show()
except:
    pass
gc.collect()

try:
    from py_run import main_menu
    main_menu()
except Exception as e:
    sys.print_exception(e)
    print("Menu failed — USB REPL still up.")
    gc.collect()
