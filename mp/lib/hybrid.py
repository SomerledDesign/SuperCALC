"""
Thin hybrid math interface for SuperCalc.OG (Phase 0 proof).
Tries the fast C extension (picocalc_math) first, falls back to Python math.
This is the canonical thin boundary: UI/lang in MPy, hot numeric in C when available.

On real hardware after custom UF2 build: HAS_C_MATH=True and calls are native.
On host/dev machine: always falls back (C module not importable outside MP build).
"""

import math as _py_math

try:
    import picocalc_math as _c
    HAS_C_MATH = True
except ImportError:
    HAS_C_MATH = False

def version():
    if HAS_C_MATH:
        return _c.version()
    return "pure-python-fallback-0.2"

def add(a, b):
    if HAS_C_MATH:
        return _c.add(a, b)
    return a + b

def sin(x):
    if HAS_C_MATH:
        return _c.sin(x)
    return _py_math.sin(x)

def sqrt(x):
    if HAS_C_MATH:
        return _c.sqrt(x)
    if x < 0:
        raise ValueError("sqrt of negative")
    return _py_math.sqrt(x)

# Phase 1 will add: rpn_eval / infix_eval, complex support, matrices via ulab hooks,
# more kernels (log, exp, pow, hypot, stats primitives, etc). Keep boundary minimal.