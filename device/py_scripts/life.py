# picocalc-app: Life | Graphics | Conway's Game of Life screensaver
"""
@file    life.py
@brief   Menu launcher for the Life screensaver (code is in life_core.mpy,
         precompiled; life_core.py is the source).
@details py_run reads a menu script into one string and keeps it alive
         while it runs, so this file is kept tiny; life_core is imported
         (streamed from flash) and dropped from sys.modules on exit so its
         bytecode is freed too.
"""
import gc
import sys


def _oom(why="not enough memory to load."):
    """@brief Say why we are going straight back to the menu."""
    try:
        import picocalc
        import utime
        d = picocalc.display
        d.beginDraw()
        utime.sleep_ms(8)
        d.fill(0)
        d.text("Life: " + why, 8, 140, 15)
        d.text("Free %d B. Returning to menu." % gc.mem_free(), 8, 152, 15)
        d.show()
        utime.sleep(3)
    except Exception:
        pass


def main():
    """@brief Import life_core, run it, then unload it."""
    gc.collect()
    gc.collect()
    try:
        try:
            import life_core
        except MemoryError:
            gc.collect()
            _oom()
            return
        except (ValueError, ImportError) as exc:   # missing or wrong-arch .mpy
            _oom("cannot load life_core: %s" % exc)
            return
        life_core.main()
    finally:
        try:
            sys.modules.pop("life_core", None)
        except Exception:
            pass
        gc.collect()


if __name__ == "__main__":
    main()
