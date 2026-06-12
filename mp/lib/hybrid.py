"""
Thin hybrid math interface for SuperCalc.OG.
Tries the fast C extension first, falls back to pure Python.
"""
try:
    import picocalc_math as _c
    HAS_C_MATH = True
except ImportError:
    HAS_C_MATH = False

def version():
    if HAS_C_MATH:
        return _c.version()
    return "pure-python-fallback-0.1"

def add(a, b):
    if HAS_C_MATH:
        return _c.add(a, b)
    return a + b

# Future: sin, complex, rpn_eval, etc. will be added here