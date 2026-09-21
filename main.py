# SuperCalc.OG — light the IPS on boot (USB REPL remains available).
try:
    from examples.boot_banner import *  # paints on import
except Exception:
    try:
        import boot_banner  # if copied to root
    except Exception as e:
        print("boot banner skip:", e)
